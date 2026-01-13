"""
Station TV - Run Batch Whisper
Script principal de transcription batch multi-process.
Adapté depuis WhisperTranscriptor.py avec améliorations modulaires.

Usage:
    python scripts/RunBatchWhisper.py --config config/default_config.yaml
"""

import sys
import argparse
import yaml
import time
from pathlib import Path
from multiprocessing import Process
from typing import List

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.transcription import WhisperTranscriber
from core.affinity import CPUAffinityManager, Audio
from qos.monitor import SystemMonitor
from qos.metrics import MetricsCalculator
from qos.power_monitor import PowerMonitor
from utils.logger import setup_logger
from utils.file_handler import FileHandler

# Logger
logger = setup_logger("RunBatchWhisper", level="INFO")


def load_config(config_file: str) -> dict:
    """Charge la configuration depuis un fichier YAML."""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"Configuration chargée depuis {config_file}")
        return config
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la configuration: {str(e)}")
        sys.exit(1)


def process_audio_files_on_core(
    audio_list: List[Audio],
    config: dict,
    cpu_cores: List[int],
    core_index: int,
    metrics_calculator: MetricsCalculator
):
    """
    Lance séquentiellement la transcription sur chaque fichier Audio de la liste.
    Adapté depuis WhisperTranscriptor.py
    
    Args:
        audio_list: Liste d'objets Audio à traiter
        config: Configuration
        cpu_cores: Liste des cœurs CPU à utiliser
        core_index: Index du processus
        metrics_calculator: Calculateur de métriques
    """
    duree_totale = sum(audio.duree for audio in audio_list)
    logger.info(
        f"Processus {core_index}: {len(audio_list)} fichiers, "
        f"durée totale: {duree_totale:.2f}s ({duree_totale/3600:.2f}h)"
    )
    
    # Créer le répertoire trackers
    trackers_dir = Path(config.get('paths', {}).get('trackers_dir', 'trackers'))
    trackers_dir.mkdir(exist_ok=True)
    tracker_path = trackers_dir / f"Tracker{core_index}.txt"
    
    # Réinitialiser le tracker
    with open(tracker_path, 'w', encoding='utf-8') as f:
        f.write(f"=== Processus {core_index} - {len(audio_list)} fichiers ===\n\n")
    
    # Créer le transcripteur
    transcriber = WhisperTranscriber(config)
    
    # Traiter chaque fichier
    for i, audio in enumerate(audio_list, 1):
        try:
            filename = Path(audio.path).name
            
            # Log de début de traitement
            logger.info("")
            logger.info("=" * 80)
            logger.info(f"PROCESSUS {core_index} | Fichier {i}/{len(audio_list)} | Progression: {i/len(audio_list)*100:.1f}%")
            logger.info("=" * 80)
            logger.info(f"Fichier   : {filename}")
            logger.info(f"Durée     : {audio.duree / 60:.2f} min ({audio.duree:.0f}s)")
            logger.info(f"Chemin    : {audio.path}")
            logger.info("-" * 80)
            logger.info("Démarrage de la transcription...")
            
            start_time = time.time()
            
            # Transcription
            success = transcriber.process_and_write(
                audio.path,
                cpu_cores,
                core_index,
                str(tracker_path)
            )
            
            processing_time = time.time() - start_time
            throughput = audio.duree / processing_time if processing_time > 0 else 0
            
            # Ajouter aux métriques
            if metrics_calculator:
                metrics_calculator.add_transcription(
                    audio_duration=audio.duree,
                    processing_time=processing_time,
                    file_path=audio.path,
                    model=config.get('whisper', {}).get('model', 'unknown'),
                    success=success
                )
            
            # Log de fin de traitement
            if success:
                logger.info("-" * 80)
                logger.info(f"[SUCCES] Processus {core_index} | {filename}")
                logger.info(f"   Temps traitement : {processing_time:.2f}s")
                logger.info(f"   Throughput       : {throughput:.2f}x temps réel")
                logger.info(f"   Restant          : {len(audio_list) - i} fichiers")
                logger.info("=" * 80)
            else:
                logger.error("-" * 80)
                logger.error(f"[ECHEC] Processus {core_index} | {filename}")
                logger.error("=" * 80)
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement de {audio.path}: {str(e)}")


