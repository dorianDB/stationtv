"""
Station TV - Basic Test Whisper
Script de test unitaire des modèles Whisper sur un fichier audio court.

Usage:
    python scripts/BasicTestWhisper.py --input <audio_file> --model small
"""

import sys
import argparse
import yaml
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.transcription import WhisperTranscriber
from core.models import ModelManager
from utils.logger import setup_logger

# Logger
logger = setup_logger("BasicTestWhisper", level="INFO")


def load_config(config_file: str) -> dict:
    """Charge la configuration depuis un fichier YAML."""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"Configuration chargée depuis {config_file}")
        return config
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la configuration: {str(e)}")
        return {}


def test_model(audio_file: str, model_name: str, config: dict):
    """
    Teste un modèle Whisper sur un fichier audio.
    
    Args:
        audio_file: Chemin du fichier audio
        model_name: Nom du modèle à tester
        config: Configuration
    """
    logger.info("=" * 80)
    logger.info(f"TEST DU MODÈLE WHISPER: {model_name.upper()}")
    logger.info("=" * 80)
    
    # Vérifier que le fichier existe
    if not Path(audio_file).exists():
        logger.error(f"Fichier audio introuvable: {audio_file}")
        return
    
    logger.info(f"Fichier audio: {audio_file}")
    logger.info(f"Modèle: {model_name}")
    
    # Mettre à jour la config avec le modèle spécifié
    if 'whisper' not in config:
        config['whisper'] = {}
    config['whisper']['model'] = model_name
    
    # Créer le transcripteur
    transcriber = WhisperTranscriber(config)
    
    # Nombre de cœurs CPU à utiliser (par défaut: 4)
    cpu_cores = list(range(4))
    logger.info(f"Cœurs CPU utilisés: {cpu_cores}")
    
    # Lancer la transcription
    logger.info("\nDébut de la transcription...")
    result = transcriber.transcribe_on_specific_cores(
        audio_file,
        cpu_cores,
        model_name=model_name
    )
    
    if result is None:
        logger.error("❌ Échec de la transcription")
        return
    
    # Afficher les résultats
    logger.info("\n" + "=" * 80)
    logger.info("RÉSULTATS DE LA TRANSCRIPTION")
    logger.info("=" * 80)
    
    logger.info(f"\nTexte transcrit ({len(result['text'])} caractères):")
    logger.info("-" * 80)
    logger.info(result['text'][:500] + ("..." if len(result['text']) > 500 else ""))
    logger.info("-" * 80)
    
    if 'segments' in result:
        logger.info(f"\nNombre de segments: {len(result['segments'])}")
        logger.info("Premiers segments:")
        for i, seg in enumerate(result['segments'][:3], 1):
            logger.info(f"  {i}. [{seg['start']:.2f}s - {seg['end']:.2f}s] {seg['text'].strip()}")
    
    # Écrire les fichiers de sortie
    logger.info("\nÉcriture des fichiers de sortie...")
    success = transcriber.process_and_write(
        audio_file,
        cpu_cores,
        core_index=1
    )
    
    if success:
        logger.info("✅ Test terminé avec succès!")
    else:
        logger.error("❌ Erreur lors de l'écriture des fichiers")


def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(
        description="Test unitaire des modèles Whisper - Station TV"
    )
    parser.add_argument(
        '--input', '-i',
        required=True,
        help="Chemin du fichier audio à transcrire"
    )
    parser.add_argument(
        '--model', '-m',
        default='small',
        choices=['tiny', 'base', 'small', 'medium', 'large'],
        help="Modèle Whisper à utiliser (défaut: small)"
    )
    parser.add_argument(
        '--config', '-c',
        default='config/default_config.yaml',
        help="Fichier de configuration YAML (défaut: config/default_config.yaml)"
    )
    
    args = parser.parse_args()
    
    # Charger la configuration
    config = load_config(args.config)
    if not config:
        logger.warning("Utilisation de la configuration par défaut")
        config = {
            'whisper': {
                'model': args.model,
                'language': 'fr',
                'device': 'cpu',
                'output_formats': {
                    'txt': True,
                    'srt': True,
                    'csv': False,
                    'json': False
                }
            }
        }
    
    # Lancer le test
    test_model(args.input, args.model, config)


if __name__ == "__main__":
    main()
