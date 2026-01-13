"""
Station TV - System Monitor
Surveillance en temps réel de l'utilisation CPU et RAM.
Adapté depuis WhisperTranscriptor.py avec améliorations.
"""

import time
import csv
import psutil
import threading
from pathlib import Path
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class SystemMonitor:
    """
    Moniteur système temps réel pour CPU et RAM.
    """
    
    def __init__(
        self, 
        output_dir: str = "output/reports",
        interval: int = 2,
        auto_start: bool = False
    ):
        """
        Initialise le moniteur système.
        
        Args:
            output_dir: Répertoire de sortie pour les fichiers CSV
            interval: Intervalle de surveillance en secondes
            auto_start: Démarrer automatiquement le monitoring
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.interval = interval
        self.monitoring_active = False
        
        self.cpu_thread: Optional[threading.Thread] = None
        self.memory_thread: Optional[threading.Thread] = None
        
        self.cpu_file = self.output_dir / "monitoring_cpu.csv"
        self.memory_file = self.output_dir / "monitoring_memory.csv"
        
        logger.info(f"SystemMonitor initialisé (intervalle={interval}s, output_dir={output_dir})")
        
        if auto_start:
            self.start()
    
    def monitor_cpu_usage(self):
        """
        Enregistre l'utilisation du CPU dans un fichier CSV.
        Réutilisé depuis WhisperTranscriptor.py avec améliorations.
        """
        # Créer le fichier avec en-têtes
        with open(self.cpu_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Timestamp", "CPU_Usage_Percent"])
        
        logger.info(f"Monitoring CPU démarré → {self.cpu_file}")
        
        while self.monitoring_active:
            try:
                # Mesure CPU (interval=1 pour psutil)
                cpu_percent = psutil.cpu_percent(interval=1)
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                
                # Écrire dans le CSV
                with open(self.cpu_file, 'a', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow([timestamp, f"{cpu_percent:.2f}"])
                
                # Attendre l'intervalle configuré
                time.sleep(self.interval)
                
            except Exception as e:
                logger.error(f"Erreur monitoring CPU: {str(e)}")
                break
        
        logger.info("Monitoring CPU arrêté")
    
    def monitor_memory_usage(self):
        """
        Enregistre l'utilisation de la RAM dans un fichier CSV.
        Réutilisé depuis WhisperTranscriptor.py avec améliorations.
        """
        # Créer le fichier avec en-têtes
        with open(self.memory_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Timestamp", "Memory_Usage_Percent", "Memory_Used_GB", "Memory_Total_GB"])
        
        logger.info(f"Monitoring RAM démarré → {self.memory_file}")
        
        while self.monitoring_active:
            try:
                # Mesure RAM
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                memory_used_gb = memory.used / (1024**3)  # Convertir en Go
                memory_total_gb = memory.total / (1024**3)
                
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                
                # Écrire dans le CSV
                with open(self.memory_file, 'a', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow([
                        timestamp, 
                        f"{memory_percent:.2f}",
                        f"{memory_used_gb:.2f}",
                        f"{memory_total_gb:.2f}"
                    ])
                
                # Alerte si usage élevé
                if memory_percent > 95:
                    logger.warning(f"⚠️ Utilisation RAM critique: {memory_percent:.1f}%")
                
                # Attendre l'intervalle configuré
                time.sleep(self.interval)
                
            except Exception as e:
                logger.error(f"Erreur monitoring RAM: {str(e)}")
                break
        
        logger.info("Monitoring RAM arrêté")
    
    def start(self):
        """Démarre le monitoring CPU et RAM."""
        if self.monitoring_active:
            logger.warning("Monitoring déjà actif")
            return
        
        self.monitoring_active = True
        
        # Démarrer le thread CPU
        self.cpu_thread = threading.Thread(target=self.monitor_cpu_usage, daemon=True)
        self.cpu_thread.start()
        
        # Démarrer le thread RAM
        self.memory_thread = threading.Thread(target=self.monitor_memory_usage, daemon=True)
        self.memory_thread.start()
        
        logger.info("Monitoring système démarré")
    
    def stop(self, timeout: int = 5):
        """
        Arrête le monitoring CPU et RAM.
        
        Args:
            timeout: Temps maximal d'attente pour la fin des threads (secondes)
        """
        if not self.monitoring_active:
            logger.warning("Monitoring déjà arrêté")
            return
        
        logger.info("Arrêt du monitoring système...")
        self.monitoring_active = False
        
        # Attendre la fin des threads
        if self.cpu_thread and self.cpu_thread.is_alive():
            self.cpu_thread.join(timeout=timeout)
        
        if self.memory_thread and self.memory_thread.is_alive():
            self.memory_thread.join(timeout=timeout)
        
        logger.info("Monitoring système arrêté")
    
    def get_current_stats(self) -> dict:
        """
        Retourne les statistiques système actuelles.
        
        Returns:
            Dictionnaire avec CPU et RAM
        """
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_gb": memory.used / (1024**3),
            "memory_total_gb": memory.total / (1024**3),
            "memory_available_gb": memory.available / (1024**3)
        }
    
    def __enter__(self):
        """Support du context manager."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Support du context manager."""
        self.stop()
