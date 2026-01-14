"""
Station TV - Vérification de l'environnement pour le benchmark
Vérifie que tout est prêt pour lancer un benchmark.

Usage:
    python scripts/CheckBenchmarkSetup.py
"""

import sys
import subprocess
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import setup_logger

# Logger
logger = setup_logger("CheckBenchmarkSetup", level="INFO")


def check_python_version():
    """Vérifie la version de Python."""
    version = sys.version_info
    logger.info(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 8:
        logger.info("  ✓ Version Python OK (>= 3.8)")
        return True
    else:
        logger.error("  ❌ Python 3.8 ou supérieur requis")
        return False


def check_module(module_name: str, package_name: str = None):
    """Vérifie qu'un module Python est installé."""
    package_name = package_name or module_name
    
    try:
        __import__(module_name)
        logger.info(f"  ✓ {module_name} installé")
        return True
    except ImportError:
        logger.warning(f"  ⚠️ {module_name} non installé")
        logger.warning(f"     Installez avec: pip install {package_name}")
        return False


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
            # Extraire la version
            first_line = result.stdout.split('\n')[0]
            logger.info(f"  ✓ ffmpeg installé: {first_line}")
            return True
        return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        logger.warning("  ⚠️ ffmpeg non trouvé")
        logger.warning("     Requis pour PrepareTestFiles.py")
        logger.warning("     Téléchargez sur: https://ffmpeg.org/download.html")
        return False


def check_file_exists(file_path: str, description: str):
    """Vérifie qu'un fichier existe."""
    path = Path(file_path)
    
    if path.exists():
        logger.info(f"  ✓ {description}: {file_path}")
        return True
    else:
        logger.warning(f"  ⚠️ {description} introuvable: {file_path}")
        return False


def check_directory(dir_path: str, description: str, create: bool = True):
    """Vérifie qu'un répertoire existe."""
    path = Path(dir_path)
    
    if path.exists():
        logger.info(f"  ✓ {description}: {dir_path}")
        return True
    else:
        if create:
            logger.warning(f"  ⚠️ {description} n'existe pas, création...")
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"     Créé: {dir_path}")
            return True
        else:
            logger.warning(f"  ⚠️ {description} n'existe pas: {dir_path}")
            return False


def check_audio_files(bdd_dir: str):
    """Vérifie la présence de fichiers audio de test."""
    path = Path(bdd_dir)
    
    if not path.exists():
        logger.warning(f"  ⚠️ Répertoire {bdd_dir} n'existe pas")
        return False
    
    # Chercher les fichiers de test
    test_files = list(path.glob("test_*.mp3")) + list(path.glob("test_*.wav"))
    
    if test_files:
        logger.info(f"  ✓ {len(test_files)} fichier(s) de test trouvé(s)")
        for f in test_files:
            logger.info(f"     - {f.name}")
        return True
    else:
        logger.warning(f"  ⚠️ Aucun fichier de test trouvé dans {bdd_dir}")
        logger.warning(f"     Utilisez: python scripts/PrepareTestFiles.py")
        return False


def check_config_file(config_file: str):
    """Vérifie et analyse le fichier de configuration."""
    if not check_file_exists(config_file, "Fichier de configuration"):
        return False
    
    try:
        import yaml
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Vérifier les sections importantes
        benchmark_config = config.get('benchmark', {})
        
        models = benchmark_config.get('models', [])
        repetitions = benchmark_config.get('repetitions', 0)
        audio_files = benchmark_config.get('audio_files', [])
        
        logger.info(f"  Configuration:")
        logger.info(f"     Modèles: {', '.join(models)}")
        logger.info(f"     Répétitions: {repetitions}")
        logger.info(f"     Fichiers audio: {len(audio_files)}")
        
        return True
        
    except Exception as e:
        logger.error(f"  ❌ Erreur lors de la lecture de la config: {str(e)}")
        return False


def main():
    """Fonction principale."""
    logger.info("=" * 80)
    logger.info("VÉRIFICATION DE L'ENVIRONNEMENT BENCHMARK")
    logger.info("=" * 80)
    
    all_checks = []
    
    # 1. Version Python
    logger.info("\n1. Vérification de Python")
    logger.info("-" * 80)
    all_checks.append(check_python_version())
    
    # 2. Modules requis
    logger.info("\n2. Vérification des modules Python")
    logger.info("-" * 80)
    all_checks.append(check_module('yaml', 'pyyaml'))
    all_checks.append(check_module('torch'))
    all_checks.append(check_module('whisper', 'openai-whisper'))
    
    # Modules optionnels
    logger.info("\nModules optionnels (pour GenerateExcelReport.py):")
    check_module('pandas')
    check_module('openpyxl')
    
    # 3. Outils externes
    logger.info("\n3. Vérification des outils externes")
    logger.info("-" * 80)
    check_ffmpeg()  # Optionnel pour PrepareTestFiles
    
    # 4. Structure des répertoires
    logger.info("\n4. Vérification de la structure des répertoires")
    logger.info("-" * 80)
    all_checks.append(check_directory('config', 'Répertoire config', create=False))
    all_checks.append(check_directory('scripts', 'Répertoire scripts', create=False))
    check_directory('bdd', 'Répertoire des fichiers audio', create=True)
    check_directory('output', 'Répertoire de sortie', create=True)
    
    # 5. Fichiers de configuration
    logger.info("\n5. Vérification des fichiers de configuration")
    logger.info("-" * 80)
    all_checks.append(check_config_file('config/benchmark_config.yaml'))
    
    # 6. Scripts
    logger.info("\n6. Vérification des scripts")
    logger.info("-" * 80)
    all_checks.append(check_file_exists('scripts/BenchmarkModels.py', 'Script de benchmark'))
    check_file_exists('scripts/PrepareTestFiles.py', 'Script de préparation')
    check_file_exists('scripts/GenerateExcelReport.py', 'Script de rapport Excel')
    
    # 7. Fichiers audio de test
    logger.info("\n7. Vérification des fichiers audio de test")
    logger.info("-" * 80)
    check_audio_files('bdd')
    
    # 8. Modules core
    logger.info("\n8. Vérification des modules core")
    logger.info("-" * 80)
    all_checks.append(check_file_exists('core/transcription.py', 'Module transcription'))
    all_checks.append(check_file_exists('core/models.py', 'Module models'))
    all_checks.append(check_file_exists('utils/logger.py', 'Module logger'))
    
    # Résumé
    logger.info("\n" + "=" * 80)
    logger.info("RÉSUMÉ")
    logger.info("=" * 80)
    
    if all(all_checks):
        logger.info("✅ Tous les éléments essentiels sont présents!")
        logger.info("\nVous pouvez maintenant:")
        logger.info("  1. Préparer des fichiers de test:")
        logger.info("     python scripts/PrepareTestFiles.py --source votre_fichier.mp3")
        logger.info("\n  2. Lancer le benchmark:")
        logger.info("     python scripts/BenchmarkModels.py")
        logger.info("\n  3. Générer le rapport Excel:")
        logger.info("     python scripts/GenerateExcelReport.py")
    else:
        logger.warning("⚠️ Certains éléments sont manquants")
        logger.warning("Consultez les avertissements ci-dessus pour corriger")
        logger.info("\nDocumentation:")
        logger.info("  - docs/BENCHMARK_QUICKSTART.md - Guide de démarrage rapide")
        logger.info("  - docs/BENCHMARK_GUIDE.md - Guide complet")


if __name__ == "__main__":
    main()
