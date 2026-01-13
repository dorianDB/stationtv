"""
Station TV - Compute QoS
Script de calcul et génération des rapports QoS post-traitement.

Usage:
    python scripts/ComputeQoS.py --session-dir output/reports
"""

import sys
import argparse
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from qos.reporter import QoSReporter
from qos.metrics import MetricsCalculator
from utils.logger import setup_logger

# Logger
logger = setup_logger("ComputeQoS", level="INFO")


def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(
        description="Calcul et génération des rapports QoS - Station TV"
    )
    parser.add_argument(
        '--session-dir', '-s',
        default='output/reports',
        help="Répertoire contenant les fichiers de monitoring (défaut: output/reports)"
    )
    parser.add_argument(
        '--output-dir', '-o',
        help="Répertoire de sortie (défaut: même que session-dir)"
    )
    
    args = parser.parse_args()
    
    session_dir = Path(args.session_dir)
    output_dir = Path(args.output_dir) if args.output_dir else session_dir
    
    logger.info("=" * 80)
    logger.info("STATION TV - CALCUL DES MÉTRIQUES QoS")
    logger.info("=" * 80)
    logger.info(f"Répertoire session: {session_dir}")
    logger.info(f"Répertoire sortie: {output_dir}")
    
    # Créer le reporter
    reporter = QoSReporter(output_dir=str(output_dir))
    
    # Fichiers de monitoring
    cpu_file = session_dir / "monitoring_cpu.csv"
    memory_file = session_dir / "monitoring_memory.csv"
    
    # Vérifier l'existence des fichiers
    if not cpu_file.exists():
        logger.warning(f"Fichier CPU introuvable: {cpu_file}")
    else:
        logger.info("\nGénération du graphique CPU...")
        reporter.plot_cpu_usage(str(cpu_file))
    
    if not memory_file.exists():
        logger.warning(f"Fichier RAM introuvable: {memory_file}")
    else:
        logger.info("\nGénération du graphique RAM...")
        reporter.plot_memory_usage(str(memory_file))
    
    # Graphique de consommation énergétique
    power_file = session_dir / "monitoring_power.csv"
    if power_file.exists():
        logger.info("\nGénération du graphique consommation énergétique...")
        reporter.plot_power_usage(str(power_file))
    else:
        logger.info("\nPas de données énergétiques disponibles (monitoring_power.csv introuvable)")
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ Rapports QoS générés avec succès")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