def lancer_traitement_batch(config: dict, metrics_calculator: MetricsCalculator):
    """
    Lance les processus de traitement batch.
    Adapté depuis WhisperTranscriptor.py
    
    Args:
        config: Configuration
        metrics_calculator: Calculateur de métriques
    """
    # Charger les fichiers audio depuis le CSV
    csv_path = config.get('paths', {}).get('csv_filename', 'fichiers_audio.csv')
    
    if not Path(csv_path).exists():
        logger.error(f"Fichier CSV introuvable: {csv_path}")
        return []
    
    logger.info(f"Chargement des fichiers audio depuis {csv_path}...")
    
    # Lire le CSV
    donnees = FileHandler.lire_csv(csv_path)
    
    if not donnees:
        logger.error("Aucun fichier audio trouvé dans le CSV")
        return []
    
    # Convertir en objets Audio
    liste_audios = [Audio(path, duree) for path, duree in donnees]
    logger.info(f"{len(liste_audios)} fichiers audio chargés")
    
    # Nombre de processus
    nb_processus = config.get('hardware', {}).get('max_parallel_processes', 3)
    logger.info(f"Nombre de processus parallèles: {nb_processus}")
    
    # Répartition avec algorithme glouton
    listes_audio = CPUAffinityManager.equilibrage_charge(liste_audios, nb_processus)
    
    # Configuration des cœurs CPU
    cpu_affinity = config.get('whisper', {}).get('cpu_affinity', [])
    
    if len(cpu_affinity) < nb_processus:
        logger.warning(
            f"Configuration CPU insuffisante ({len(cpu_affinity)} configs pour "
            f"{nb_processus} processus). Utilisation par défaut."
        )
        # Répartition automatique
        cores_per_process = config.get('hardware', {}).get('cpu_threads', 36) // nb_processus
        cpu_affinity = [
            list(range(i * cores_per_process, (i + 1) * cores_per_process))
            for i in range(nb_processus)
        ]
    
    # Lancer les processus
    processes = []
    for i, liste_audio in enumerate(listes_audio):
        if not liste_audio:
            logger.warning(f"Liste {i+1} vide, processus non lancé")
            continue
        
        logger.info(f"Lancement du processus {i+1} sur les cœurs {cpu_affinity[i]}")
        
        p = Process(
            target=process_audio_files_on_core,
            args=(liste_audio, config, cpu_affinity[i], i+1, metrics_calculator)
        )
        p.start()
        processes.append(p)
    
    return processes


