"""
Station TV - Benchmark des modèles Whisper
Script de test permettant d'évaluer les performances de différents modèles
sur plusieurs fichiers audio avec des répétitions multiples.

Usage:
    python scripts/BenchmarkModels.py --config config/benchmark_config.yaml
"""

import sys
import argparse
import yaml
import time
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
import statistics

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.transcription import WhisperTranscriber
from core.affinity import CPUAffinityManager
from utils.logger import setup_logger
from utils.file_handler import FileHandler

# Logger
logger = setup_logger("BenchmarkModels", level="INFO")


class BenchmarkRunner:
    """Classe pour exécuter les benchmarks de modèles Whisper."""
    
    def __init__(self, config: dict):
        """
        Initialise le runner de benchmark.
        
        Args:
            config: Configuration du benchmark
        """
        self.config = config
        self.results = []
        # Récupérer num_threads depuis la config (par défaut: None = auto)
        self.num_threads = config.get('benchmark', {}).get('num_threads', None)
        
    def run_single_test(
        self,
        audio_file: str,
        model_name: str,
        cpu_cores: List[int],
        run_number: int
    ) -> Tuple[float, bool]:
        """
        Exécute un test unique de transcription.
        
        Args:
            audio_file: Chemin du fichier audio
            model_name: Nom du modèle Whisper
            cpu_cores: Cœurs CPU à utiliser
            run_number: Numéro de l'exécution (pour le tracking)
        
        Returns:
            Tuple (temps de traitement en secondes, succès)
        """
        # Créer une configuration temporaire pour ce modèle
        temp_config = self.config.copy()
        temp_config['whisper']['model'] = model_name
        
        # Si num_threads est défini, l'ajouter à la config
        if self.num_threads is not None:
            temp_config['num_threads'] = self.num_threads
        
        # Créer le transcripteur
        transcriber = WhisperTranscriber(temp_config)
        
        logger.info(f"  Test #{run_number} avec {model_name}...")
        
        try:
            start_time = time.time()
            
            # Transcription avec sauvegarde des fichiers
            # Utilise process_and_write pour sauvegarder avec le numéro de run
            success = transcriber.process_and_write(
                audio_file,
                cpu_cores,
                core_index=0,
                run_number=run_number
            )
            
            processing_time = time.time() - start_time
            
            if not success:
                logger.error(f"    ❌ Échec de la transcription")
                return 0.0, False
            
            logger.info(f"    ✓ Complété en {processing_time:.2f}s")
            return processing_time, True
            
        except Exception as e:
            logger.error(f"    ❌ Erreur: {str(e)}")
            return 0.0, False
    
    def run_benchmark(
        self,
        audio_files: List[str],
        models: List[str],
        repetitions: int,
        cpu_cores: List[int]
    ):
        """
        Exécute le benchmark complet.
        
        Args:
            audio_files: Liste des fichiers audio à tester
            models: Liste des modèles à tester
            repetitions: Nombre de répétitions pour chaque test
            cpu_cores: Cœurs CPU à utiliser
        """
        logger.info("=" * 80)
        logger.info("DÉMARRAGE DU BENCHMARK")
        logger.info("=" * 80)
        logger.info(f"Fichiers audio: {len(audio_files)}")
        logger.info(f"Modèles: {', '.join(models)}")
        logger.info(f"Répétitions par test: {repetitions}")
        logger.info(f"Cœurs CPU: {cpu_cores}")
        logger.info("=" * 80)
        
        total_tests = len(audio_files) * len(models) * repetitions
        current_test = 0
        
        # Pour chaque fichier audio
        for audio_file in audio_files:
            audio_path = Path(audio_file)
            
            if not audio_path.exists():
                logger.warning(f"⚠️ Fichier introuvable: {audio_file}")
                continue
            
            # Obtenir la durée du fichier
            try:
                from utils.file_handler import FichierAudio
                fichier_audio = FichierAudio(str(audio_path))
                audio_duration = fichier_audio.longueur
            except Exception as e:
                logger.warning(f"Impossible d'obtenir la durée du fichier: {str(e)}")
                audio_duration = 0
            
            logger.info("")
            logger.info("=" * 80)
            logger.info(f"FICHIER: {audio_path.name}")
            logger.info(f"Durée: {audio_duration:.1f}s ({audio_duration/60:.2f} min)")
            logger.info("=" * 80)
            
            # Pour chaque modèle
            for model_name in models:
                logger.info("")
                logger.info(f"📊 Modèle: {model_name}")
                logger.info("-" * 80)
                
                times = []
                
                # Répéter le test
                for run in range(1, repetitions + 1):
                    current_test += 1
                    progress = (current_test / total_tests) * 100
                    
                    logger.info(f"[{current_test}/{total_tests} - {progress:.1f}%]")
                    
                    processing_time, success = self.run_single_test(
                        str(audio_path),
                        model_name,
                        cpu_cores,
                        run
                    )
                    
                    if success:
                        times.append(processing_time)
                
                # Calculer les statistiques
                if times:
                    avg_time = statistics.mean(times)
                    median_time = statistics.median(times)
                    min_time = min(times)
                    max_time = max(times)
                    std_dev = statistics.stdev(times) if len(times) > 1 else 0
                    
                    # Calculer les RT (Real-Time factors) pour chaque run
                    rt_factors = [audio_duration / t if t > 0 else 0 for t in times]
                    avg_rt = statistics.mean(rt_factors)
                    median_rt = statistics.median(rt_factors)
                    
                    logger.info("-" * 80)
                    logger.info(f"📈 Résultats pour {model_name} ({len(times)}/{repetitions} réussis):")
                    logger.info(f"   Temps moyen    : {avg_time:.2f}s")
                    logger.info(f"   Temps médian   : {median_time:.2f}s")
                    logger.info(f"   Temps min      : {min_time:.2f}s")
                    logger.info(f"   Temps max      : {max_time:.2f}s")
                    logger.info(f"   Écart-type     : {std_dev:.2f}s")
                    logger.info(f"   RT moyen       : {avg_rt:.3f}× temps réel")
                    logger.info(f"   RT médian      : {median_rt:.3f}× temps réel")
                    
                    # Enregistrer les résultats
                    self.results.append({
                        'file': audio_path.name,
                        'duration_s': audio_duration,
                        'model': model_name,
                        'repetitions': len(times),
                        'avg_time': avg_time,
                        'median_time': median_time,
                        'min_time': min_time,
                        'max_time': max_time,
                        'std_dev': std_dev,
                        'avg_rt': avg_rt,
                        'median_rt': median_rt,
                        'all_times': times,
                        'all_rt_factors': rt_factors
                    })
                else:
                    logger.warning(f"⚠️ Aucun test réussi pour {model_name}")
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("BENCHMARK TERMINÉ")
        logger.info("=" * 80)
    
    def export_results(self, output_file: str):
        """
        Exporte les résultats dans un fichier CSV.
        
        Args:
            output_file: Chemin du fichier de sortie
        """
        if not self.results:
            logger.warning("Aucun résultat à exporter")
            return
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"\n📊 Export des résultats vers {output_file}")
        
        # Créer le CSV avec toutes les informations
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'file', 'duration_s', 'duration_min', 'model', 'repetitions',
                'avg_time_s', 'median_time_s', 'min_time_s', 'max_time_s', 'std_dev_s',
                'avg_rt', 'median_rt',
                'run_1', 'run_2', 'run_3', 'run_4', 'run_5',
                'run_6', 'run_7', 'run_8', 'run_9', 'run_10',
                'rt_1', 'rt_2', 'rt_3', 'rt_4', 'rt_5',
                'rt_6', 'rt_7', 'rt_8', 'rt_9', 'rt_10'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in self.results:
                row = {
                    'file': result['file'],
                    'duration_s': f"{result['duration_s']:.2f}",
                    'duration_min': f"{result['duration_s']/60:.2f}",
                    'model': result['model'],
                    'repetitions': result['repetitions'],
                    'avg_time_s': f"{result['avg_time']:.2f}",
                    'median_time_s': f"{result['median_time']:.2f}",
                    'min_time_s': f"{result['min_time']:.2f}",
                    'max_time_s': f"{result['max_time']:.2f}",
                    'std_dev_s': f"{result['std_dev']:.2f}",
                    'avg_rt': f"{result['avg_rt']:.3f}",
                    'median_rt': f"{result['median_rt']:.3f}"
                }
                
                # Ajouter les temps individuels (jusqu'à 10 runs)
                for i, t in enumerate(result['all_times'], 1):
                    if i <= 10:
                        row[f'run_{i}'] = f"{t:.2f}"
                
                # Ajouter les RT individuels (jusqu'à 10 runs)
                for i, rt in enumerate(result['all_rt_factors'], 1):
                    if i <= 10:
                        row[f'rt_{i}'] = f"{rt:.3f}"
                
                writer.writerow(row)
        
        logger.info(f"✓ Résultats exportés avec succès")
        
        # Créer également un résumé au format Excel-compatible
        summary_file = output_path.parent / f"{output_path.stem}_summary.csv"
        self._export_summary_matrix(str(summary_file))
    
    def _export_summary_matrix(self, output_file: str):
        """
        Exporte un résumé sous forme de matrice (comme dans votre image).
        Crée deux matrices: une pour les temps médians, une pour les RT médians.
        
        Args:
            output_file: Chemin du fichier de sortie
        """
        logger.info(f"📊 Export du résumé matriciel vers {output_file}")
        
        # Organiser les résultats par durée et modèle
        median_time_matrix = {}
        median_rt_matrix = {}
        
        for result in self.results:
            duration = result['duration_s']
            model = result['model']
            median_time = result['median_time']
            median_rt = result['median_rt']
            
            if duration not in median_time_matrix:
                median_time_matrix[duration] = {}
                median_rt_matrix[duration] = {}
            
            median_time_matrix[duration][model] = median_time
            median_rt_matrix[duration][model] = median_rt
        
        # Écrire les matrices
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            models = sorted(set(r['model'] for r in self.results))
            durations = sorted(median_time_matrix.keys())
            
            writer = csv.writer(csvfile)
            
            # === MATRICE 1: Temps de traitement médian (secondes) ===
            writer.writerow(['### TEMPS DE TRAITEMENT MÉDIAN (secondes) ###'])
            writer.writerow([])
            
            # En-tête
            writer.writerow(['Duration (s)'] + models)
            
            # Lignes de données
            for duration in durations:
                row = [f"{duration:.0f}"]
                for model in models:
                    time_val = median_time_matrix.get(duration, {}).get(model, 0)
                    row.append(f"{time_val:.2f}" if time_val > 0 else "")
                writer.writerow(row)
            
            writer.writerow([])
            writer.writerow([])
            
            # === MATRICE 2: RT (Real-Time factor) médian ===
            writer.writerow(['### RT MÉDIAN (Real-Time factor) ###'])
            writer.writerow([])
            
            # En-tête
            writer.writerow(['Duration (s)'] + models)
            
            # Lignes de données
            for duration in durations:
                row = [f"{duration:.0f}"]
                for model in models:
                    rt_val = median_rt_matrix.get(duration, {}).get(model, 0)
                    row.append(f"{rt_val:.3f}" if rt_val > 0 else "")
                writer.writerow(row)
            
            writer.writerow([])
            writer.writerow([])
            
            # === MÉTRIQUES GLOBALES ===
            writer.writerow(['### MÉTRIQUES GLOBALES ###'])
            writer.writerow([])
            
            # Calculer RT médian moyen par modèle
            rt_median_avg_row = ['RT médian moyen']
            rt_inverse_row = ['1/RT médian moyen']
            
            for model in models:
                model_results = [r for r in self.results if r['model'] == model]
                if model_results:
                    avg_median_rt = statistics.mean([r['median_rt'] for r in model_results])
                    rt_median_avg_row.append(f"{avg_median_rt:.3f}")
                    rt_inverse_row.append(f"{1/avg_median_rt:.3f}" if avg_median_rt > 0 else "")
                else:
                    rt_median_avg_row.append("")
                    rt_inverse_row.append("")
            
            writer.writerow(rt_median_avg_row)
            writer.writerow(rt_inverse_row)
        
        logger.info(f"✓ Résumé matriciel exporté avec succès")


