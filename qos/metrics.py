"""
Station TV - Metrics Calculator
Calcul des métriques QoS (throughput, WER, temps de traitement, etc.)
"""

import time
from pathlib import Path
from typing import Dict, List, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class MetricsCalculator:
    """
    Calculateur de métriques de qualité de service.
    """
    
    def __init__(self):
        """Initialise le calculateur de métriques."""
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.transcriptions: List[Dict] = []
        
        logger.info("MetricsCalculator initialisé")
    
    def start_session(self):
        """Démarre une session de mesure."""
        self.start_time = time.time()
        self.transcriptions = []
        logger.info("Session de mesure démarrée")
    
    def end_session(self):
        """Termine une session de mesure."""
        self.end_time = time.time()
        logger.info("Session de mesure terminée")
    
    def add_transcription(
        self, 
        audio_duration: float, 
        processing_time: float,
        file_path: str,
        model: str,
        success: bool = True
    ):
        """
        Ajoute une transcription aux métriques.
        
        Args:
            audio_duration: Durée du fichier audio (secondes)
            processing_time: Temps de traitement (secondes)
            file_path: Chemin du fichier audio
            model: Nom du modèle utilisé
            success: Succès de la transcription
        """
        self.transcriptions.append({
            "file_path": file_path,
            "audio_duration": audio_duration,
            "processing_time": processing_time,
            "model": model,
            "success": success,
            "timestamp": time.time()
        })
        
        logger.debug(f"Transcription ajoutée: {file_path} ({audio_duration:.2f}s → {processing_time:.2f}s)")
    
    def calculate_throughput(self) -> float:
        """
        Calcule le débit (throughput) global.
        Throughput = durée audio totale / durée réelle totale
        
        Un throughput de 5× signifie qu'on peut traiter 5 heures d'audio en 1 heure.
        
        Returns:
            Throughput (ratio)
        """
        if not self.transcriptions:
            logger.warning("Aucune transcription pour calculer le throughput")
            return 0.0
        
        total_audio_duration = sum(t["audio_duration"] for t in self.transcriptions if t["success"])
        total_processing_time = sum(t["processing_time"] for t in self.transcriptions if t["success"])
        
        if total_processing_time == 0:
            return 0.0
        
        throughput = total_audio_duration / total_processing_time
        
        logger.info(
            f"Throughput calculé: {throughput:.2f}× "
            f"({total_audio_duration/3600:.2f}h audio / {total_processing_time/3600:.2f}h traitement)"
        )
        
        return throughput
    
    def calculate_average_processing_time(self) -> float:
        """
        Calcule le temps de traitement moyen par fichier.
        
        Returns:
            Temps moyen en secondes
        """
        successful = [t for t in self.transcriptions if t["success"]]
        
        if not successful:
            return 0.0
        
        avg_time = sum(t["processing_time"] for t in successful) / len(successful)
        
        logger.info(f"Temps de traitement moyen: {avg_time:.2f}s par fichier")
        
        return avg_time
    
    def calculate_success_rate(self) -> float:
        """
        Calcule le taux de réussite des transcriptions.
        
        Returns:
            Taux de réussite (0.0 - 1.0)
        """
        if not self.transcriptions:
            return 0.0
        
        success_count = sum(1 for t in self.transcriptions if t["success"])
        success_rate = success_count / len(self.transcriptions)
        
        logger.info(
            f"Taux de réussite: {success_rate*100:.1f}% "
            f"({success_count}/{len(self.transcriptions)})"
        )
        
        return success_rate
    
    def get_session_duration(self) -> float:
        """
        Retourne la durée totale de la session.
        
        Returns:
            Durée en secondes
        """
        if self.start_time is None:
            return 0.0
        
        end = self.end_time if self.end_time is not None else time.time()
        duration = end - self.start_time
        
        return duration
    
    def get_summary(self) -> Dict:
        """
        Génère un résumé complet des métriques.
        
        Returns:
            Dictionnaire avec toutes les métriques
        """
        summary = {
            "session_duration_seconds": self.get_session_duration(),
            "total_files": len(self.transcriptions),
            "successful_files": sum(1 for t in self.transcriptions if t["success"]),
            "failed_files": sum(1 for t in self.transcriptions if not t["success"]),
            "success_rate": self.calculate_success_rate(),
            "total_audio_duration_seconds": sum(t["audio_duration"] for t in self.transcriptions if t["success"]),
            "total_processing_time_seconds": sum(t["processing_time"] for t in self.transcriptions if t["success"]),
            "throughput": self.calculate_throughput(),
            "average_processing_time_seconds": self.calculate_average_processing_time()
        }
        
        # Conversion en heures pour lisibilité
        summary["session_duration_hours"] = summary["session_duration_seconds"] / 3600
        summary["total_audio_duration_hours"] = summary["total_audio_duration_seconds"] / 3600
        summary["total_processing_time_hours"] = summary["total_processing_time_seconds"] / 3600
        
        return summary
    
    def export_to_csv(self, output_file: str) -> bool:
        """
        Exporte les métriques détaillées vers un fichier CSV.
        
        Args:
            output_file: Chemin du fichier de sortie
        
        Returns:
            True si succès, False sinon
        """
        try:
            import pandas as pd
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            
            df = pd.DataFrame(self.transcriptions)
            df.to_csv(output_file, index=False, encoding='utf-8')
            
            logger.info(f"Métriques exportées vers {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'export CSV: {str(e)}")
            return False
    
    def calculate_wer(self, reference_text: str, hypothesis_text: str) -> float:
        """
        Calcule le Word Error Rate (WER) entre un texte de référence et une hypothèse.
        
        WER = (Substitutions + Insertions + Deletions) / Nombre total de mots
        
        Args:
            reference_text: Texte de référence (vérité terrain)
            hypothesis_text: Texte généré par la transcription
        
        Returns:
            WER (0.0 = parfait, 1.0 = complètement faux)
        """
        # Tokenisation simple (par mots)
        ref_words = reference_text.split()
        hyp_words = hypothesis_text.split()
        
        # Matrice de distance de Levenshtein (programmation dynamique)
        d = [[0] * (len(hyp_words) + 1) for _ in range(len(ref_words) + 1)]
        
        for i in range(len(ref_words) + 1):
            d[i][0] = i
        for j in range(len(hyp_words) + 1):
            d[0][j] = j
        
        for i in range(1, len(ref_words) + 1):
            for j in range(1, len(hyp_words) + 1):
                if ref_words[i-1] == hyp_words[j-1]:
                    d[i][j] = d[i-1][j-1]
                else:
                    substitution = d[i-1][j-1] + 1
                    insertion = d[i][j-1] + 1
                    deletion = d[i-1][j] + 1
                    d[i][j] = min(substitution, insertion, deletion)
        
        # WER = distance / nombre de mots de référence
        if len(ref_words) == 0:
            return 1.0 if len(hyp_words) > 0 else 0.0
        
        wer = d[len(ref_words)][len(hyp_words)] / len(ref_words)
        
        logger.info(f"WER calculé: {wer*100:.2f}%")
        
        return wer

    def import_from_trackers(self, trackers_dir: str):
        """
        Importe les métriques depuis les fichiers trackers générés par les processus.
        Utile quand les objets MetricsCalculator ne sont pas partagés entre processus (multiprocessing).
        
        Args:
            trackers_dir: Répertoire contenant les fichiers Tracker*.txt
        """
        import glob
        import os
        
        tracker_files = glob.glob(os.path.join(trackers_dir, "Tracker*.txt"))
        if not tracker_files:
            logger.warning(f"Aucun fichier tracker trouvé dans {trackers_dir}")
            return
            
        logger.info(f"Importation des métriques depuis {len(tracker_files)} fichiers trackers...")
        
        count = 0
        for t_file in tracker_files:
            try:
                with open(t_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        # Format attendu: "filename: duration secondes" OU "filename: duration secondes (audio: duration)"
                        # Exemple v1: "audio.mp3: 243.60 secondes"
                        # Exemple v2: "audio.mp3: 243.60 secondes (audio: 300.00)"
                        if "secondes" in line:
                            try:
                                # On sépare autour de "secondes" qui est notre ancre fiable
                                # part_before: "audio.mp3: 243.60 "
                                # part_after: " (audio: 300.00)" ou ""
                                part_before, _, part_after = line.partition("secondes")
                                
                                # Dans part_before, on cherche le dernier ":" pour séparer fichier et temps
                                if ":" in part_before:
                                    filename_part, _, time_part = part_before.rpartition(":")
                                    file_path = filename_part.strip()
                                    processing_time = float(time_part.strip())
                                else:
                                    # Pas de deux points found? Cas étrange, on skip
                                    continue
                                
                                # Extraction de la durée audio depuis part_after
                                audio_duration = 0.0
                                if "(audio:" in part_after:
                                    try:
                                        # " (audio: 300.00)" -> "300.00)" -> "300.00"
                                        audio_str = part_after.split("(audio:")[1].strip().rstrip(")")
                                        audio_duration = float(audio_str)
                                    except ValueError:
                                        pass
                                
                                self.add_transcription(
                                    audio_duration=audio_duration,
                                    processing_time=processing_time,
                                    file_path=file_path,
                                    model="unknown",
                                    success=True
                                )
                                count += 1
                            except ValueError:
                                continue
            except Exception as e:
                logger.error(f"Erreur lecture tracker {t_file}: {e}")
                
        logger.info(f"Importé {count} transcriptions depuis les trackers.")
