"""
Station TV - CPU Affinity Manager
Gestion de l'affinité CPU et répartition des tâches.
Adapté du code WhisperTranscriptor.py existant
"""

import os
import psutil
from typing import List
from utils.logger import get_logger

logger = get_logger(__name__)


class Audio:
    """
    Représente un fichier audio à traiter.
    Réutilisé depuis WhisperTranscriptor.py
    """
    
    def __init__(self, path: str, duree: float):
        self.path = path
        self.duree = duree
    
    def __repr__(self):
        return f"Audio('{self.path}', {self.duree:.2f}s)"


class CPUAffinityManager:
    """
    Gestionnaire d'affinité CPU pour optimiser la répartition des processus.
    """
    
    @staticmethod
    def set_cpu_affinity(cpu_list: List[int]) -> bool:
        """
        Définit l'affinité CPU du processus actuel aux cœurs spécifiés.
        Réutilisé depuis WhisperTranscriptor.py
        
        Args:
            cpu_list: Liste des IDs de cœurs CPU à utiliser
        
        Returns:
            True si succès, False sinon
        """
        try:
            p = psutil.Process(os.getpid())
            p.cpu_affinity(cpu_list)
            logger.info(f"Affinité CPU définie sur les cœurs: {cpu_list}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la définition de l'affinité CPU: {str(e)}")
            return False
    
    @staticmethod
    def get_cpu_affinity() -> List[int]:
        """
        Récupère l'affinité CPU du processus actuel.
        
        Returns:
            Liste des IDs de cœurs CPU utilisés
        """
        try:
            p = psutil.Process(os.getpid())
            return p.cpu_affinity()
        except Exception as e:
            logger.error(f"Erreur lors de la lecture de l'affinité CPU: {str(e)}")
            return []
    
    @staticmethod
    def glouton_n_listes(objets: List[Audio], n: int) -> List[List[Audio]]:
        """
        Algorithme glouton pour répartir n objets dans n listes de manière équilibrée.
        Place chaque objet dans la liste avec la plus petite somme actuelle.
        
        Réutilisé depuis WhisperTranscriptor.py
        
        Args:
            objets: Liste d'objets Audio à répartir
            n: Nombre de listes (processus) à créer
        
        Returns:
            Liste de n listes d'objets Audio
        """
        if not objets or n <= 0:
            logger.warning(f"Répartition impossible: {len(objets)} objets, {n} listes")
            return [[] for _ in range(n)]
        
        # Trier par durée décroissante
        objets_tries = sorted(objets, key=lambda x: x.duree, reverse=True)
        
        # Initialiser n listes vides avec leurs sommes
        listes = [[] for _ in range(n)]
        sommes = [0] * n
        
        # Répartir chaque objet dans la liste avec la plus petite somme
        for objet in objets_tries:
            # Trouver l'index de la liste avec la somme minimale
            index_min = sommes.index(min(sommes))
            
            # Ajouter l'objet à cette liste
            listes[index_min].append(objet)
            sommes[index_min] += objet.duree
        
        # Log des statistiques de répartition
        for i, (liste, somme) in enumerate(zip(listes, sommes)):
            logger.info(
                f"Liste {i+1}: {len(liste)} fichiers, "
                f"durée totale: {somme:.2f}s ({somme/3600:.2f}h)"
            )
        
        return listes
    
    @staticmethod
    def equilibrage_charge(objets: List[Audio], nb_processus: int) -> List[List[Audio]]:
        """
        Équilibre la charge entre les processus disponibles.
        Alias pour glouton_n_listes avec logging amélioré.
        
        Args:
            objets: Liste d'objets Audio à répartir
            nb_processus: Nombre de processus disponibles
        
        Returns:
            Liste de listes d'objets Audio répartis équitablement
        """
        logger.info(f"Équilibrage de {len(objets)} fichiers sur {nb_processus} processus")
        
        duree_totale = sum(obj.duree for obj in objets)
        logger.info(f"Durée totale à traiter: {duree_totale:.2f}s ({duree_totale/3600:.2f}h)")
        
        listes = CPUAffinityManager.glouton_n_listes(objets, nb_processus)
        
        # Calculer l'écart-type pour vérifier l'équilibre
        sommes = [sum(obj.duree for obj in liste) for liste in listes]
        moyenne = sum(sommes) / len(sommes) if sommes else 0
        variance = sum((s - moyenne) ** 2 for s in sommes) / len(sommes) if sommes else 0
        ecart_type = variance ** 0.5
        
        logger.info(
            f"Répartition effectuée - Moyenne: {moyenne:.2f}s, "
            f"Écart-type: {ecart_type:.2f}s"
        )
        
        return listes
