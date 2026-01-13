"""
Station TV - Script de test principal
Exécute tous les tests unitaires du projet
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_core import run_tests
from utils.logger import setup_logger

logger = setup_logger("TestRunner", level="INFO")


def main():
    """Exécute tous les tests"""
    logger.info("=" * 80)
    logger.info("STATION TV - TESTS UNITAIRES")
    logger.info("=" * 80)
    
    logger.info("\nExécution des tests...\n")
    
    success = run_tests()
    
    if success:
        logger.info("\n" + "=" * 80)
        logger.info("✅ TOUS LES TESTS SONT PASSÉS")
        logger.info("=" * 80)
        return 0
    else:
        logger.error("\n" + "=" * 80)
        logger.error("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        logger.error("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
