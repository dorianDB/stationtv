"""
Station TV - Tests complémentaires
Tests unitaires pour les modules non couverts par test_core.py :
  - TranscriptionExporter (export/)
  - AudioConverter (preprocessing/)
  - SystemMonitor (qos/)
  - PowerMonitor (qos/)
  - QoSReporter (qos/)
  - FileHandler complet (utils/)
  - WhisperTranscriber (core/) — avec mocks
"""

import unittest
import tempfile
import shutil
import csv
import json
import os
import time
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock
import sys

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock des modules non installés localement (whisper/torch) pour permettre l'import
_mock_torch = MagicMock()
_mock_torch.Tensor = type('Tensor', (), {})  # Classe réelle pour issubclass()
for mod in ['whisper', 'torch', 'torch.cuda']:
    if mod not in sys.modules:
        sys.modules[mod] = _mock_torch if 'torch' in mod else MagicMock()

from export.exporter import TranscriptionExporter
from preprocessing.audio_converter import AudioConverter
from qos.monitor import SystemMonitor
from qos.power_monitor import PowerMonitor
from qos.metrics import MetricsCalculator
from utils.file_handler import FileHandler, FichierAudio
from core.affinity import CPUAffinityManager, Audio


# ============================================================
# TranscriptionExporter
# ============================================================
class TestTranscriptionExporter(unittest.TestCase):
    """Tests pour TranscriptionExporter"""
    
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.exporter = TranscriptionExporter(output_dir=self.tmpdir)
        
        self.sample_transcription = {
            "text": "Bonjour, bienvenue sur Station TV.",
            "language": "fr",
            "duration": 5.0,
            "segments": [
                {"id": 0, "start": 0.0, "end": 2.5, "text": " Bonjour,"},
                {"id": 1, "start": 2.5, "end": 5.0, "text": " bienvenue sur Station TV."},
            ]
        }
    
    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_export_json_creates_file(self):
        """Vérifie que l'export JSON crée un fichier valide"""
        out = os.path.join(self.tmpdir, "test.json")
        result = self.exporter.export_to_json(self.sample_transcription, out)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(out))
        
        with open(out, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.assertEqual(data["version"], "1.0")
        self.assertEqual(data["transcription"]["text"], "Bonjour, bienvenue sur Station TV.")
        self.assertEqual(data["transcription"]["language"], "fr")
        self.assertEqual(len(data["segments"]), 2)
    
    def test_export_json_with_metadata(self):
        """Vérifie l'inclusion des métadonnées dans l'export JSON"""
        out = os.path.join(self.tmpdir, "meta.json")
        metadata = {"channel": "TF1", "date": "2026-02-16", "emission": "JT 20h"}
        
        result = self.exporter.export_to_json(self.sample_transcription, out, metadata=metadata)
        
        self.assertTrue(result)
        with open(out, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.assertEqual(data["metadata"]["channel"], "TF1")
        self.assertEqual(data["metadata"]["emission"], "JT 20h")
    
    def test_export_json_empty_segments(self):
        """Vérifie l'export JSON sans segments"""
        trans = {"text": "Test", "language": "fr", "duration": 1.0}
        out = os.path.join(self.tmpdir, "noseg.json")
        
        result = self.exporter.export_to_json(trans, out)
        
        self.assertTrue(result)
        with open(out, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.assertEqual(data["segments"], [])
    
    def test_export_csv_creates_file(self):
        """Vérifie que l'export CSV crée un fichier valide"""
        out = os.path.join(self.tmpdir, "test.csv")
        transcriptions = [
            {
                "file_path": "audio1.mp3",
                "text": "Texte un",
                "duration": 60.0,
                "segments": [{"id": 0}],
                "metadata": {"channel": "France2", "date": "2026-01-01", "time": "20:00", "emission": "JT"}
            },
            {
                "file_path": "audio2.mp3",
                "text": "Texte deux",
                "duration": 120.0,
                "segments": [{"id": 0}, {"id": 1}],
                "metadata": {"channel": "TF1", "date": "2026-01-02", "time": "13:00", "emission": "Info"}
            }
        ]
        
        result = self.exporter.export_to_csv(transcriptions, out)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(out))
        
        with open(out, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["file_path"], "audio1.mp3")
        self.assertEqual(rows[0]["segment_count"], "1")
        self.assertEqual(rows[1]["channel"], "TF1")
    
    def test_export_csv_without_metadata(self):
        """Vérifie l'export CSV sans métadonnées"""
        out = os.path.join(self.tmpdir, "nometadata.csv")
        transcriptions = [{"file_path": "a.mp3", "text": "txt", "duration": 10.0, "segments": []}]
        
        result = self.exporter.export_to_csv(transcriptions, out, include_metadata=False)
        
        self.assertTrue(result)
        with open(out, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertNotIn("channel", rows[0])
    
    def test_create_backup_nonexistent_source(self):
        """Vérifie le comportement avec un répertoire source inexistant"""
        result = self.exporter.create_backup("/nonexistent/path", self.tmpdir)
        self.assertFalse(result)
    
    def test_create_backup_copy(self):
        """Vérifie la création d'un backup par copie"""
        # Créer un répertoire source avec des fichiers
        src = os.path.join(self.tmpdir, "source")
        os.makedirs(src)
        with open(os.path.join(src, "test.txt"), 'w') as f:
            f.write("contenu test")
        
        backup_dir = os.path.join(self.tmpdir, "backups")
        result = self.exporter.create_backup(src, backup_dir, compression=False)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(backup_dir))
        # Vérifier qu'un sous-dossier a été créé
        contents = os.listdir(backup_dir)
        self.assertEqual(len(contents), 1)
        self.assertTrue(contents[0].startswith("transcriptions_backup_"))
    
    def test_create_backup_zip(self):
        """Vérifie la création d'un backup compressé"""
        src = os.path.join(self.tmpdir, "source_zip")
        os.makedirs(src)
        with open(os.path.join(src, "data.txt"), 'w') as f:
            f.write("données")
        
        backup_dir = os.path.join(self.tmpdir, "backups_zip")
        result = self.exporter.create_backup(src, backup_dir, compression=True)
        
        self.assertTrue(result)
        # Vérifier qu'un fichier .zip a été créé
        zip_files = [f for f in os.listdir(backup_dir) if f.endswith('.zip')]
        self.assertEqual(len(zip_files), 1)


# ============================================================
# AudioConverter (mocking FFmpeg)
# ============================================================
class TestAudioConverter(unittest.TestCase):
    """Tests pour AudioConverter"""
    
    def setUp(self):
        self.converter = AudioConverter(
            target_format="wav",
            sample_rate=48000,
            channels=1,
            bit_depth=16
        )
        self.tmpdir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_init_defaults(self):
        """Vérifie les paramètres par défaut"""
        self.assertEqual(self.converter.target_format, "wav")
        self.assertEqual(self.converter.sample_rate, 48000)
        self.assertEqual(self.converter.channels, 1)
        self.assertEqual(self.converter.bit_depth, 16)
    
    @patch('preprocessing.audio_converter.subprocess.run')
    def test_check_ffmpeg_available(self, mock_run):
        """Vérifie la détection de FFmpeg"""
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(self.converter.check_ffmpeg())
    
    @patch('preprocessing.audio_converter.subprocess.run')
    def test_check_ffmpeg_missing(self, mock_run):
        """Vérifie le comportement quand FFmpeg est absent"""
        mock_run.return_value = MagicMock(returncode=1)
        self.assertFalse(self.converter.check_ffmpeg())
    
    def test_convert_nonexistent_file(self):
        """Vérifie le comportement avec un fichier inexistant"""
        success, path = self.converter.convert_to_wav("/nonexistent/file.mp3")
        self.assertFalse(success)
        self.assertIsNone(path)
    
    def test_convert_existing_output_no_overwrite(self):
        """Vérifie qu'un fichier existant n'est pas écrasé sans overwrite"""
        # Créer un fichier source et un fichier de sortie existant
        src = os.path.join(self.tmpdir, "test.mp3")
        dst = os.path.join(self.tmpdir, "test.wav")
        Path(src).touch()
        Path(dst).touch()
        
        success, path = self.converter.convert_to_wav(src, dst, overwrite=False)
        self.assertFalse(success)
        self.assertEqual(path, dst)
    
    @patch('preprocessing.audio_converter.subprocess.run')
    def test_convert_to_wav_success(self, mock_run):
        """Vérifie la conversion réussie"""
        mock_run.return_value = MagicMock(returncode=0)
        
        src = os.path.join(self.tmpdir, "input.mp3")
        Path(src).touch()
        
        success, path = self.converter.convert_to_wav(src, overwrite=True)
        
        self.assertTrue(success)
        self.assertTrue(path.endswith(".wav"))
        mock_run.assert_called_once()
    
    @patch('preprocessing.audio_converter.subprocess.run')
    def test_convert_to_wav_failure(self, mock_run):
        """Vérifie le comportement en cas d'échec FFmpeg"""
        mock_run.return_value = MagicMock(returncode=1, stderr="Error")
        
        src = os.path.join(self.tmpdir, "bad.mp3")
        Path(src).touch()
        
        success, path = self.converter.convert_to_wav(src, overwrite=True)
        self.assertFalse(success)
    
    @patch('preprocessing.audio_converter.subprocess.run')
    def test_convert_batch(self, mock_run):
        """Vérifie la conversion batch"""
        mock_run.return_value = MagicMock(returncode=0)
        
        files = []
        for i in range(3):
            f = os.path.join(self.tmpdir, f"file{i}.mp3")
            Path(f).touch()
            files.append(f)
        
        results = self.converter.convert_batch(files, overwrite=True)
        
        self.assertEqual(results['total'], 3)
        self.assertEqual(results['success'], 3)
        self.assertEqual(results['failed'], 0)


# ============================================================
# SystemMonitor
# ============================================================
class TestSystemMonitor(unittest.TestCase):
    """Tests pour SystemMonitor"""
    
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_init_creates_output_dir(self):
        """Vérifie que le constructeur crée le répertoire de sortie"""
        out = os.path.join(self.tmpdir, "reports")
        monitor = SystemMonitor(output_dir=out, interval=2)
        
        self.assertTrue(os.path.exists(out))
        self.assertEqual(monitor.interval, 2)
        self.assertFalse(monitor.monitoring_active)
    
    def test_csv_file_paths(self):
        """Vérifie les chemins des fichiers CSV"""
        monitor = SystemMonitor(output_dir=self.tmpdir)
        
        self.assertTrue(str(monitor.cpu_file).endswith("monitoring_cpu.csv"))
        self.assertTrue(str(monitor.memory_file).endswith("monitoring_memory.csv"))
        self.assertTrue(str(monitor.io_file).endswith("monitoring_io.csv"))
    
    def test_start_stop(self):
        """Vérifie que start/stop fonctionne sans erreur"""
        monitor = SystemMonitor(output_dir=self.tmpdir, interval=1)
        
        monitor.start()
        self.assertTrue(monitor.monitoring_active)
        
        # Laisser un cycle de monitoring s'exécuter
        time.sleep(2)
        
        monitor.stop(timeout=3)
        self.assertFalse(monitor.monitoring_active)
        
        # Vérifier que les CSV ont été créés
        self.assertTrue(monitor.cpu_file.exists())
        self.assertTrue(monitor.memory_file.exists())
    
    def test_context_manager(self):
        """Vérifie le support du context manager"""
        with SystemMonitor(output_dir=self.tmpdir, interval=1) as monitor:
            self.assertTrue(monitor.monitoring_active)
            time.sleep(2)
        
        self.assertFalse(monitor.monitoring_active)
    
    def test_get_current_stats(self):
        """Vérifie que get_current_stats retourne les bonnes clés"""
        monitor = SystemMonitor(output_dir=self.tmpdir)
        stats = monitor.get_current_stats()
        
        self.assertIn("cpu_percent", stats)
        self.assertIn("memory_percent", stats)
        self.assertIn("memory_used_gb", stats)
        self.assertIn("memory_total_gb", stats)
        self.assertIn("memory_available_gb", stats)
        self.assertIn("io_read_bytes", stats)
        self.assertIn("io_write_bytes", stats)
        
        # Vérifier les types
        self.assertIsInstance(stats["cpu_percent"], float)
        self.assertGreater(stats["memory_total_gb"], 0)
    
    def test_double_start_ignored(self):
        """Vérifie que start() appelé deux fois ne crée pas de doublons"""
        monitor = SystemMonitor(output_dir=self.tmpdir, interval=1)
        monitor.start()
        monitor.start()  # Doit être ignoré
        
        self.assertTrue(monitor.monitoring_active)
        monitor.stop(timeout=3)
    
    def test_cpu_csv_content(self):
        """Vérifie le contenu du CSV CPU"""
        monitor = SystemMonitor(output_dir=self.tmpdir, interval=1)
        monitor.start()
        time.sleep(4)
        monitor.stop(timeout=3)
        
        # Lire le CSV
        with open(monitor.cpu_file, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        # Vérifier l'en-tête
        self.assertEqual(rows[0], ["Timestamp", "CPU_Usage_Percent"])
        # Au moins une ligne de données
        self.assertGreater(len(rows), 1)


# ============================================================
# PowerMonitor
# ============================================================
class TestPowerMonitor(unittest.TestCase):
    """Tests pour PowerMonitor"""
    
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_init_defaults(self):
        """Vérifie les paramètres par défaut"""
        pm = PowerMonitor(output_dir=self.tmpdir, interval=30)
        
        self.assertEqual(pm.interval, 30)
        self.assertEqual(pm.electricity_cost, 0.18)
        self.assertEqual(pm.carbon_intensity, 0.1)
        self.assertFalse(pm.monitoring)
        self.assertGreater(pm.tdp_watts, 0)
    
    def test_detect_tdp(self):
        """Vérifie que le TDP est détecté automatiquement"""
        pm = PowerMonitor(output_dir=self.tmpdir)
        tdp = pm._detect_tdp()
        
        self.assertIsInstance(tdp, int)
        self.assertGreater(tdp, 0)
        self.assertLessEqual(tdp, 165)
    
    def test_custom_tdp(self):
        """Vérifie l'injection d'un TDP personnalisé"""
        pm = PowerMonitor(output_dir=self.tmpdir, tdp_watts=125)
        self.assertEqual(pm.tdp_watts, 125)
    
    @patch('qos.power_monitor.psutil.cpu_percent', return_value=50.0)
    def test_estimate_power(self, mock_cpu):
        """Vérifie l'estimation de puissance"""
        pm = PowerMonitor(output_dir=self.tmpdir, tdp_watts=100)
        
        power = pm._estimate_power()
        
        # idle (15W) + active (100 * 50/100 = 50W) = 65W
        self.assertAlmostEqual(power, 65.0, places=0)
    
    @patch('qos.power_monitor.psutil.cpu_percent', return_value=0.0)
    def test_estimate_power_idle(self, mock_cpu):
        """Vérifie la puissance au repos"""
        pm = PowerMonitor(output_dir=self.tmpdir, tdp_watts=100)
        power = pm._estimate_power()
        
        # idle = 100 * 0.15 = 15W, active = 0
        self.assertAlmostEqual(power, 15.0, places=0)
    
    @patch('qos.power_monitor.psutil.cpu_percent', return_value=100.0)
    def test_estimate_power_full_load(self, mock_cpu):
        """Vérifie la puissance à pleine charge"""
        pm = PowerMonitor(output_dir=self.tmpdir, tdp_watts=100)
        power = pm._estimate_power()
        
        # idle (15W) + active (100W) = 115W
        self.assertAlmostEqual(power, 115.0, places=0)
    
    def test_stop_without_start(self):
        """Vérifie que stop() sans start() retourne un dict vide"""
        pm = PowerMonitor(output_dir=self.tmpdir)
        result = pm.stop()
        self.assertEqual(result, {})
    
    def test_get_summary_without_start(self):
        """Vérifie que get_summary() sans start() retourne un dict vide"""
        pm = PowerMonitor(output_dir=self.tmpdir)
        result = pm.get_summary()
        self.assertEqual(result, {})
    
    def test_csv_file_path(self):
        """Vérifie le chemin du fichier CSV"""
        pm = PowerMonitor(output_dir=self.tmpdir)
        self.assertTrue(str(pm.csv_file).endswith("monitoring_power.csv"))


# ============================================================
# QoSReporter (avec fichiers CSV temporaires)
# ============================================================
class TestQoSReporter(unittest.TestCase):
    """Tests pour QoSReporter"""
    
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # Importer ici pour éviter les erreurs de matplotlib en environnement headless
        try:
            import matplotlib
            matplotlib.use('Agg')  # Backend non-interactif
        except Exception:
            pass
        from qos.reporter import QoSReporter
        self.QoSReporter = QoSReporter
    
    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def _create_cpu_csv(self):
        """Crée un fichier CSV CPU de test"""
        path = os.path.join(self.tmpdir, "monitoring_cpu.csv")
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "CPU_Usage_Percent"])
            for i in range(10):
                writer.writerow([f"2026-02-16 14:{i:02d}:00", f"{50 + i * 3:.2f}"])
        return path
    
    def _create_memory_csv(self):
        """Crée un fichier CSV mémoire de test"""
        path = os.path.join(self.tmpdir, "monitoring_memory.csv")
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Memory_Usage_Percent", "Memory_Used_GB", "Memory_Total_GB"])
            for i in range(10):
                writer.writerow([f"2026-02-16 14:{i:02d}:00", f"{30 + i:.2f}", f"{76.8 + i:.2f}", "256.00"])
        return path
    
    def _create_io_csv(self):
        """Crée un fichier CSV I/O de test"""
        path = os.path.join(self.tmpdir, "monitoring_io.csv")
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "IO_Usage_Percent", "Read_MB_s", "Write_MB_s", "Read_Count", "Write_Count"])
            for i in range(10):
                writer.writerow([f"2026-02-16 14:{i:02d}:00", f"{10 + i:.2f}", f"{50.0:.2f}", f"{20.0:.2f}", "100", "50"])
        return path
    
    def test_plot_cpu_usage(self):
        """Vérifie la génération du graphique CPU"""
        reporter = self.QoSReporter(output_dir=self.tmpdir)
        csv_path = self._create_cpu_csv()
        
        result = reporter.plot_cpu_usage(csv_path)
        self.assertTrue(result)
        
        # Vérifier qu'un PNG a été généré
        png_file = os.path.join(self.tmpdir, "cpu_usage.png")
        self.assertTrue(os.path.exists(png_file))
    
    def test_plot_memory_usage(self):
        """Vérifie la génération du graphique RAM"""
        reporter = self.QoSReporter(output_dir=self.tmpdir)
        csv_path = self._create_memory_csv()
        
        result = reporter.plot_memory_usage(csv_path)
        self.assertTrue(result)
        
        png_file = os.path.join(self.tmpdir, "memory_usage.png")
        self.assertTrue(os.path.exists(png_file))
    
    def test_plot_io_usage(self):
        """Vérifie la génération du graphique I/O"""
        reporter = self.QoSReporter(output_dir=self.tmpdir)
        csv_path = self._create_io_csv()
        
        result = reporter.plot_io_usage(csv_path)
        self.assertTrue(result)
        
        png_file = os.path.join(self.tmpdir, "io_usage.png")
        self.assertTrue(os.path.exists(png_file))
    
    def test_generate_summary_report(self):
        """Vérifie la génération du rapport résumé"""
        reporter = self.QoSReporter(output_dir=self.tmpdir)
        
        metrics_summary = {
            "total_files": 24,
            "successful_files": 22,
            "failed_files": 2,
            "total_audio_duration_h": 24.0,
            "total_processing_time_h": 4.8,
            "throughput": 5.0,
            "success_rate": 0.917,
            "average_processing_time_s": 720.0,
            "session_duration_h": 5.0,
        }
        
        result = reporter.generate_summary_report(metrics_summary)
        self.assertTrue(result)


