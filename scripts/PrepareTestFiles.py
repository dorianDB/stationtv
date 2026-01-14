"""
Station TV - Préparation des fichiers de test pour le benchmark
Script pour découper un fichier audio source en plusieurs fichiers de durées spécifiques.

Usage:
    python scripts/PrepareTestFiles.py --source chemin/vers/fichier.mp3
"""

import sys
import argparse
import subprocess
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import setup_logger

# Logger
logger = setup_logger("PrepareTestFiles", level="INFO")


def check_ffmpeg():
    """Vérifie que ffmpeg est installé."""
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            logger.info("✓ ffmpeg détecté")
            return True
        return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        logger.error("❌ ffmpeg n'est pas installé ou n'est pas dans le PATH")
        logger.error("Installez ffmpeg: https://ffmpeg.org/download.html")
        return False


def get_audio_duration(file_path: str) -> float:
    """
    Obtient la durée d'un fichier audio avec ffprobe.
    
    Args:
        file_path: Chemin du fichier audio
    
    Returns:
        Durée en secondes, ou 0 en cas d'erreur
    """
    try:
        result = subprocess.run(
            [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                file_path
            ],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            duration = float(result.stdout.strip())
            return duration
        return 0
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
        logger.warning(f"Impossible d'obtenir la durée de {file_path}")
        return 0


def extract_audio_segment(
    source_file: str,
    output_file: str,
    duration: int,
    start_offset: int = 0
) -> bool:
    """
    Extrait un segment audio d'une durée spécifique.
    
    Args:
        source_file: Fichier audio source
        output_file: Fichier de sortie
        duration: Durée à extraire (en secondes)
        start_offset: Début de l'extraction (en secondes)
    
    Returns:
        True si succès, False sinon
    """
    logger.info(f"Extraction de {duration}s depuis {Path(source_file).name}...")
    
    try:
        cmd = [
            'ffmpeg',
            '-y',  # Écraser le fichier si existe
            '-ss', str(start_offset),  # Position de départ
            '-i', source_file,  # Fichier source
            '-t', str(duration),  # Durée
            '-c', 'copy',  # Copie sans réencodage (rapide)
            output_file
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            # Vérifier que le fichier existe
            if Path(output_file).exists():
                actual_duration = get_audio_duration(output_file)
                logger.info(f"  ✓ Créé: {output_file} (durée: {actual_duration:.1f}s)")
                return True
            else:
                logger.error(f"  ❌ Fichier non créé: {output_file}")
                return False
        else:
            logger.error(f"  ❌ Erreur ffmpeg: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"  ❌ Timeout lors de l'extraction")
        return False
    except Exception as e:
        logger.error(f"  ❌ Erreur: {str(e)}")
        return False


def prepare_test_files(
    source_file: str,
    output_dir: str,
    durations: list,
    start_offset: int = 0
):
    """
    Prépare tous les fichiers de test.
    
    Args:
        source_file: Fichier audio source
        output_dir: Répertoire de sortie
        durations: Liste des durées à extraire (en secondes)
        start_offset: Offset de départ dans le fichier source
    """
    source_path = Path(source_file)
    
    if not source_path.exists():
        logger.error(f"Fichier source introuvable: {source_file}")
        return
    
    # Vérifier la durée du fichier source
    source_duration = get_audio_duration(str(source_path))
    logger.info(f"Fichier source: {source_path.name}")
    logger.info(f"Durée source: {source_duration:.1f}s ({source_duration/60:.1f} min)")
    
    max_duration = max(durations) + start_offset
    if source_duration < max_duration:
        logger.warning(
            f"⚠️ Le fichier source ({source_duration:.0f}s) est plus court que "
            f"la durée maximale nécessaire ({max_duration}s)"
        )
        logger.warning("Certains fichiers risquent d'être incomplets")
    
    # Créer le répertoire de sortie
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Répertoire de sortie: {output_path}")
    
    logger.info("=" * 80)
    logger.info("EXTRACTION DES SEGMENTS AUDIO")
    logger.info("=" * 80)
    
    # Extraire chaque durée
    successes = 0
    for duration in durations:
        # Nom du fichier de sortie
        output_file = output_path / f"test_{duration}s{source_path.suffix}"
        
        if extract_audio_segment(str(source_path), str(output_file), duration, start_offset):
            successes += 1
    
    logger.info("=" * 80)
    logger.info(f"✅ {successes}/{len(durations)} fichiers créés avec succès")
    logger.info("=" * 80)
    
    # Afficher un résumé
    logger.info("\nFichiers créés:")
    for duration in durations:
        output_file = output_path / f"test_{duration}s{source_path.suffix}"
        if output_file.exists():
            size_mb = output_file.stat().st_size / (1024 * 1024)
            logger.info(f"  - {output_file.name} ({size_mb:.2f} MB)")


def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(
        description="Préparation des fichiers de test pour le benchmark Whisper"
    )
    parser.add_argument(
        '--source', '-s',
        required=True,
        help="Fichier audio source (MP3, WAV, etc.)"
    )
    parser.add_argument(
        '--output', '-o',
        default='bdd',
        help="Répertoire de sortie (défaut: bdd)"
    )
    parser.add_argument(
        '--durations', '-d',
        nargs='+',
        type=int,
        default=[240, 480, 720, 960, 1200],
        help="Durées à extraire en secondes (défaut: 240 480 720 960 1200)"
    )
    parser.add_argument(
        '--offset',
        type=int,
        default=0,
        help="Offset de départ dans le fichier source en secondes (défaut: 0)"
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 80)
    logger.info("PRÉPARATION DES FICHIERS DE TEST POUR BENCHMARK")
    logger.info("=" * 80)
    
    # Vérifier ffmpeg
    if not check_ffmpeg():
        logger.error("Impossible de continuer sans ffmpeg")
        return
    
    # Préparer les fichiers
    prepare_test_files(
        source_file=args.source,
        output_dir=args.output,
        durations=args.durations,
        start_offset=args.offset
    )
    
    logger.info("\n✅ Préparation terminée!")
    logger.info(f"📁 Les fichiers sont prêts dans: {args.output}")
    logger.info("\nProchaine étape:")
    logger.info("  python scripts/BenchmarkModels.py --config config/benchmark_config.yaml")


if __name__ == "__main__":
    main()
