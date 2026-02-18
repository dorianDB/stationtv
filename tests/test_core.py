"""
Station TV - Tests
Tests unitaires pour les modules principaux
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import sys

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock des modules non installés localement (whisper/torch) pour permettre l'import
from unittest.mock import MagicMock

# Créer un mock torch qui ne casse pas scipy
_mock_torch = MagicMock()
_mock_torch.Tensor = type('Tensor', (), {})  # Classe réelle pour issubclass()
for mod in ['whisper', 'torch', 'torch.cuda']:
    if mod not in sys.modules:
        sys.modules[mod] = _mock_torch if 'torch' in mod else MagicMock()

from core.models import ModelManager
from core.affinity import CPUAffinityManager, Audio
from qos.metrics import MetricsCalculator
from utils.file_handler import FichierAudio


class TestModelManager(unittest.TestCase):
    """Tests pour ModelManager"""
    
    def setUp(self):
        self.manager = ModelManager(device="cpu")
    
    def test_model_specs_exist(self):
        """Vérifie que les spécifications des modèles sont définies"""
        self.assertIn("tiny", ModelManager.MODEL_SPECS)
        self.assertIn("small", ModelManager.MODEL_SPECS)
        self.assertIn("medium", ModelManager.MODEL_SPECS)
        self.assertIn("large", ModelManager.MODEL_SPECS)
    
    def test_get_model_suffix(self):
        """Vérifie la récupération du suffixe de modèle"""
        self.assertEqual(self.manager.get_model_suffix("tiny"), "wt")
        self.assertEqual(self.manager.get_model_suffix("small"), "ws")
        self.assertEqual(self.manager.get_model_suffix("medium"), "wm")
    
    def test_estimate_ram_usage(self):
        """Vérifie l'estimation de RAM"""
        ram = self.manager.estimate_ram_usage("small", num_processes=2)
        self.assertGreater(ram, 0)
        # Pour small: 2 Go * 2 processus * 1.5 marge = 6 Go
        self.assertEqual(ram, 6.0)
    
    def test_validate_memory_availability(self):
        """Vérifie la validation de mémoire disponible"""
        # Configuration faible en RAM (insuffisant)
        is_valid = self.manager.validate_memory_availability(
            "large", 
            num_processes=10, 
            total_ram_gb=64,
            max_usage_percent=90
        )
        self.assertFalse(is_valid)
        
        # Configuration avec beaucoup de RAM (suffisant)
        is_valid = self.manager.validate_memory_availability(
            "small", 
            num_processes=2, 
            total_ram_gb=256,
            max_usage_percent=90
        )
        self.assertTrue(is_valid)


class TestCPUAffinityManager(unittest.TestCase):
    """Tests pour CPUAffinityManager"""
    
    def test_glouton_n_listes_basic(self):
        """Vérifie l'algorithme glouton basique"""
        audios = [
            Audio("file1.mp3", 100),
            Audio("file2.mp3", 200),
            Audio("file3.mp3", 150)
        ]
        
        listes = CPUAffinityManager.glouton_n_listes(audios, 2)
        
        # Doit retourner 2 listes
        self.assertEqual(len(listes), 2)
        
        # Total des durées doit être préservé
        total_original = sum(a.duree for a in audios)
        total_reparti = sum(
            sum(a.duree for a in liste) for liste in listes
        )
        self.assertEqual(total_original, total_reparti)
    
    def test_glouton_n_listes_equilibrage(self):
        """Vérifie que l'équilibrage est correct"""
        audios = [
            Audio(f"file{i}.mp3", 100) for i in range(10)
        ]
        
        listes = CPUAffinityManager.glouton_n_listes(audios, 3)
        
        # Calculer les sommes
        sommes = [sum(a.duree for a in liste) for liste in listes]
        
        # Vérifier que les sommes sont relativement équilibrées
        # (écart max de ±100 acceptable pour 10 fichiers de 100s)
        moyenne = sum(sommes) / len(sommes)
        for somme in sommes:
            self.assertLess(abs(somme - moyenne), 150)
    
    def test_glouton_empty_list(self):
        """Vérifie le comportement avec liste vide"""
        listes = CPUAffinityManager.glouton_n_listes([], 3)
        self.assertEqual(len(listes), 3)
        for liste in listes:
            self.assertEqual(len(liste), 0)


class TestMetricsCalculator(unittest.TestCase):
    """Tests pour MetricsCalculator"""
    
    def setUp(self):
        self.calc = MetricsCalculator()
        self.calc.start_session()
    
    def test_calculate_throughput(self):
        """Vérifie le calcul du throughput"""
        # Ajouter des transcriptions fictives
        self.calc.add_transcription(
            audio_duration=3600,  # 1 heure audio
            processing_time=720,  # 12 minutes traitement
            file_path="test1.mp3",
            model="small",
            success=True
        )
        
        throughput = self.calc.calculate_throughput()
        # 3600 / 720 = 5× temps réel
        self.assertAlmostEqual(throughput, 5.0, places=1)
    
    def test_calculate_success_rate(self):
        """Vérifie le calcul du taux de réussite"""
        self.calc.add_transcription(100, 20, "f1.mp3", "small", True)
        self.calc.add_transcription(100, 20, "f2.mp3", "small", True)
        self.calc.add_transcription(100, 20, "f3.mp3", "small", False)
        
        success_rate = self.calc.calculate_success_rate()
        # 2/3 = 0.667
        self.assertAlmostEqual(success_rate, 2/3, places=2)
    
    def test_calculate_wer(self):
        """Vérifie le calcul du WER"""
        ref = "bonjour le monde"
        hyp = "bonjour le monde"
        
        # Texte identique: WER = 0
        wer = self.calc.calculate_wer(ref, hyp)
        self.assertEqual(wer, 0.0)
        
        # Texte complètement différent
        hyp2 = "hello world test"
        wer2 = self.calc.calculate_wer(ref, hyp2)
        self.assertGreater(wer2, 0.5)  # WER > 50%


class TestFichierAudio(unittest.TestCase):
    """Tests pour FichierAudio"""
    
    def test_creation_basic(self):
        """Vérifie la création basique d'un FichierAudio"""
        # Créer un fichier temporaire
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            fichier = FichierAudio(tmp_path)
            self.assertEqual(fichier.chemin, tmp_path)
            # La durée sera 0 car c'est un fichier vide
            self.assertGreaterEqual(fichier.longueur, 0)
        finally:
            Path(tmp_path).unlink(missing_ok=True)


def run_tests():
    """Exécute tous les tests"""
    # Créer la suite de tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Ajouter tous les tests
    suite.addTests(loader.loadTestsFromTestCase(TestModelManager))
    suite.addTests(loader.loadTestsFromTestCase(TestCPUAffinityManager))
    suite.addTests(loader.loadTestsFromTestCase(TestMetricsCalculator))
    suite.addTests(loader.loadTestsFromTestCase(TestFichierAudio))
    
    # Exécuter
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
