"""
Station TV - Whisper Transcriber
Module principal de transcription audio basé sur Whisper.
Adapté et amélioré depuis WhisperTranscriptor.py
"""

import time
import os
import torch
import warnings
from pathlib import Path
from typing import Dict, List, Optional
from multiprocessing import Process
from datetime import datetime

from core.models import ModelManager
from core.affinity import CPUAffinityManager
from utils.logger import get_logger

logger = get_logger(__name__)

# Supprimer les avertissements FP16
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")


class WhisperTranscriber:
    """
    Classe principale de transcription audio avec Whisper.
    """
    
    def __init__(self, config: dict):
        """
        Initialise le transcripteur.
        
        Args:
            config: Dictionnaire de configuration
        """
        self.config = config
        self.model_manager = ModelManager(device=config.get('whisper', {}).get('device', 'cpu'))
        self.model_name = config.get('whisper', {}).get('model', 'small')
        self.language = config.get('whisper', {}).get('language', 'fr')
        
        # Formats de sortie
        output_formats = config.get('whisper', {}).get('output_formats', {})
        self.transcription_txt = output_formats.get('txt', True)
        self.transcription_srt = output_formats.get('srt', True)
        self.transcription_csv = output_formats.get('csv', False)
        self.transcription_json = output_formats.get('json', False)
        
        logger.info(f"WhisperTranscriber initialisé avec modèle={self.model_name}, langue={self.language}")
    
    def transcribe_on_specific_cores(
        self, 
        audio_path: str, 
        cpu_cores: List[int],
        model_name: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Effectue la transcription sur les cœurs CPU spécifiés.
        Réutilisé depuis WhisperTranscriptor.py avec améliorations.
        
        Args:
            audio_path: Chemin du fichier audio
            cpu_cores: Liste des cœurs CPU à utiliser
            model_name: Nom du modèle (optionnel, utilise config par défaut)
        
        Returns:
            Résultat de la transcription ou None en cas d'erreur
        """
        # Définir l'affinité CPU
        CPUAffinityManager.set_cpu_affinity(cpu_cores)
        
        # Utiliser le modèle spécifié ou celui par défaut
        model_name = model_name or self.model_name
        
        # Charger le modèle
        model = self.model_manager.load_model(model_name)
        if model is None:
            logger.error(f"Impossible de charger le modèle {model_name}")
            return None
        
        # Configurer PyTorch
        # Utiliser num_threads de la config si spécifié (pour benchmarks k=1)
        # Sinon, utiliser le nombre de cores
        num_threads = self.config.get('num_threads', len(cpu_cores))
        torch.set_num_threads(num_threads)
        logger.info(f"Threads PyTorch: {torch.get_num_threads()} (cores alloués: {len(cpu_cores)})")
        
        try:
            # Effectuer la transcription
            word_timestamps = self.config.get('whisper', {}).get('word_timestamps', True)
            
            logger.info(f"Transcription de {audio_path} avec {model_name}...")
            start_time = time.time()
            
            result = model.transcribe(
                audio_path,
                language=self.language,
                word_timestamps=word_timestamps if self.transcription_srt else False
            )
            
            elapsed_time = time.time() - start_time
            logger.info(f"Transcription terminée en {elapsed_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de la transcription de {audio_path}: {str(e)}")
            return None
    
    @staticmethod
    def format_timestamp_srt(seconds: float) -> str:
        """
        Convertit les secondes au format SRT (HH:MM:SS,mmm).
        Réutilisé depuis WhisperTranscriptor.py
        
        Args:
            seconds: Temps en secondes
        
        Returns:
            Timestamp formaté
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    @staticmethod
    def create_srt_file(segments: List[Dict], output_file: str) -> bool:
        """
        Crée un fichier SRT à partir des segments.
        Réutilisé depuis WhisperTranscriptor.py
        
        Args:
            segments: Liste des segments de transcription
            output_file: Chemin du fichier de sortie
        
        Returns:
            True si succès, False sinon
        """
        try:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, "w", encoding="utf-8") as f:
                for i, segment in enumerate(segments, 1):
                    start_time = WhisperTranscriber.format_timestamp_srt(segment["start"])
                    end_time = WhisperTranscriber.format_timestamp_srt(segment["end"])
                    text = segment["text"].strip()
                    
                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{text}\n\n")
            
            logger.info(f"Fichier SRT créé: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du fichier SRT: {str(e)}")
            return False
    
    @staticmethod
    def create_txt_file(result: Dict, output_file: str) -> bool:
        """
        Crée un fichier TXT avec la transcription complète.
        Réutilisé depuis WhisperTranscriptor.py
        
        Args:
            result: Résultat de la transcription
            output_file: Chemin du fichier de sortie
        
        Returns:
            True si succès, False sinon
        """
        try:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(result["text"].strip())
            
            logger.info(f"Fichier TXT créé: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du fichier TXT: {str(e)}")
            return False
    
    def process_and_write(
        self, 
        audio_file: str, 
        cpu_cores: List[int],
        core_index: int,
        tracker_path: Optional[str] = None,
        run_number: Optional[int] = None
    ) -> bool:
        """
        Lance la transcription et écrit les résultats dans les fichiers de sortie.
        Réutilisé depuis WhisperTranscriptor.py avec améliorations.
        
        Args:
            audio_file: Chemin du fichier audio
            cpu_cores: Liste des cœurs CPU à utiliser
            core_index: Index du processus (pour tracking)
            tracker_path: Chemin du fichier tracker (optionnel)
            run_number: Numéro du run (optionnel, pour benchmark avec répétitions)
        
        Returns:
            True si succès, False sinon
        """
        start_time = time.time()
        
        # Transcription
        result = self.transcribe_on_specific_cores(audio_file, cpu_cores)
        if result is None:
            return False
        
        # Préparer les noms de fichiers (Format STVD-MNER)
        audio_dir = os.path.dirname(audio_file)
        base_name = os.path.basename(audio_file)
        file_name_without_ext, _ = os.path.splitext(base_name)
        
        # Extraire ou générer le timestamp STVD-MNER
        # Format attendu: YYYYMMDD_HH_MM
        # Si le fichier commence déjà par un timestamp, le réutiliser
        # Sinon, utiliser l'heure actuelle
        timestamp_pattern = r'^(\d{8}_\d{2}_\d{2})'
        import re
        match = re.match(timestamp_pattern, file_name_without_ext)
        
        if match:
            # Timestamp déjà présent dans le nom de fichier
            timestamp = match.group(1)
        else:
            # Générer timestamp actuel (heure de transcription)
            timestamp = datetime.now().strftime("%Y%m%d_%H_%M_%S")
        
        # Suffixe du modèle (format STVD-MNER: wt, wb, ws, wm)
        model_suffix = self.model_manager.get_model_suffix(self.model_name)
        
        # Ajouter le numéro de run si fourni (pour benchmarks)
        run_suffix = f"_run{run_number}" if run_number is not None else ""
        
        # Générer les fichiers de sortie selon la convention STVD-MNER
        # Format: {timestamp}_transcript_{model_suffix}{run_suffix}.{ext}
        success = True
        
        if self.transcription_srt and "segments" in result and result["segments"]:
            # SRT avec sous-titres: _transcript_st_{model_suffix}{run_suffix}
            output_srt = os.path.join(audio_dir, f"{timestamp}_transcript_st_{model_suffix}{run_suffix}.srt")
            success &= self.create_srt_file(result["segments"], output_srt)
        
        if self.transcription_txt and "text" in result and result["text"].strip():
            # TXT simple: _transcript_{model_suffix}{run_suffix}
            output_txt = os.path.join(audio_dir, f"{timestamp}_transcript_{model_suffix}{run_suffix}.txt")
            success &= self.create_txt_file(result, output_txt)
        
        # Temps d'exécution
        execution_time = time.time() - start_time
        logger.info(f"Temps total d'exécution: {execution_time:.2f} secondes")
        
        # Écrire dans le tracker si spécifié
        if tracker_path:
            try:
                Path(tracker_path).parent.mkdir(parents=True, exist_ok=True)
                with open(tracker_path, 'a', encoding='utf-8') as tracker:
                    tracker.write(f"{base_name}: {execution_time:.2f} secondes\n")
            except Exception as e:
                logger.error(f"Erreur lors de l'écriture du tracker: {str(e)}")
        
        return success
