"""
Station TV - System Logger
Configuration centralisée du système de logging
"""

import logging
import os
from datetime import datetime
from pathlib import Path


def setup_logger(name: str, log_file: str = None, level: str = "INFO") -> logging.Logger:
    """
    Configure et retourne un logger avec formatage standardisé.
    
    Args:
        name: Nom du logger
        log_file: Chemin du fichier de log (optionnel)
        level: Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Logger configuré
    """
    logger = logging.getLogger(name)
    
    # Convertir le niveau en constante logging
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # Éviter les handlers dupliqués
    if logger.handlers:
        return logger
    
    # Format des logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler fichier (si spécifié)
    if log_file:
        # Créer le répertoire si nécessaire
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Récupère un logger existant.
    
    Args:
        name: Nom du logger
    
    Returns:
        Logger
    """
    return logging.getLogger(name)
