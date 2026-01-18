"""
Station TV - File Handler
Utilitaires pour la gestion des fichiers audio et métadonnées
Adapté du code WhisperTranscriptor.py existant
"""

import os
import csv
import mutagen
from pathlib import Path
from typing import List, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class FichierAudio:
    """
    Représente un fichier audio avec ses métadonnées.
    Réutilisé depuis WhisperTranscriptor.py
    """
    
    def __init__(self, chemin: str):
        self.chemin = chemin
        self.longueur = self.extraire_duree()
    
    def extraire_duree(self) -> float:
        """Extrait la durée en secondes du fichier audio"""
        try:
            audio = mutagen.File(self.chemin)
            if audio is not None and hasattr(audio, 'info') and hasattr(audio.info, 'length'):
                return audio.info.length
            return 0
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction de la durée pour {self.chemin}: {str(e)}")
            return 0
    
    def __str__(self):
        return f"{self.chemin} (durée: {self.longueur:.2f}s)"
    
    def __repr__(self):
        return f"FichierAudio('{self.chemin}', {self.longueur:.2f}s)"


class FileHandler:
    """
    Gestionnaire de fichiers pour le projet Station TV.
    """
    
    @staticmethod
    def lister_fichiers(chemin: str, suffixes: Optional[List[str]] = None) -> List[FichierAudio]:
        """
        Crée et retourne une liste d'objets FichierAudio pour chaque fichier 
        se terminant par les suffixes spécifiés.
        
        Exploration récursive de tous les sous-répertoires.
        Réutilisé depuis WhisperTranscriptor.py
        
        Args:
            chemin: Répertoire racine à explorer
            suffixes: Liste des extensions à rechercher (ex: ['.mp3', '.wav'])
        
        Returns:
            Liste d'objets FichierAudio
        """
        if suffixes is None:
            suffixes = ['.mp3']
        
        objets_fichiers = []
        
        # Vérifier si le chemin existe
        if not os.path.exists(chemin):
            logger.error(f"Le répertoire {chemin} n'existe pas.")
            return objets_fichiers
        
        # Créer une pile pour stocker les répertoires à explorer
        repertoires_a_explorer = [chemin]
        
        # Tant qu'il reste des répertoires à explorer
        while repertoires_a_explorer:
            repertoire_courant = repertoires_a_explorer.pop()
            
            try:
                contenu = os.listdir(repertoire_courant)
                
                for element in contenu:
                    chemin_element = os.path.join(repertoire_courant, element)
                    
                    # Si c'est un fichier et qu'il se termine par un des suffixes
                    if os.path.isfile(chemin_element) and any(
                        chemin_element.lower().endswith(ext.lower()) for ext in suffixes
                    ):
                        nouvel_objet = FichierAudio(chemin_element)
                        
                        # Filtrer les fichiers sans audio (durée = 0)
                        # Cela arrive avec les fichiers vidéo qui n'ont pas de piste audio
                        if nouvel_objet.longueur <= 0:
                            logger.warning(
                                f"Fichier ignoré (pas de piste audio détectable): "
                                f"{os.path.basename(chemin_element)}"
                            )
                            continue
                        
                        objets_fichiers.append(nouvel_objet)
                        logger.debug(f"Fichier trouvé: {nouvel_objet}")
                    
                    # Si c'est un répertoire, l'ajouter à la pile
                    elif os.path.isdir(chemin_element):
                        repertoires_a_explorer.append(chemin_element)
                        
            except PermissionError:
                logger.warning(f"Pas de permission pour accéder à {repertoire_courant}")
            except Exception as e:
                logger.error(f"Erreur lors de l'accès à {repertoire_courant}: {str(e)}")
        
        logger.info(f"{len(objets_fichiers)} fichiers trouvés dans {chemin}")
        return objets_fichiers
    
    @staticmethod
    def ecrire_csv(objets: List[FichierAudio], nom_fichier: str) -> bool:
        """
        Écrit les informations des objets dans un fichier CSV.
        Réutilisé depuis WhisperTranscriptor.py
        
        Args:
            objets: Liste d'objets FichierAudio
            nom_fichier: Nom du fichier CSV à créer
        
        Returns:
            True si succès, False sinon
        """
        try:
            # Créer le répertoire parent si nécessaire
            Path(nom_fichier).parent.mkdir(parents=True, exist_ok=True)
            
            with open(nom_fichier, 'w', newline='', encoding='utf-8') as fichier_csv:
                writer = csv.writer(fichier_csv)
                # En-tête
                writer.writerow(['Chemin', 'Duree(s)'])
                # Données
                for obj in objets:
                    writer.writerow([obj.chemin, obj.longueur])
            
            logger.info(f"Les données ont été écrites dans {nom_fichier}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'écriture du fichier CSV: {str(e)}")
            return False
    
    @staticmethod
    def lire_csv(nom_fichier: str) -> List[tuple]:
        """
        Lit un fichier CSV et retourne les données.
        
        Args:
            nom_fichier: Nom du fichier CSV à lire
        
        Returns:
            Liste de tuples (chemin, durée)
        """
        try:
            donnees = []
            with open(nom_fichier, 'r', encoding='utf-8') as fichier:
                lecteur = csv.reader(fichier)
                next(lecteur)  # Skip header
                for ligne in lecteur:
                    if len(ligne) >= 2:
                        donnees.append((ligne[0], float(ligne[1])))
            
            logger.info(f"{len(donnees)} entrées lues depuis {nom_fichier}")
            return donnees
            
        except Exception as e:
            logger.error(f"Erreur lors de la lecture du fichier CSV: {str(e)}")
            return []
