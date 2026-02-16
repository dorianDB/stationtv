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
        self.io_thread: Optional[threading.Thread] = None
        
        self.cpu_file = self.output_dir / "monitoring_cpu.csv"
        self.memory_file = self.output_dir / "monitoring_memory.csv"
        self.io_file = self.output_dir / "monitoring_io.csv"
        
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
    
    def monitor_io_usage(self):
        """
        Enregistre l'utilisation des I/O disque dans un fichier CSV.
        Mesure le pourcentage d'occupation disque et les débits lecture/écriture.
        """
        # Créer le fichier avec en-têtes
        with open(self.io_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Timestamp", "IO_Usage_Percent", "Read_MB_s", "Write_MB_s", "Read_Count", "Write_Count"])
        
        logger.info(f"Monitoring I/O démarré → {self.io_file}")
        
        # Snapshot initial
        prev_counters = psutil.disk_io_counters()
        prev_time = time.time()
        
        # Attendre le premier intervalle
        time.sleep(self.interval)
        
        while self.monitoring_active:
            try:
                current_counters = psutil.disk_io_counters()
                current_time = time.time()
                elapsed = current_time - prev_time
                
                if elapsed > 0 and current_counters and prev_counters:
                    # Débits en MB/s
                    read_mb_s = (current_counters.read_bytes - prev_counters.read_bytes) / (1024**2) / elapsed
                    write_mb_s = (current_counters.write_bytes - prev_counters.write_bytes) / (1024**2) / elapsed
                    
                    # Nombre d'opérations par seconde
                    read_count = (current_counters.read_count - prev_counters.read_count) / elapsed
                    write_count = (current_counters.write_count - prev_counters.write_count) / elapsed
                    
                    # Pourcentage d'occupation I/O (busy_time en ms)
                    if hasattr(current_counters, 'busy_time') and hasattr(prev_counters, 'busy_time'):
                        busy_ms = current_counters.busy_time - prev_counters.busy_time
                        io_percent = min(100.0, (busy_ms / (elapsed * 1000)) * 100)
                    else:
                        # Estimation basée sur le débit (approximation)
                        # Hypothèse: SSD ~500 MB/s max
                        total_mb_s = read_mb_s + write_mb_s
                        io_percent = min(100.0, (total_mb_s / 500.0) * 100)
                    
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    
                    with open(self.io_file, 'a', newline='', encoding='utf-8') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow([
                            timestamp,
                            f"{io_percent:.2f}",
                            f"{read_mb_s:.2f}",
                            f"{write_mb_s:.2f}",
                            f"{read_count:.0f}",
                            f"{write_count:.0f}"
                        ])
                
                prev_counters = current_counters
                prev_time = current_time
                
                time.sleep(self.interval)
                
            except Exception as e:
                logger.error(f"Erreur monitoring I/O: {str(e)}")
                break
        
        logger.info("Monitoring I/O arrêté")
    
    def start(self):
        """Démarre le monitoring CPU, RAM et I/O."""
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
        
        # Démarrer le thread I/O
        self.io_thread = threading.Thread(target=self.monitor_io_usage, daemon=True)
        self.io_thread.start()
        
        logger.info("Monitoring système démarré (CPU + RAM + I/O)")
    
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
        
        if self.io_thread and self.io_thread.is_alive():
            self.io_thread.join(timeout=timeout)
        
        logger.info("Monitoring système arrêté")
    
    def get_current_stats(self) -> dict:
        """
        Retourne les statistiques système actuelles.
        
        Returns:
            Dictionnaire avec CPU et RAM
        """
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        io = psutil.disk_io_counters()
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_gb": memory.used / (1024**3),
            "memory_total_gb": memory.total / (1024**3),
            "memory_available_gb": memory.available / (1024**3),
            "io_read_bytes": io.read_bytes if io else 0,
            "io_write_bytes": io.write_bytes if io else 0
        }
    
    def __enter__(self):
        """Support du context manager."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Support du context manager."""
        self.stop()