# ============================================================
# FileHandler (complet)
# ============================================================
class TestFileHandler(unittest.TestCase):
    """Tests complets pour FileHandler"""
    
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_lister_fichiers_empty_dir(self):
        """Vérifie le scan d'un répertoire vide"""
        fichiers = FileHandler.lister_fichiers(self.tmpdir, suffixes=['.mp3'])
        self.assertEqual(len(fichiers), 0)
    
    def test_lister_fichiers_nonexistent_dir(self):
        """Vérifie le comportement avec un répertoire inexistant"""
        fichiers = FileHandler.lister_fichiers("/nonexistent/path", suffixes=['.mp3'])
        self.assertEqual(len(fichiers), 0)
    
    def test_ecrire_et_lire_csv(self):
        """Vérifie l'écriture et la lecture de CSV"""
        csv_path = os.path.join(self.tmpdir, "inventory.csv")
        
        # Créer des objets FichierAudio mockés
        fichiers = []
        for i in range(3):
            fa = MagicMock()
            fa.chemin = f"/audio/file{i}.mp3"
            fa.longueur = 100.0 * (i + 1)
            fichiers.append(fa)
        
        # Écrire
        result = FileHandler.ecrire_csv(fichiers, csv_path)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(csv_path))
        
        # Lire
        data = FileHandler.lire_csv(csv_path)
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0][0], "/audio/file0.mp3")
        self.assertAlmostEqual(data[0][1], 100.0)
        self.assertEqual(data[2][0], "/audio/file2.mp3")
        self.assertAlmostEqual(data[2][1], 300.0)
    
    def test_lire_csv_nonexistent(self):
        """Vérifie la lecture d'un CSV inexistant"""
        data = FileHandler.lire_csv("/nonexistent/file.csv")
        self.assertEqual(data, [])
    
    def test_ecrire_csv_creates_parent_dirs(self):
        """Vérifie que les répertoires parents sont créés"""
        csv_path = os.path.join(self.tmpdir, "sub", "dir", "inventory.csv")
        
        fa = MagicMock()
        fa.chemin = "test.mp3"
        fa.longueur = 50.0
        
        result = FileHandler.ecrire_csv([fa], csv_path)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(csv_path))


