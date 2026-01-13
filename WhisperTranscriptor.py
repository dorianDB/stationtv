from multiprocessing import Process
import time
import os
import torch
import psutil
import warnings

# ========================================================================================================
# SECTION PARSE - Parse les fichiers dans un csv
# ========================================================================================================

class FichierAudio:
    def __init__(self, chemin):
        self.chemin = chemin
        self.longueur = self.extraire_duree()
    
    def extraire_duree(self):
        """Extrait la durée en secondes du fichier audio"""
        try:
            # Tenter d'ouvrir le fichier avec mutagen
            audio = mutagen.File(self.chemin)
            if audio is not None and hasattr(audio, 'info') and hasattr(audio.info, 'length'):
                return audio.info.length  # Durée en secondes
            return 0  # Valeur par défaut si la durée ne peut pas être extraite
        except Exception as e:
            print(f"Erreur lors de l'extraction de la durée pour {self.chemin}: {str(e)}")
            return 0
    
    def __str__(self):
        return f"{self.chemin} (durée: {self.longueur:.2f}s)"

def lister_fichiers(chemin, suffixes=None):
    """Crée et retourne une liste d'objets FichierAudio pour chaque fichier se terminant par les suffixes spécifiés"""
    if suffixes is None:
        suffixes = suffixe_audio
    
    objets_fichiers = []
    
    # Vérifier si le chemin existe
    if not os.path.exists(chemin):
        print(f"Le répertoire {chemin} n'existe pas.")
        return objets_fichiers
    
    # Créer une pile pour stocker les répertoires à explorer
    repertoires_a_explorer = [chemin]
    
    # Tant qu'il reste des répertoires à explorer
    while repertoires_a_explorer:
        # Prendre le prochain répertoire à explorer
        repertoire_courant = repertoires_a_explorer.pop()
        
        try:
            # Lister tout le contenu du répertoire courant
            contenu = os.listdir(repertoire_courant)
            
            for element in contenu:
                # Construire le chemin complet
                chemin_element = os.path.join(repertoire_courant, element)
                
                # Si c'est un fichier et qu'il se termine par un des suffixes, créer un objet FichierAudio
                if os.path.isfile(chemin_element) and any(chemin_element.lower().endswith(ext.lower()) for ext in suffixes):
                    # Créer un nouvel objet FichierAudio et l'ajouter à la liste
                    nouvel_objet = FichierAudio(chemin_element)
                    objets_fichiers.append(nouvel_objet)
                # Si c'est un répertoire, l'ajouter à la pile
                elif os.path.isdir(chemin_element):
                    repertoires_a_explorer.append(chemin_element)
                    
        except PermissionError:
            # Ignorer les répertoires pour lesquels on n'a pas les permissions
            print(f"Pas de permission pour accéder à {repertoire_courant}")
        except Exception as e:
            # Gérer d'autres exceptions possibles
            print(f"Erreur lors de l'accès à {repertoire_courant}: {str(e)}")
    
    return objets_fichiers

def ecrire_csv(objets, nom_fichier=pathCSV):
    """Écrit les informations des objets dans un fichier CSV"""
    try:
        with open(nom_fichier, 'w', newline='', encoding='utf-8') as fichier_csv:
            writer = csv.writer(fichier_csv)
            # Écrire l'en-tête
            writer.writerow(['Chemin', 'Duree(s)'])
            # Écrire les données de chaque objet
            for obj in objets:
                writer.writerow([obj.chemin, obj.longueur])
        print(f"Les données ont été écrites dans {nom_fichier}")
    except Exception as e:
        print(f"Erreur lors de l'écriture du fichier CSV: {str(e)}")

# ========================================================================================================
# SECTION REPARTITION - Utilise le csv pour répartir a charge égale les fichiers sur les threads
# ========================================================================================================

class Audio:
    def __init__(self, path, duree):
        self.path = path
        self.duree = duree

def glouton_n_listes(objets, n):
    """Algorithme glouton pour n listes : place chaque objet dans la liste avec la plus petite somme"""
    if not objets or n <= 0:
        return [[] for _ in range(n)]
    
    # Trier par durée décroissante
    objets_tries = sorted(objets, key=lambda x: x.duree, reverse=True)
    
    # Initialiser n listes vides avec leurs sommes
    listes = [[] for _ in range(n)]
    sommes = [0] * n
    
    # Répartir chaque objet dans la liste avec la plus petite somme
    for objet in objets_tries:
        # Trouver l'index de la liste avec la somme minimale
        index_min = sommes.index(min(sommes))
        
        # Ajouter l'objet à cette liste
        listes[index_min].append(objet)
        sommes[index_min] += objet.duree
    
    return listes

# ========================================================================================================
# SECTION WHISPER - Lance la retranscription
# ========================================================================================================

