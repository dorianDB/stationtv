"""
Station TV - Model Manager
Gestion des modèles Whisper (chargement, cache, validation)
"""

import whisper
import torch
from typing import Optional, Dict
from utils.logger import get_logger

logger = get_logger(__name__)


class ModelManager:
    """
    Gestionnaire centralisé des modèles Whisper.
    """
    
    # Spécifications des modèles (RAM estimée en Go)
    MODEL_SPECS = {
        "tiny": {"ram_gb": 1, "suffix": "wt"},
        "base": {"ram_gb": 1, "suffix": "wb"},
        "small": {"ram_gb": 2, "suffix": "ws"},
        "medium": {"ram_gb": 5, "suffix": "wm"},
        "large": {"ram_gb": 10, "suffix": "wl"},
        "large-v2": {"ram_gb": 10, "suffix": "wl2"},
        "large-v3": {"ram_gb": 10, "suffix": "wl3"},
    }
    
    def __init__(self, device: str = "cpu"):
        """
        Initialise le gestionnaire de modèles.
        
        Args:
            device: Device à utiliser ('cpu' ou 'cuda')
        """
        self.device = device
        self.device = device
        # self._loaded_models removed to prevent caching
        
        logger.info(f"ModelManager initialisé avec device={device}")
    
    def load_model(self, model_name: str, force_reload: bool = False) -> Optional[whisper.Whisper]:
        """
        Charge un modèle Whisper en mémoire.
        
        Args:
            model_name: Nom du modèle (tiny, base, small, medium, large)
            force_reload: Ignoré (plus de cache)
        
        Returns:
            Modèle Whisper chargé ou None en cas d'erreur
        """
        # Valider le nom du modèle
        if model_name not in self.MODEL_SPECS:
            logger.error(f"Modèle inconnu: {model_name}. Modèles disponibles: {list(self.MODEL_SPECS.keys())}")
            return None
        
        try:
            logger.info(f"Chargement du modèle {model_name} sur {self.device}...")
            model = whisper.load_model(model_name, device=self.device)
            
            logger.info(f"Modèle {model_name} chargé avec succès")
            return model
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle {model_name}: {str(e)}")
            return None
    
    def unload_model(self, model: Optional[whisper.Whisper]) -> bool:
        """
        Décharge un modèle de la mémoire.
        
        Args:
            model: Instance du modèle à décharger
        
        Returns:
            True si succès
        """
        if model:
            del model
            import gc
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            logger.info(f"Modèle déchargé et garbage collector appelé")
            return True
        return False

    def unload_all(self):
        """Décharge tous les modèles de la mémoire (Obsolète avec la nouvelle gestion)."""
        import gc
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("Nettoyage mémoire forcé")
    
    def get_model_suffix(self, model_name: str) -> str:
        """
        Retourne le suffixe de fichier pour un modèle donné.
        
        Args:
            model_name: Nom du modèle
        
        Returns:
            Suffixe (ex: 'wt' pour tiny, 'ws' pour small)
        """
        return self.MODEL_SPECS.get(model_name, {}).get("suffix", "w")
    
    def estimate_ram_usage(self, model_name: str, num_processes: int = 1) -> float:
        """
        Estime l'utilisation RAM totale pour un nombre de processus donné.
        
        Args:
            model_name: Nom du modèle
            num_processes: Nombre de processus simultanés
        
        Returns:
            RAM estimée en Go
        """
        base_ram = self.MODEL_SPECS.get(model_name, {}).get("ram_gb", 0)
        # Ajouter une marge de sécurité de 50%
        estimated_ram = base_ram * num_processes * 1.5
        
        logger.info(
            f"RAM estimée pour {num_processes} processus {model_name}: "
            f"{estimated_ram:.1f} Go"
        )
        
        return estimated_ram
    
    def validate_memory_availability(
        self, 
        model_name: str, 
        num_processes: int, 
        total_ram_gb: float,
        max_usage_percent: float = 90.0
    ) -> bool:
        """
        Vérifie si la RAM disponible est suffisante.
        
        Args:
            model_name: Nom du modèle
            num_processes: Nombre de processus simultanés
            total_ram_gb: RAM totale disponible (Go)
            max_usage_percent: Pourcentage maximal d'utilisation autorisé
        
        Returns:
            True si la mémoire est suffisante, False sinon
        """
        estimated_ram = self.estimate_ram_usage(model_name, num_processes)
        max_allowed_ram = total_ram_gb * (max_usage_percent / 100.0)
        
        is_valid = estimated_ram <= max_allowed_ram
        
        if is_valid:
            logger.info(
                f"✓ Mémoire suffisante: {estimated_ram:.1f} Go / "
                f"{max_allowed_ram:.1f} Go disponibles"
            )
        else:
            logger.warning(
                f"✗ Mémoire insuffisante: {estimated_ram:.1f} Go requis > "
                f"{max_allowed_ram:.1f} Go disponibles"
            )
            logger.warning(
                f"Réduire le nombre de processus ou choisir un modèle plus petit"
            )
        
        return is_valid
    
    @staticmethod
    def list_available_models() -> list:
        """
        Retourne la liste des modèles disponibles.
        
        Returns:
            Liste des noms de modèles
        """
        return list(ModelManager.MODEL_SPECS.keys())
