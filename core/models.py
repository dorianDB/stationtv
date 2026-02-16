"""
Station TV - Model Manager
Gestion des modèles Whisper (chargement, cache, validation)
Utilise faster-whisper (CTranslate2) pour des performances optimales.
"""

from faster_whisper import WhisperModel
from typing import Optional, Dict
from utils.logger import get_logger

logger = get_logger(__name__)


class ModelManager:
    """
    Gestionnaire centralisé des modèles Whisper.
    Utilise faster-whisper (CTranslate2) au lieu de openai-whisper (PyTorch)
    pour réduire la consommation RAM et améliorer le throughput.
    """
    
    # Spécifications des modèles (RAM estimée en Go avec CTranslate2 int8)
    MODEL_SPECS = {
        "tiny": {"ram_gb": 0.5, "suffix": "wt"},
        "base": {"ram_gb": 0.5, "suffix": "wb"},
        "small": {"ram_gb": 1, "suffix": "ws"},
        "medium": {"ram_gb": 3, "suffix": "wm"},
        "large": {"ram_gb": 5, "suffix": "wl"},
        "large-v2": {"ram_gb": 5, "suffix": "wl2"},
        "large-v3": {"ram_gb": 5, "suffix": "wl3"},
    }
    
    def __init__(self, device: str = "cpu", compute_type: str = "int8"):
        """
        Initialise le gestionnaire de modèles.
        
        Args:
            device: Device à utiliser ('cpu' ou 'cuda')
            compute_type: Type de calcul CTranslate2 ('int8', 'float16', 'float32')
        """
        self.device = device
        self.compute_type = compute_type
        self._loaded_models: Dict[str, WhisperModel] = {}
        
        logger.info(f"ModelManager initialisé avec device={device}, compute_type={compute_type}")
    
    def load_model(self, model_name: str, force_reload: bool = False) -> Optional[WhisperModel]:
        """
        Charge un modèle Whisper en mémoire via faster-whisper.
        
        Args:
            model_name: Nom du modèle (tiny, base, small, medium, large)
            force_reload: Forcer le rechargement même si déjà en cache
        
        Returns:
            Modèle WhisperModel chargé ou None en cas d'erreur
        """
        # Vérifier si le modèle est déjà chargé
        if model_name in self._loaded_models and not force_reload:
            logger.info(f"Modèle {model_name} déjà chargé (cache)")
            return self._loaded_models[model_name]
        
        # Valider le nom du modèle
        if model_name not in self.MODEL_SPECS:
            logger.error(f"Modèle inconnu: {model_name}. Modèles disponibles: {list(self.MODEL_SPECS.keys())}")
            return None
        
        try:
            logger.info(f"Chargement du modèle {model_name} sur {self.device} (compute_type={self.compute_type})...")
            
            # faster-whisper: cpu_threads=0 = auto-détection
            model = WhisperModel(
                model_name,
                device=self.device,
                compute_type=self.compute_type,
                cpu_threads=0
            )
            
            # Mettre en cache
            self._loaded_models[model_name] = model
            
            logger.info(f"Modèle {model_name} chargé avec succès (faster-whisper/CTranslate2)")
            return model
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle {model_name}: {str(e)}")
            return None
    
    def unload_model(self, model_name: str) -> bool:
        """
        Décharge un modèle de la mémoire.
        
        Args:
            model_name: Nom du modèle à décharger
        
        Returns:
            True si succès, False sinon
        """
        if model_name in self._loaded_models:
            del self._loaded_models[model_name]
            logger.info(f"Modèle {model_name} déchargé")
            return True
        else:
            logger.warning(f"Modèle {model_name} non trouvé dans le cache")
            return False
    
    def unload_all(self):
        """Décharge tous les modèles de la mémoire."""
        model_names = list(self._loaded_models.keys())
        for name in model_names:
            self.unload_model(name)
        logger.info("Tous les modèles ont été déchargés")
    
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
        # Marge de sécurité de 50% (plus faible qu'avec PyTorch)
        estimated_ram = base_ram * num_processes * 1.5
        
        logger.info(
            f"RAM estimée pour {num_processes} processus {model_name}: "
            f"{estimated_ram:.1f} Go (faster-whisper/CTranslate2)"
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
