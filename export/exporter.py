"""
Station TV - Exporter
Export des transcriptions vers différents formats structurés
"""

import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class TranscriptionExporter:
    """
    Exporteur de transcriptions vers formats structurés (CSV, JSON).
    """
    
    def __init__(self, output_dir: str = "output/transcriptions"):
        """
        Initialise l'exporteur.
        
        Args:
            output_dir: Répertoire de sortie
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"TranscriptionExporter initialisé (output_dir={output_dir})")
    
    def export_to_json(
        self,
        transcription: Dict,
        output_file: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Exporte une transcription au format JSON structuré.
        
        Args:
            transcription: Résultat Whisper (dict avec 'text', 'segments', etc.)
            output_file: Chemin du fichier de sortie
            metadata: Métadonnées additionnelles (chaîne, date, émission)
        
        Returns:
            True si succès, False sinon
        """
        try:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            
            # Structure JSON finale
            export_data = {
                "version": "1.0",
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {},
                "transcription": {
                    "text": transcription.get("text", ""),
                    "language": transcription.get("language", "fr"),
                    "duration": transcription.get("duration", 0.0)
                },
                "segments": []
            }
            
            # Ajouter les segments si disponibles
            if "segments" in transcription and transcription["segments"]:
                for seg in transcription["segments"]:
                    export_data["segments"].append({
                        "id": seg.get("id", 0),
                        "start": seg.get("start", 0.0),
                        "end": seg.get("end", 0.0),
                        "text": seg.get("text", "").strip()
                    })
            
            # Écrire le JSON
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Export JSON réussi: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'export JSON: {str(e)}")
            return False
    
    def export_to_csv(
        self,
        transcriptions: List[Dict],
        output_file: str,
        include_metadata: bool = True
    ) -> bool:
        """
        Exporte plusieurs transcriptions au format CSV.
        
        Args:
            transcriptions: Liste de transcriptions avec métadonnées
            output_file: Chemin du fichier CSV de sortie
            include_metadata: Inclure les colonnes de métadonnées
        
        Returns:
            True si succès, False sinon
        """
        try:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            
            # Définir les colonnes
            if include_metadata:
                fieldnames = [
                    'file_path', 'channel', 'date', 'time', 'emission',
                    'duration', 'text', 'segment_count'
                ]
            else:
                fieldnames = ['file_path', 'duration', 'text', 'segment_count']
            
            # Écrire le CSV
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for trans in transcriptions:
                    row = {}
                    
                    # Données de base
                    row['file_path'] = trans.get('file_path', '')
                    row['duration'] = trans.get('duration', 0.0)
                    row['text'] = trans.get('text', '').replace('\n', ' ')
                    row['segment_count'] = len(trans.get('segments', []))
                    
                    # Métadonnées (si demandées)
                    if include_metadata:
                        metadata = trans.get('metadata', {})
                        row['channel'] = metadata.get('channel', '')
                        row['date'] = metadata.get('date', '')
                        row['time'] = metadata.get('time', '')
                        row['emission'] = metadata.get('emission', '')
                    
                    writer.writerow(row)
            
            logger.info(f"Export CSV réussi: {output_file} ({len(transcriptions)} entrées)")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'export CSV: {str(e)}")
            return False
    
    def create_backup(
        self,
        source_dir: str,
        backup_dir: str,
        compression: bool = False
    ) -> bool:
        """
        Crée une sauvegarde des transcriptions.
        
        Args:
            source_dir: Répertoire source
            backup_dir: Répertoire de backup
            compression: Compresser en archive ZIP
        
        Returns:
            True si succès, False sinon
        """
        try:
            import shutil
            
            source = Path(source_dir)
            backup = Path(backup_dir)
            
            if not source.exists():
                logger.error(f"Répertoire source introuvable: {source_dir}")
                return False
            
            # Créer le répertoire de backup
            backup.mkdir(parents=True, exist_ok=True)
            
            # Nom du backup avec timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"transcriptions_backup_{timestamp}"
            
            if compression:
                # Créer une archive ZIP
                archive_path = backup / backup_name
                shutil.make_archive(
                    str(archive_path),
                    'zip',
                    source_dir
                )
                logger.info(f"Backup compressé créé: {archive_path}.zip")
            else:
                # Copier le répertoire
                dest = backup / backup_name
                shutil.copytree(source_dir, dest)
                logger.info(f"Backup créé: {dest}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du backup: {str(e)}")
            return False