def load_config(config_file: str) -> dict:
    """Charge la configuration depuis un fichier YAML."""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"Configuration chargée depuis {config_file}")
        return config
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la configuration: {str(e)}")
        sys.exit(1)


def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(
        description="Benchmark des modèles Whisper - Station TV"
    )
    parser.add_argument(
        '--config', '-c',
        default='config/benchmark_config.yaml',
        help="Fichier de configuration YAML (défaut: config/benchmark_config.yaml)"
    )
    parser.add_argument(
        '--models', '-m',
        nargs='+',
        default=None,
        help="Liste des modèles à tester (ex: tiny base small medium large)"
    )
    parser.add_argument(
        '--repetitions', '-r',
        type=int,
        default=None,
        help="Nombre de répétitions par test (défaut: depuis config)"
    )
    parser.add_argument(
        '--output', '-o',
        default=None,
        help="Fichier de sortie CSV (défaut: depuis config)"
    )
    
    args = parser.parse_args()
    
    # Charger la configuration
    config = load_config(args.config)
    
    # Configuration du benchmark
    benchmark_config = config.get('benchmark', {})
    
    # Modèles à tester
    models = args.models or benchmark_config.get('models', ['tiny', 'base', 'small', 'medium'])
    
    # Nombre de répétitions
    repetitions = args.repetitions or benchmark_config.get('repetitions', 5)
    
    # Fichiers audio à tester
    audio_files = benchmark_config.get('audio_files', [])
    
    if not audio_files:
        logger.error("Aucun fichier audio spécifié dans la configuration")
        return
    
    # Cœurs CPU
    cpu_cores = benchmark_config.get('cpu_cores', list(range(12)))
    
    # Fichier de sortie
    output_file = args.output or benchmark_config.get('output_file', 'output/benchmark_results.csv')
    
    # Créer le runner
    runner = BenchmarkRunner(config)
    
    try:
        # Exécuter le benchmark
        runner.run_benchmark(
            audio_files=audio_files,
            models=models,
            repetitions=repetitions,
            cpu_cores=cpu_cores
        )
        
        # Exporter les résultats
        runner.export_results(output_file)
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ BENCHMARK TERMINÉ AVEC SUCCÈS")
        logger.info("=" * 80)
        logger.info(f"📁 Résultats disponibles dans: {output_file}")
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Interruption par l'utilisateur")
        # Sauvegarder les résultats partiels
        if runner.results:
            logger.info("💾 Sauvegarde des résultats partiels...")
            runner.export_results(output_file)
    except Exception as e:
        logger.error(f"\n❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