def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(
        description="Transcription batch multi-process - Station TV"
    )
    parser.add_argument(
        '--config', '-c',
        default='config/default_config.yaml',
        help="Fichier de configuration YAML (défaut: config/default_config.yaml)"
    )
    parser.add_argument(
        '--scan-only',
        action='store_true',
        help="Scanner les fichiers audio sans lancer la transcription"
    )
    
    args = parser.parse_args()
    
    # Charger la configuration
    config = load_config(args.config)
    
    logger.info("=" * 80)
    logger.info("STATION TV - TRANSCRIPTION AUDIO HAUTE PERFORMANCE")
    logger.info("=" * 80)
    
    # Étape 1: Scanner les fichiers audio
    logger.info("\n" + "=" * 80)
    logger.info("ÉTAPE 1: ANALYSE DES FICHIERS AUDIO")
    logger.info("=" * 80)
    
    input_dir = config.get('paths', {}).get('input_audio_dir', 'bdd')
    suffixes = ['.mp3', '.wav']
    
    logger.info(f"Répertoire d'entrée: {input_dir}")
    logger.info(f"Extensions recherchées: {suffixes}")
    
    # Scanner les fichiers
    fichiers_audio = FileHandler.lister_fichiers(input_dir, suffixes)
    
    if not fichiers_audio:
        logger.error("Aucun fichier audio trouvé!")
        return
    
    logger.info(f"\n{len(fichiers_audio)} fichiers audio trouvés")
    logger.info("\nLISTE DES FICHIERS DETECTES:")
    logger.info("-" * 80)
    
    # Afficher la liste des fichiers avec leur durée
    total_duration = 0
    for i, fichier in enumerate(fichiers_audio, 1):
        filename = Path(fichier.chemin).name
        duration_min = fichier.longueur / 60
        total_duration += fichier.longueur
        logger.info(f"  {i:3d}. {filename:60s} ({duration_min:6.2f} min)")
    
    total_hours = total_duration / 3600
    logger.info("-" * 80)
    logger.info(f"Durée audio totale : {total_hours:.2f} heures ({total_duration:.0f} secondes)")
    logger.info("-" * 80)
    
    # Écrire le CSV
    csv_path = config.get('paths', {}).get('csv_filename', 'fichiers_audio.csv')
    FileHandler.ecrire_csv(fichiers_audio, csv_path)
    logger.info(f"\nFichier CSV créé: {csv_path}")
    
    if args.scan_only:
        logger.info("Mode scan-only: arrêt après le scan des fichiers")
        return
    
    # Étape 2: Transcription batch
    logger.info("\n" + "=" * 80)
    logger.info("ÉTAPE 2: TRANSCRIPTION BATCH")
    logger.info("=" * 80)
    
    # Créer le calculateur de métriques
    metrics_calculator = MetricsCalculator()
    metrics_calculator.start_session()
    
    # Démarrer le monitoring système (si activé)
    qos_enabled = config.get('qos', {}).get('enabled', True)
    monitor = None
    power_monitor = None
    
    if qos_enabled:
        logger.info("\n" + "-" * 80)
        logger.info("Démarrage du monitoring QoS...")
        logger.info("-" * 80)
        
        output_dir = config.get('paths', {}).get('reports_dir', 'output/reports')
        interval = config.get('qos', {}).get('monitoring_interval', 2)
        
        monitor = SystemMonitor(output_dir=output_dir, interval=interval)
        monitor.start()
        
        # Démarrer le monitoring énergétique
        power_config = config.get('qos', {}).get('power', {})
        if power_config.get('enabled', True):
            logger.info("Démarrage du monitoring énergétique...")
            power_monitor = PowerMonitor(
                output_dir=output_dir,
                interval=interval,
                tdp_watts=power_config.get('tdp_watts'),
                electricity_cost_per_kwh=power_config.get('cost_per_kwh', 0.18),
                carbon_intensity=power_config.get('carbon_kg_per_kwh', 0.1)
            )
            power_monitor.start()
    
    try:
        # Lancer le traitement batch
        processes = lancer_traitement_batch(config, metrics_calculator)
        
        if not processes:
            logger.error("Aucun processus lancé")
            return
        
        logger.info(f"\n{len(processes)} processus lancés, attente de la fin...")
        
        # Attendre la fin de tous les processus
        for p in processes:
            p.join()
        
        # Terminer la session de métriques
        metrics_calculator.end_session()
        
        logger.info("\n" + "=" * 80)
        logger.info("TRAITEMENT TERMINÉ AVEC SUCCÈS")
        logger.info("=" * 80)
        
        # Afficher le résumé des métriques
        summary = metrics_calculator.get_summary()
        
        logger.info("\nRÉSUMÉ DES PERFORMANCES:")
        logger.info("-" * 80)
        logger.info(f"Fichiers traités: {summary['successful_files']}/{summary['total_files']}")
        logger.info(f"Taux de réussite: {summary['success_rate']*100:.1f}%")
        logger.info(f"Durée totale: {summary['session_duration_hours']:.2f}h")
        logger.info(f"Audio traité: {summary['total_audio_duration_hours']:.2f}h")
        logger.info(f"Throughput: {summary['throughput']:.2f}× temps réel")
        logger.info("-" * 80)
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Interruption par l'utilisateur")
    except Exception as e:
        logger.error(f"\n❌ Erreur: {str(e)}")
    finally:
        # Arrêter le monitoring
        if monitor:
            logger.info("\nArrêt du monitoring QoS...")
            monitor.stop()
            logger.info("✓ Monitoring arrêté")
        
        # Arrêter le monitoring énergétique
        if power_monitor:
            logger.info("\nArrêt du monitoring énergétique...")
            power_summary = power_monitor.stop()
            logger.info("✓ Monitoring énergétique arrêté")


if __name__ == "__main__":
    main()