# ============================================================
# WhisperTranscriber (mocking faster-whisper)
# ============================================================
class TestWhisperTranscriber(unittest.TestCase):
    """Tests pour WhisperTranscriber avec mocks"""
    
    def setUp(self):
        self.config = {
            'whisper': {
                'model': 'small',
                'language': 'fr',
                'device': 'cpu',
            },
            'paths': {
                'output_dir': tempfile.mkdtemp()
            }
        }
        self.tmpdir = self.config['paths']['output_dir']
    
    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    @patch('core.transcription.ModelManager')
    def test_init(self, MockModelManager):
        """Vérifie l'initialisation du transcriber"""
        from core.transcription import WhisperTranscriber
        
        transcriber = WhisperTranscriber(self.config)
        
        self.assertEqual(transcriber.model_name, 'small')
        self.assertEqual(transcriber.language, 'fr')
        MockModelManager.assert_called_once()
    
    @patch('core.transcription.ModelManager')
    def test_init_defaults(self, MockModelManager):
        """Vérifie les valeurs par défaut"""
        from core.transcription import WhisperTranscriber
        
        transcriber = WhisperTranscriber({})
        
        self.assertEqual(transcriber.model_name, 'small')
        self.assertEqual(transcriber.language, 'fr')


# ============================================================
# MetricsCalculator (tests complémentaires)
# ============================================================
class TestMetricsCalculatorExtended(unittest.TestCase):
    """Tests complémentaires pour MetricsCalculator"""
    
    def setUp(self):
        self.calc = MetricsCalculator()
        self.calc.start_session()
    
    def test_get_summary(self):
        """Vérifie le résumé complet des métriques"""
        self.calc.add_transcription(3600, 720, "f1.mp3", "small", True)
        self.calc.add_transcription(3600, 600, "f2.mp3", "small", True)
        self.calc.add_transcription(3600, 900, "f3.mp3", "small", False)
        self.calc.end_session()
        
        summary = self.calc.get_summary()
        
        self.assertIn("total_files", summary)
        self.assertIn("throughput", summary)
        self.assertIn("success_rate", summary)
        self.assertEqual(summary["total_files"], 3)
        self.assertAlmostEqual(summary["success_rate"], 2/3, places=2)
    
    def test_session_duration(self):
        """Vérifie le calcul de la durée de session"""
        time.sleep(0.1)
        self.calc.end_session()
        
        duration = self.calc.get_session_duration()
        self.assertGreater(duration, 0)
    
    def test_average_processing_time(self):
        """Vérifie le temps moyen de traitement"""
        self.calc.add_transcription(100, 10, "f1.mp3", "small", True)
        self.calc.add_transcription(100, 20, "f2.mp3", "small", True)
        self.calc.add_transcription(100, 30, "f3.mp3", "small", True)
        
        avg = self.calc.calculate_average_processing_time()
        self.assertAlmostEqual(avg, 20.0, places=1)
    
    def test_export_to_csv(self):
        """Vérifie l'export des métriques en CSV"""
        tmpdir = tempfile.mkdtemp()
        try:
            self.calc.add_transcription(3600, 720, "f1.mp3", "small", True)
            csv_path = os.path.join(tmpdir, "metrics.csv")
            
            result = self.calc.export_to_csv(csv_path)
            self.assertTrue(result)
            self.assertTrue(os.path.exists(csv_path))
            
            # Vérifier le contenu
            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
            self.assertGreater(len(rows), 1)  # Header + data
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_wer_empty_reference(self):
        """Vérifie le WER avec référence vide"""
        wer = self.calc.calculate_wer("", "quelques mots")
        self.assertGreater(wer, 0)
    
    def test_wer_empty_hypothesis(self):
        """Vérifie le WER avec hypothèse vide"""
        wer = self.calc.calculate_wer("quelques mots", "")
        self.assertEqual(wer, 1.0)


