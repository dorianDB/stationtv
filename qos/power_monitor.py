"""
Station TV - Power Consumption Monitor
Monitoring de la consommation énergétique du système
"""

import time
import platform
import csv
from pathlib import Path
from datetime import datetime
from typing import Optional
import psutil

try:
    import pyRAPL
    RAPL_AVAILABLE = True
except ImportError:
    RAPL_AVAILABLE = False

from utils.logger import get_logger

logger = get_logger(__name__)


class PowerMonitor:
    """
    Moniteur de consommation énergétique.
    
    Utilise RAPL (Intel) si disponible, sinon estimation basée sur CPU.
    """
    
    def __init__(
        self,
        output_dir: str = "output/reports",
        interval: int = 30,
        tdp_watts: Optional[int] = None,
        electricity_cost_per_kwh: float = 0.18,  # €/kWh (moyenne France)
        carbon_intensity: float = 0.1  # kg CO2/kWh (moyenne France)
    ):
        """
        Initialise le moniteur de consommation.
        
        Args:
            output_dir: Répertoire de sortie pour les fichiers CSV
            interval: Intervalle entre mesures (secondes)
            tdp_watts: TDP du processeur (pour estimation si RAPL indisponible)
            electricity_cost_per_kwh: Coût électricité en €/kWh
            carbon_intensity: Intensité carbone en kg CO2/kWh
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.interval = interval
        self.tdp_watts = tdp_watts or self._detect_tdp()
        self.electricity_cost = electricity_cost_per_kwh
        self.carbon_intensity = carbon_intensity
        
        self.monitoring = False
        self.cumulative_kwh = 0.0
        self.start_time = None
        
        # Détection méthode de mesure
        self.use_rapl = RAPL_AVAILABLE and platform.system() == "Linux"
        
        if self.use_rapl:
            logger.info("RAPL disponible - Mesure précise de la consommation")
            try:
                pyRAPL.setup()
            except Exception as e:
                logger.warning(f"RAPL setup échoué, utilisation estimation: {e}")
                self.use_rapl = False
        else:
            logger.info(f"RAPL indisponible - Estimation basée TDP ({self.tdp_watts}W)")
        
        # Fichier CSV
        self.csv_file = self.output_dir / "monitoring_power.csv"
        
        logger.info(
            f"PowerMonitor initialisé: "
            f"intervalle={interval}s, TDP={self.tdp_watts}W, "
            f"coût={electricity_cost_per_kwh}€/kWh"
        )
    
    def _detect_tdp(self) -> int:
        """
        Détecte le TDP du processeur (estimation).
        
        Returns:
            TDP estimé en Watts
        """
        # Détection basique basée sur le nombre de cœurs
        cpu_count = psutil.cpu_count(logical=False) or 4
        
        # TDP approximatif par cœur (conservateur)
        tdp_per_core = {
            (1, 2): 15,      # Mobile/Low power
            (3, 4): 35,      # Desktop entry
            (5, 8): 65,      # Desktop mainstream
            (9, 12): 95,     # Desktop high-end
            (13, 18): 125,   # Workstation (Xeon W-2295)
            (19, 32): 165,   # Server/HEDT
        }
        
        for (min_cores, max_cores), tdp in tdp_per_core.items():
            if min_cores <= cpu_count <= max_cores:
                logger.info(f"TDP estimé: {tdp}W pour {cpu_count} cœurs")
                return tdp
        
        # Fallback
        return 95
    
    def _measure_rapl(self) -> float:
        """
        Mesure la consommation via RAPL (Intel).
        
        Returns:
            Puissance instantanée en Watts
        """
        try:
            # Lecture des compteurs RAPL
            meter = pyRAPL.Measurement('power_measurement')
            meter.begin()
            time.sleep(1)  # Mesure sur 1 seconde
            meter.end()
            
            # Puissance en microjoules, conversion en Watts
            energy_uj = meter.result.pkg[0]  # Package energy
            watts = energy_uj / 1_000_000  # µJ -> W
            
            return watts
        except Exception as e:
            logger.error(f"Erreur mesure RAPL: {e}")
            return self._estimate_power()
    
    def _estimate_power(self) -> float:
        """
        Estime la consommation basée sur l'utilisation CPU.
        
        Returns:
            Puissance estimée en Watts
        """
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Formule: Puissance = TDP × (Utilisation_CPU / 100)
        # + Puissance de base (idle ~10-20% du TDP)
        idle_power = self.tdp_watts * 0.15
        active_power = self.tdp_watts * (cpu_percent / 100)
        
        total_power = idle_power + active_power
        
        return total_power
    
    def get_current_power(self) -> float:
        """
        Obtient la puissance instantanée.
        
        Returns:
            Puissance en Watts
        """
        if self.use_rapl:
            return self._measure_rapl()
        else:
            return self._estimate_power()
    
    def start(self):
        """Démarre le monitoring continu."""
        if self.monitoring:
            logger.warning("Monitoring déjà actif")
            return
        
        self.monitoring = True
        self.start_time = time.time()
        self.cumulative_kwh = 0.0
        
        # Créer le fichier CSV
        with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Timestamp',
                'Power_W',
                'Energy_kWh',
                'Cost_EUR',
                'Carbon_kgCO2'
            ])
        
        logger.info(f"Monitoring énergétique démarré → {self.csv_file}")
        
        # Thread de monitoring
        import threading
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def _monitor_loop(self):
        """Boucle de monitoring continue."""
        while self.monitoring:
            try:
                # Mesure puissance
                power_w = self.get_current_power()
                
                # Calcul énergie (kWh)
                # Énergie = Puissance × Temps
                energy_interval_kwh = (power_w / 1000) * (self.interval / 3600)
                self.cumulative_kwh += energy_interval_kwh
                
                # Calcul coût
                cost_eur = self.cumulative_kwh * self.electricity_cost
                
                # Calcul impact carbone
                carbon_kg = self.cumulative_kwh * self.carbon_intensity
                
                # Timestamp
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Écrire dans CSV
                with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        timestamp,
                        f"{power_w:.2f}",
                        f"{self.cumulative_kwh:.6f}",
                        f"{cost_eur:.4f}",
                        f"{carbon_kg:.4f}"
                    ])
                
                # Log périodique (toutes les 10 mesures)
                if self.cumulative_kwh > 0 and int(self.cumulative_kwh * 1000) % 10 == 0:
                    logger.info(
                        f"⚡ Consommation: {power_w:.1f}W | "
                        f"Total: {self.cumulative_kwh:.3f} kWh | "
                        f"Coût: {cost_eur:.2f}€"
                    )
                
                time.sleep(self.interval)
                
            except Exception as e:
                logger.error(f"Erreur monitoring: {e}")
                time.sleep(self.interval)
    
    def stop(self) -> dict:
        """
        Arrête le monitoring et retourne le résumé.
        
        Returns:
            Dictionnaire avec statistiques énergétiques
        """
        if not self.monitoring:
            return {}
        
        self.monitoring = False
        duration_hours = (time.time() - self.start_time) / 3600
        
        # Puissance moyenne
        avg_power = (self.cumulative_kwh / duration_hours) * 1000 if duration_hours > 0 else 0
        
        summary = {
            'duration_hours': duration_hours,
            'energy_kwh': self.cumulative_kwh,
            'average_power_w': avg_power,
            'cost_eur': self.cumulative_kwh * self.electricity_cost,
            'carbon_kg': self.cumulative_kwh * self.carbon_intensity,
            'electricity_cost_per_kwh': self.electricity_cost,
            'carbon_intensity': self.carbon_intensity
        }
        
        logger.info("=" * 60)
        logger.info("BILAN ÉNERGÉTIQUE")
        logger.info("=" * 60)
        logger.info(f"Durée session    : {duration_hours:.2f} heures")
        logger.info(f"Énergie totale   : {self.cumulative_kwh:.3f} kWh")
        logger.info(f"Puissance moyenne: {avg_power:.1f} W")
        logger.info(f"Coût électricité : {summary['cost_eur']:.2f} €")
        logger.info(f"Impact carbone   : {summary['carbon_kg']:.2f} kg CO2")
        logger.info("=" * 60)
        
        return summary
    
    def get_summary(self) -> dict:
        """
        Obtient les statistiques actuelles sans arrêter.
        
        Returns:
            Dictionnaire avec statistiques
        """
        if not self.start_time:
            return {}
        
        duration_hours = (time.time() - self.start_time) / 3600
        avg_power = (self.cumulative_kwh / duration_hours) * 1000 if duration_hours > 0 else 0
        
        return {
            'duration_hours': duration_hours,
            'energy_kwh': self.cumulative_kwh,
            'average_power_w': avg_power,
            'cost_eur': self.cumulative_kwh * self.electricity_cost,
            'carbon_kg': self.cumulative_kwh * self.carbon_intensity
        }
