"""
Station TV - QoS Reporter
Génération de rapports et graphiques de performance
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from pathlib import Path
from typing import Dict, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

# Style des graphiques
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)


class QoSReporter:
    """
    Générateur de rapports QoS avec graphiques.
    """
    
    def __init__(self, output_dir: str = "output/reports"):
        """
        Initialise le générateur de rapports.
        
        Args:
            output_dir: Répertoire de sortie
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"QoSReporter initialisé (output_dir={output_dir})")
    
    def plot_cpu_usage(
        self, 
        cpu_csv_file: str, 
        output_file: Optional[str] = None
    ) -> bool:
        """
        Génère un graphique de l'utilisation CPU.
        
        Args:
            cpu_csv_file: Fichier CSV avec données CPU
            output_file: Fichier de sortie PNG (optionnel)
        
        Returns:
            True si succès, False sinon
        """
        try:
            # Lire les données
            df = pd.read_csv(cpu_csv_file)
            
            if df.empty:
                logger.warning("Fichier CPU vide")
                return False
            
            # Créer le graphique
            plt.figure(figsize=(14, 6))
            plt.plot(range(len(df)), df['CPU_Usage_Percent'], color='#2E86AB', linewidth=1.5)
            plt.fill_between(range(len(df)), df['CPU_Usage_Percent'], alpha=0.3, color='#2E86AB')
            
            plt.title('Utilisation CPU - Station TV', fontsize=16, fontweight='bold')
            plt.xlabel('Temps (échantillons)', fontsize=12)
            plt.ylabel('Utilisation CPU (%)', fontsize=12)
            plt.ylim(0, 100)
            plt.grid(True, alpha=0.3)
            
            # Ajouter des statistiques
            mean_cpu = df['CPU_Usage_Percent'].mean()
            max_cpu = df['CPU_Usage_Percent'].max()
            plt.axhline(y=mean_cpu, color='red', linestyle='--', label=f'Moyenne: {mean_cpu:.1f}%')
            plt.legend()
            
            # Sauvegarder
            if output_file is None:
                output_file = self.output_dir / "cpu_usage.png"
            
            plt.tight_layout()
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Graphique CPU généré: {output_file}")
            logger.info(f"  CPU moyen: {mean_cpu:.1f}%, CPU max: {max_cpu:.1f}%")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du graphique CPU: {str(e)}")
            return False
    
    def plot_memory_usage(
        self, 
        memory_csv_file: str, 
        output_file: Optional[str] = None
    ) -> bool:
        """
        Génère un graphique de l'utilisation RAM.
        
        Args:
            memory_csv_file: Fichier CSV avec données RAM
            output_file: Fichier de sortie PNG (optionnel)
        
        Returns:
            True si succès, False sinon
        """
        try:
            # Lire les données
            df = pd.read_csv(memory_csv_file)
            
            if df.empty:
                logger.warning("Fichier RAM vide")
                return False
            
            # Créer le graphique
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
            
            # Graphique 1: Pourcentage
            ax1.plot(range(len(df)), df['Memory_Usage_Percent'], color='#A23B72', linewidth=1.5)
            ax1.fill_between(range(len(df)), df['Memory_Usage_Percent'], alpha=0.3, color='#A23B72')
            ax1.set_title('Utilisation RAM (%) - Station TV', fontsize=14, fontweight='bold')
            ax1.set_xlabel('Temps (échantillons)', fontsize=11)
            ax1.set_ylabel('Utilisation RAM (%)', fontsize=11)
            ax1.set_ylim(0, 100)
            ax1.grid(True, alpha=0.3)
            
            mean_mem = df['Memory_Usage_Percent'].mean()
            max_mem = df['Memory_Usage_Percent'].max()
            ax1.axhline(y=mean_mem, color='red', linestyle='--', label=f'Moyenne: {mean_mem:.1f}%')
            ax1.axhline(y=90, color='orange', linestyle=':', label='Seuil alerte: 90%')
            ax1.legend()
            
            # Graphique 2: Valeurs absolues (Go)
            if 'Memory_Used_GB' in df.columns and 'Memory_Total_GB' in df.columns:
                ax2.plot(range(len(df)), df['Memory_Used_GB'], color='#F18F01', linewidth=1.5, label='RAM utilisée')
                ax2.axhline(y=df['Memory_Total_GB'].iloc[0], color='gray', linestyle='--', label=f"RAM totale: {df['Memory_Total_GB'].iloc[0]:.1f} Go")
                ax2.fill_between(range(len(df)), df['Memory_Used_GB'], alpha=0.3, color='#F18F01')
                ax2.set_title('Utilisation RAM (Go) - Station TV', fontsize=14, fontweight='bold')
                ax2.set_xlabel('Temps (échantillons)', fontsize=11)
                ax2.set_ylabel('RAM utilisée (Go)', fontsize=11)
                ax2.grid(True, alpha=0.3)
                ax2.legend()
            
            # Sauvegarder
            if output_file is None:
                output_file = self.output_dir / "memory_usage.png"
            
            plt.tight_layout()
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Graphique RAM généré: {output_file}")
            logger.info(f"  RAM moyenne: {mean_mem:.1f}%, RAM max: {max_mem:.1f}%")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du graphique RAM: {str(e)}")
            return False
    
    def generate_summary_report(
        self, 
        metrics_summary: Dict, 
        output_file: Optional[str] = None
    ) -> bool:
        """
        Génère un rapport texte avec résumé des métriques.
        
        Args:
            metrics_summary: Dictionnaire de métriques (depuis MetricsCalculator)
            output_file: Fichier de sortie (optionnel)
        
        Returns:
            True si succès, False sinon
        """
        try:
            if output_file is None:
                output_file = self.output_dir / "summary_report.txt"
            
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("RAPPORT QoS - STATION TV - TRANSCRIPTION AUDIO\n")
                f.write("=" * 80 + "\n\n")
                
                f.write("RÉSUMÉ DE LA SESSION\n")
                f.write("-" * 80 + "\n")
                f.write(f"Durée de la session: {metrics_summary.get('session_duration_hours', 0):.2f} heures\n")
                f.write(f"Nombre total de fichiers: {metrics_summary.get('total_files', 0)}\n")
                f.write(f"Fichiers réussis: {metrics_summary.get('successful_files', 0)}\n")
                f.write(f"Fichiers échoués: {metrics_summary.get('failed_files', 0)}\n")
                f.write(f"Taux de réussite: {metrics_summary.get('success_rate', 0)*100:.1f}%\n\n")
                
                f.write("PERFORMANCE\n")
                f.write("-" * 80 + "\n")
                f.write(f"Durée audio totale traitée: {metrics_summary.get('total_audio_duration_hours', 0):.2f} heures\n")
                f.write(f"Temps de traitement total: {metrics_summary.get('total_processing_time_hours', 0):.2f} heures\n")
                f.write(f"Throughput (débit): {metrics_summary.get('throughput', 0):.2f}× temps réel\n")
                f.write(f"Temps moyen par fichier: {metrics_summary.get('average_processing_time_seconds', 0):.2f} secondes\n\n")
                
                f.write("OBJECTIFS QoS\n")
                f.write("-" * 80 + "\n")
                throughput = metrics_summary.get('throughput', 0)
                if throughput >= 5:
                    f.write("✓ Throughput ≥ 5× (modèle small) : ATTEINT\n")
                elif throughput >= 1:
                    f.write("✓ Throughput ≥ 1× (modèle medium) : ATTEINT\n")
                else:
                    f.write("✗ Throughput insuffisant\n")
                
                success_rate = metrics_summary.get('success_rate', 0)
                if success_rate >= 0.99:
                    f.write("✓ Taux de réussite ≥ 99% : ATTEINT\n")
                else:
                    f.write(f"⚠ Taux de réussite {success_rate*100:.1f}% < 99%\n")
                
                f.write("\n" + "=" * 80 + "\n")
            
            logger.info(f"Rapport de synthèse généré: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport: {str(e)}")
            return False
    
    def plot_power_usage(self, csv_file: str) -> str:
        """
        Génère un graphique de consommation énergétique.
        
        Args:
            csv_file: Chemin vers monitoring_power.csv
        
        Returns:
            Chemin du fichier PNG généré
        """
        try:
            # Lire les données
            df = pd.read_csv(csv_file)
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            
            # Créer la figure avec 2 sous-graphiques
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
            
            # === Graphique 1: Puissance instantanée ===
            ax1.plot(df['Timestamp'], df['Power_W'], 
                    color='#FF6B35', linewidth=1.5, label='Puissance instantanée')
            
            # Ligne moyenne
            avg_power = df['Power_W'].mean()
            ax1.axhline(y=avg_power, color='#004E89', linestyle='--', 
                       linewidth=2, label=f'Moyenne: {avg_power:.1f}W')
            
            ax1.set_xlabel('Temps', fontsize=11)
            ax1.set_ylabel('Puissance (W)', fontsize=11)
            ax1.set_title('Consommation Énergétique - Puissance Instantanée', 
                         fontsize=13, fontweight='bold', pad=15)
            ax1.legend(loc='upper right', fontsize=10)
            ax1.grid(True, alpha=0.3, linestyle=':', linewidth=0.8)
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            
            # === Graphique 2: Énergie cumulée et coûts ===
            ax2_twin = ax2.twinx()
            
            # Énergie (axe gauche)
            line1 = ax2.plot(df['Timestamp'], df['Energy_kWh'], 
                           color='#2ECC71', linewidth=2, label='Énergie (kWh)')
            
            # Coût (axe droit)
            line2 = ax2_twin.plot(df['Timestamp'], df['Cost_EUR'], 
                                 color='#E74C3C', linewidth=2, label='Coût (€)')
            
            ax2.set_xlabel('Temps', fontsize=11)
            ax2.set_ylabel('Énergie Cumulée (kWh)', fontsize=11, color='#2ECC71')
            ax2_twin.set_ylabel('Coût Cumulé (€)', fontsize=11, color='#E74C3C')
            ax2.set_title('Consommation Cumulée - Énergie et Coût', 
                         fontsize=13, fontweight='bold', pad=15)
            
            # Légende combinée
            lines = line1 + line2
            labels = [l.get_label() for l in lines]
            ax2.legend(lines, labels, loc='upper left', fontsize=10)
            
            ax2.grid(True, alpha=0.3, linestyle=':', linewidth=0.8)
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax2.tick_params(axis='y', labelcolor='#2ECC71')
            ax2_twin.tick_params(axis='y', labelcolor='#E74C3C')
            
            # Statistiques finales en annotation
            final_kwh = df['Energy_kWh'].iloc[-1]
            final_cost = df['Cost_EUR'].iloc[-1]
            final_carbon = df['Carbon_kgCO2'].iloc[-1]
            
            stats_text = (
                f"Total: {final_kwh:.3f} kWh | "
                f"{final_cost:.2f} € | "
                f"{final_carbon:.2f} kg CO₂"
            )
            fig.text(0.5, 0.02, stats_text, ha='center', fontsize=11, 
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            
            # Ajustement
            plt.tight_layout(rect=[0, 0.03, 1, 1])
            
            # Sauvegarder
            output_file = Path(self.output_dir) / "power_usage.png"
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Graphique énergétique généré: {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Erreur génération graphique énergie: {str(e)}")
            return ""
    
    def plot_io_usage(
        self, 
        io_csv_file: str, 
        output_file: Optional[str] = None
    ) -> bool:
        """
        Génère un graphique de l'utilisation I/O disque.
        
        Args:
            io_csv_file: Fichier CSV avec données I/O
            output_file: Fichier de sortie PNG (optionnel)
        
        Returns:
            True si succès, False sinon
        """
        try:
            df = pd.read_csv(io_csv_file)
            
            if df.empty:
                logger.warning("Fichier I/O vide")
                return False
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
            
            # Graphique 1: Pourcentage I/O
            ax1.plot(range(len(df)), df['IO_Usage_Percent'], color='#E85D04', linewidth=1.5)
            ax1.fill_between(range(len(df)), df['IO_Usage_Percent'], alpha=0.3, color='#E85D04')
            ax1.set_title('Utilisation I/O Disque (%) - Station TV', fontsize=14, fontweight='bold')
            ax1.set_xlabel('Temps (échantillons)', fontsize=11)
            ax1.set_ylabel('Utilisation I/O (%)', fontsize=11)
            ax1.set_ylim(0, 100)
            ax1.grid(True, alpha=0.3)
            
            mean_io = df['IO_Usage_Percent'].mean()
            max_io = df['IO_Usage_Percent'].max()
            ax1.axhline(y=mean_io, color='red', linestyle='--', label=f'Moyenne: {mean_io:.1f}%')
            ax1.legend()
            
            # Graphique 2: Débit lecture/écriture (MB/s)
            ax2.plot(range(len(df)), df['Read_MB_s'], color='#2196F3', linewidth=1.5, label='Lecture (MB/s)')
            ax2.plot(range(len(df)), df['Write_MB_s'], color='#FF5722', linewidth=1.5, label='Écriture (MB/s)')
            ax2.fill_between(range(len(df)), df['Read_MB_s'], alpha=0.2, color='#2196F3')
            ax2.fill_between(range(len(df)), df['Write_MB_s'], alpha=0.2, color='#FF5722')
            ax2.set_title('Débit I/O (MB/s) - Station TV', fontsize=14, fontweight='bold')
            ax2.set_xlabel('Temps (échantillons)', fontsize=11)
            ax2.set_ylabel('Débit (MB/s)', fontsize=11)
            ax2.grid(True, alpha=0.3)
            ax2.legend()
            
            if output_file is None:
                output_file = self.output_dir / "io_usage.png"
            
            plt.tight_layout()
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Graphique I/O généré: {output_file}")
            logger.info(f"  I/O moyen: {mean_io:.1f}%, I/O max: {max_io:.1f}%")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du graphique I/O: {str(e)}")
            return False


if __name__ == "__main__":
    # Test
    reporter = QoSReporter()