# ============================================================
# CPUAffinityManager (tests complémentaires)
# ============================================================
class TestCPUAffinityManagerExtended(unittest.TestCase):
    """Tests complémentaires pour CPUAffinityManager"""
    
    def test_equilibrage_charge(self):
        """Vérifie l'alias equilibrage_charge"""
        audios = [Audio(f"file{i}.mp3", 100 * (i + 1)) for i in range(6)]
        
        listes = CPUAffinityManager.equilibrage_charge(audios, 3)
        
        self.assertEqual(len(listes), 3)
        total = sum(sum(a.duree for a in l) for l in listes)
        self.assertEqual(total, sum(100 * (i + 1) for i in range(6)))
    
    def test_glouton_single_process(self):
        """Vérifie la répartition sur 1 seul processus"""
        audios = [Audio(f"f{i}.mp3", 100) for i in range(5)]
        listes = CPUAffinityManager.glouton_n_listes(audios, 1)
        
        self.assertEqual(len(listes), 1)
        self.assertEqual(len(listes[0]), 5)
    
    def test_glouton_more_processes_than_files(self):
        """Vérifie le comportement avec plus de processus que de fichiers"""
        audios = [Audio("f1.mp3", 100)]
        listes = CPUAffinityManager.glouton_n_listes(audios, 5)
        
        self.assertEqual(len(listes), 5)
        non_empty = [l for l in listes if len(l) > 0]
        self.assertEqual(len(non_empty), 1)
    
    def test_get_cpu_affinity(self):
        """Vérifie la lecture de l'affinité CPU"""
        cores = CPUAffinityManager.get_cpu_affinity()
        # Sur macOS, la méthode peut retourner une liste vide (non supporté)
        self.assertIsInstance(cores, list)
    
    def test_audio_repr(self):
        """Vérifie la représentation string d'Audio"""
        audio = Audio("test.mp3", 3600.5)
        repr_str = repr(audio)
        self.assertIn("test.mp3", repr_str)
        self.assertIn("3600.50", repr_str)


# ============================================================
# MAIN
# ============================================================
def run_tests():
    """Exécute tous les tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestTranscriptionExporter))
    suite.addTests(loader.loadTestsFromTestCase(TestAudioConverter))
    suite.addTests(loader.loadTestsFromTestCase(TestSystemMonitor))
    suite.addTests(loader.loadTestsFromTestCase(TestPowerMonitor))
    suite.addTests(loader.loadTestsFromTestCase(TestQoSReporter))
    suite.addTests(loader.loadTestsFromTestCase(TestFileHandler))
    suite.addTests(loader.loadTestsFromTestCase(TestWhisperTranscriber))
    suite.addTests(loader.loadTestsFromTestCase(TestMetricsCalculatorExtended))
    suite.addTests(loader.loadTestsFromTestCase(TestCPUAffinityManagerExtended))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