def format_timestamp_srt(seconds):
    """Convertit les secondes au format SRT (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

def create_srt_file(segments, output_file):
    """Crée un fichier SRT à partir des segments"""
    with open(output_file, "w", encoding="utf-8") as f:
        for i, segment in enumerate(segments, 1):
            start_time = format_timestamp_srt(segment["start"])
            end_time = format_timestamp_srt(segment["end"])
            text = segment["text"].strip()
            
            f.write(f"{i}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{text}\n\n")

def create_txt_file(result, output_file):
    """Crée un fichier TXT avec la transcription complète"""
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(result["text"].strip())

def charger_fichiers_audio():
    """Fonction pour charger les fichiers audio depuis le CSV"""
    listeAudiosNonTriee = []
    with open(pathCSV, 'r', encoding='utf-8') as fichier:
        lecteur = csv.reader(fichier)
        next(lecteur)  # Skip la première ligne (noms de colonnes)
        for ligne in lecteur:
            listeAudiosNonTriee.append(Audio(ligne[0], float(ligne[1])))  # ligne[0] = path, ligne[1] = durée
    listes = glouton_n_listes(listeAudiosNonTriee, nbCoeurs)  # Appliquer l'algorithme glouton pour répartir les fichiers
    return listes

def monitor_cpu_usage():
    """Enregistre l'utilisation du CPU dans un fichier CSV"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    monitoring_path = os.path.join(script_dir, "monitoring_cpu.csv")
    with open(monitoring_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Timestamp", "CPU_Usage"])
    print(f"Monitoring CPU démarré, enregistrement dans {monitoring_path}")
    while monitoring_actif:
        cpu_percent = psutil.cpu_percent(interval=1)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        with open(monitoring_path, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([timestamp, f"{cpu_percent:.2f}"])
        time.sleep(intervalleTempsMonitoring)

def monitor_memory_usage():
    """Enregistre l'utilisation de la RAM dans un fichier CSV"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    monitoring_path = os.path.join(script_dir, "monitoring_memory.csv")
    with open(monitoring_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Timestamp", "Memory_Usage"])
    print(f"Monitoring RAM démarré, enregistrement dans {monitoring_path}")
    while monitoring_actif:
        memory_percent = psutil.virtual_memory().percent
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        with open(monitoring_path, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([timestamp, f"{memory_percent:.2f}"])
        time.sleep(intervalleTempsMonitoring)

def process_audio_files_on_core(audio_list, model_name, cpu_cores, core_index):
    """Lance séquentiellement processAndWrite() sur chaque fichier Audio de la liste"""
    duree_totale = sum(audio.duree for audio in audio_list)
    print(f"Démarrage du processus sur les cœurs {cpu_cores} avec {len(audio_list)} fichiers à traiter (durée totale: {duree_totale:.2f} secondes)")
    trackers_dir = "trackers"
    os.makedirs(trackers_dir, exist_ok=True)
    tracker_path = os.path.join(trackers_dir, f"Tracker{core_index}.txt")
    
    with open(tracker_path, 'w', encoding='utf-8') as f:
        pass
    
    for audio in audio_list:
        try:
            audio_path = audio.path
            print(f"Traitement de {audio_path} sur les cœurs {cpu_cores}")
            processAndWrite(audio_path, model_name, cpu_cores, core_index)
        except Exception as e:
            print(f"Erreur lors du traitement de {audio_path}: {str(e)}")

def processAndWrite(audio_file, model_name, cpu_cores, core_index):
    """Lance la transcription et écrit les résultats dans les fichiers de sortie"""
    MODEL_SUFFIXES = {"tiny": "wt", "base": "wb", "small": "ws", "medium": "wm", "large": "wl"}
    start_time = time.time()
    result = transcribe_on_specific_cores(audio_file, model_name, cpu_cores)
    audio_dir = os.path.dirname(audio_file)
    base_name = os.path.basename(audio_file)
    file_name_without_ext, file_ext = os.path.splitext(base_name)
    if file_name_without_ext.endswith("audio"):
        cleaned_name = file_name_without_ext[:-5]  # Enlever "audio"
    else:
        cleaned_name = file_name_without_ext
    model_suffix = MODEL_SUFFIXES[modele.lower()]
    
    # Générer les fichiers de sortie selon les paramètres
    if transcriptionSRT:
        output_srt_filename = os.path.join(audio_dir, f"{cleaned_name}transcript_st_{model_suffix}.srt")
        # Créer le fichier SRT si des segments sont disponibles
        if "segments" in result and result["segments"]:
            create_srt_file(result["segments"], output_srt_filename)
            print(f"Sous-titres SRT écrits dans {output_srt_filename}")
    
    if transcriptionTxt:
        output_txt_filename = os.path.join(audio_dir, f"{cleaned_name}transcript_{model_suffix}.txt")
        # Créer le fichier TXT avec la transcription complète
        if "text" in result and result["text"].strip():
            create_txt_file(result, output_txt_filename)
            print(f"Transcription TXT écrite dans {output_txt_filename}")
    
    execution_time = time.time() - start_time
    print(f"Temps total d'exécution: {execution_time:.2f} secondes")
    trackers_dir = "trackers"
    tracker_path = os.path.join(trackers_dir, f"Tracker{core_index}.txt")
    with open(tracker_path, 'w', encoding='utf-8') as tracker:
        tracker.write(f"{base_name}: {execution_time:.2f} secondes\n\n")
    print()

def set_cpu_affinity(cpu_list):
    """Définit l'affinité CPU du processus actuel aux cœurs spécifiés"""
    p = psutil.Process(os.getpid())
    p.cpu_affinity(cpu_list)

def transcribe_on_specific_cores(audio_path, model_name=modele, cpu_cores=[0, 1]):
    """Effectue la transcription sur les coeurs spécifiés"""
    set_cpu_affinity(cpu_cores)
    p = psutil.Process(os.getpid())
    print(f"Processus restreint aux cœurs CPU: {p.cpu_affinity()}")
    device = "cpu"
    model = whisper.load_model(model_name, device=device)
    torch.set_num_threads(len(cpu_cores))
    print(f"Nombre de threads torch: {torch.get_num_threads()}")
    
    # Effectuer la transcription avec segments pour SRT si nécessaire
    if transcriptionSRT:
        result = model.transcribe(audio_path, word_timestamps=True)
    else:
        result = model.transcribe(audio_path, word_timestamps=False)
    return result

def lancer_traitement_whisper():
    """Lance les processus de traitement pour chaque liste de fichiers"""
    listes_audio = charger_fichiers_audio()
    processes = []
    for i, liste_audio in enumerate(listes_audio):
        if i >= len(repartitionCoeurs):
            print(f"Pas assez de configurations de cœurs pour traiter la liste {i}")
            continue
        if liste_audio:  # S'il y a des fichiers à traiter dans cette liste
            p = Process(target=process_audio_files_on_core, 
                       args=(liste_audio, modele, repartitionCoeurs[i], i+1))
            p.start()
            processes.append(p)
    return processes

def attendre_processus(processes):
    """Attend que tous les processus se terminent"""
    for p in processes:
        p.join()

# ========================================================================================================
# SECTION MAIN 
# ========================================================================================================

def main():
    """Fonction principale qui lance d'abord le parsing puis le traitement Whisper"""
    # Vérifier qu'au moins un type de transcription est activé
    if not transcriptionTxt and not transcriptionSRT:
        print("ERREUR: Au moins un des paramètres 'transcriptionTxt' ou 'transcriptionSRT' doit être True")
        return
    
    print("="*80)
    print("ÉTAPE 1: ANALYSE DES FICHIERS AUDIO")
    print("="*80)
    
    # Afficher les types de transcription activés
    types_actifs = []
    if transcriptionTxt:
        types_actifs.append("TXT")
    if transcriptionSRT:
        types_actifs.append("SRT")
    print(f"Types de transcription activés: {', '.join(types_actifs)}")
    
    # Étape 1: Parser les fichiers audio
    print(f"Analyse du répertoire: {repertoire_bdd}")
    print(f"Fichier avec les suffixes recherchées: {suffixe_audio}")
    
    liste_objets = lister_fichiers(repertoire_bdd, suffixe_audio)
    
    if not liste_objets:
        print("Aucun fichier audio trouvé dans le répertoire spécifié.")
        return
    
    # Afficher les objets trouvés
    print(f"\n{len(liste_objets)} fichiers audio trouvés:")
    for obj_fichier in liste_objets:
        print(f"  - {obj_fichier}")
    
    # Écrire les données dans un fichier CSV
    ecrire_csv(liste_objets, pathCSV)
    
    print("\n" + "="*80)
    print("ÉTAPE 2: TRAITEMENT AVEC WHISPER")
    print("="*80)
    
    # Démarrer le thread de monitoring CPU
    monitor_cpu_thread = threading.Thread(target=monitor_cpu_usage)
    monitor_cpu_thread.daemon = True
    monitor_cpu_thread.start()
    
    # Démarrer le thread de monitoring RAM
    monitor_memory_thread = threading.Thread(target=monitor_memory_usage)
    monitor_memory_thread.daemon = True
    monitor_memory_thread.start()
    
    try:
        # Étape 2: Lancer le traitement Whisper
        processes = lancer_traitement_whisper()
        attendre_processus(processes)
        
        print("\n" + "="*80)
        print("TRAITEMENT TERMINÉ AVEC SUCCÈS")
        print("="*80)
        
    except KeyboardInterrupt:
        print("\nInterruption par l'utilisateur. Arrêt en cours...")
    except Exception as e:
        print(f"\nErreur lors du traitement: {str(e)}")
    finally:
        # Arrêter le monitoring lorsque tous les processus sont terminés
        global monitoring_actif
        monitoring_actif = False
        monitor_cpu_thread.join(timeout=15)
        monitor_memory_thread.join(timeout=15)
        print("Monitoring CPU et RAM terminé")

if __name__ == "__main__":
    main()