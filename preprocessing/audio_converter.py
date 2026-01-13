"""
Station TV - Audio Converter
Conversion de fichiers audio MP3 → WAV avec normalisation
"""

import subprocess
import os
from pathlib import Path
from typing import Optional, Tuple
from utils.logger import get_logger

logger = get_logger(__name__)


class AudioConverter:
    """
    Convertisseur audio utilisant FFmpeg.
    """
    
    def __init__(
        self,
        target_format: str = "wav",
        sample_rate: int = 48000,
        channels: int = 1,
        bit_depth: int = 16
    ):
        """
        Initialise le convertisseur.
        
        Args:
            target_format: Format cible (wav)
            sample_rate: Fréquence d'échantillonnage (Hz)
            channels: Nombre de canaux (1=mono, 2=stéréo)
            bit_depth: Profondeur de bits (16 pour PCM16)
        """
        self.target_format = target_format
        self.sample_rate = sample_rate
        self.channels = channels
        self.bit_depth = bit_depth
        
        logger.info(
            f"AudioConverter initialisé: {sample_rate}Hz, {channels}ch, {bit_depth}bit"
        )
    
    def check_ffmpeg(self) -> bool:
        """
        Vérifie si FFmpeg est installé.
        
        Returns:
            True si FFmpeg est disponible, False sinon
        """
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info("FFmpeg détecté")
                return True
            else:
                logger.error("FFmpeg introuvable")
                return False
        except Exception as e:
            logger.error(f"Erreur lors de la vérification FFmpeg: {str(e)}")
            return False
    
    def convert_to_wav(
        self,
        input_file: str,
        output_file: Optional[str] = None,
        overwrite: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Convertit un fichier audio en WAV normalisé.
        
        Args:
            input_file: Chemin du fichier source
            output_file: Chemin du fichier de sortie (optionnel)
            overwrite: Écraser le fichier s'il existe
        
        Returns:
            Tuple (succès, chemin_sortie)
        """
        # Vérifier que le fichier source existe
        if not Path(input_file).exists():
            logger.error(f"Fichier source introuvable: {input_file}")
            return False, None
        
        # Générer le nom du fichier de sortie
        if output_file is None:
            input_path = Path(input_file)
            output_file = str(input_path.parent / f"{input_path.stem}.wav")
        
        # Vérifier si le fichier existe déjà
        if Path(output_file).exists() and not overwrite:
            logger.warning(f"Fichier existe déjà: {output_file}")
            return False, output_file
        
        # Créer le répertoire de sortie si nécessaire
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Construire la commande FFmpeg
        # -i : fichier d'entrée
        # -ar : sample rate
        # -ac : nombre de canaux
        # -sample_fmt : format échantillon (s16 = signé 16 bits)
        # -y : écraser sans demander
        cmd = [
            'ffmpeg',
            '-i', input_file,
            '-ar', str(self.sample_rate),
            '-ac', str(self.channels),
            '-sample_fmt', 's16',
            '-y' if overwrite else '-n',
            output_file
        ]
        
        try:
            logger.info(f"Conversion: {Path(input_file).name} → {Path(output_file).name}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes max
            )
            
            if result.returncode == 0:
                logger.info(f"✓ Conversion réussie: {output_file}")
                return True, output_file
            else:
                logger.error(f"✗ Échec conversion: {result.stderr}")
                return False, None
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout lors de la conversion de {input_file}")
            return False, None
        except Exception as e:
            logger.error(f"Erreur lors de la conversion: {str(e)}")
            return False, None
    
    def convert_batch(
        self,
        input_files: list,
        output_dir: Optional[str] = None,
        overwrite: bool = False
    ) -> dict:
        """
        Convertit un lot de fichiers audio.
        
        Args:
            input_files: Liste des fichiers à convertir
            output_dir: Répertoire de sortie (optionnel)
            overwrite: Écraser les fichiers existants
        
        Returns:
            Dictionnaire avec statistiques de conversion
        """
        results = {
            'total': len(input_files),
            'success': 0,
            'failed': 0,
            'converted_files': []
        }
        
        logger.info(f"Conversion batch de {len(input_files)} fichiers...")
        
        for input_file in input_files:
            # Déterminer le fichier de sortie
            if output_dir:
                output_file = str(
                    Path(output_dir) / f"{Path(input_file).stem}.wav"
                )
            else:
                output_file = None
            
            # Convertir
            success, out_path = self.convert_to_wav(
                input_file,
                output_file,
                overwrite
            )
            
            if success:
                results['success'] += 1
                results['converted_files'].append(out_path)
            else:
                results['failed'] += 1
        
        logger.info(
            f"Conversion batch terminée: "
            f"{results['success']} succès, {results['failed']} échecs"
        )
        
        return results
