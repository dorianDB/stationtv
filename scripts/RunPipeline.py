"""
Station TV - Pipeline Automatique Complet
Lance tout le processus de transcription avec QoS et rapports
"""

import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

# Configuration
STATION_TV_DIR = Path(__file__).parent.parent
CONFIG_FILE = STATION_TV_DIR / "config" / "default_config.yaml"


def run_command(cmd, description):
    """Exécute une commande et affiche le résultat."""
    print("\n" + "=" * 80)
    print(f"▶️  {description}")
    print("=" * 80)
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=str(STATION_TV_DIR),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - Terminé avec succès")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ {description} - Erreur")
            if result.stderr:
                print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution: {str(e)}")
        return False


def main():
    """Pipeline automatique complet."""
    
    start_time = time.time()
    
    print("=" * 80)
    print("STATION TV - PIPELINE AUTOMATIQUE COMPLET")
    print("=" * 80)
    print(f"Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Répertoire: {STATION_TV_DIR}")
    print(f"Configuration: {CONFIG_FILE}")
    print("=" * 80)
    
    # Étape 1: Scan des fichiers audio
    print("\n" + "🔍 ÉTAPE 1/4: SCAN DES FICHIERS AUDIO")
    success = run_command(
        f"python scripts/RunBatchWhisper.py --config {CONFIG_FILE} --scan-only",
        "Scan des fichiers audio"
    )
    
    if not success:
        print("\n❌ Échec du scan. Arrêt du pipeline.")
        return 1
    
    # Pause pour réviser
    print("\n📋 Fichiers scannés. Vérifiez fichiers_audio.csv si nécessaire.")
    input("Appuyez sur Entrée pour continuer vers la transcription...")
    
    # Étape 2: Transcription batch avec monitoring
    print("\n" + "🎤 ÉTAPE 2/4: TRANSCRIPTION BATCH")
    print("⚠️  Ceci peut prendre plusieurs heures selon le nombre de fichiers...")
    
    success = run_command(
        f"python scripts/RunBatchWhisper.py --config {CONFIG_FILE}",
        "Transcription batch avec monitoring QoS"
    )
    
    if not success:
        print("\n❌ Échec de la transcription. Arrêt du pipeline.")
        return 1
    
    # Étape 3: Génération des rapports QoS
    print("\n" + "📊 ÉTAPE 3/4: GÉNÉRATION DES RAPPORTS QoS")
    
    success = run_command(
        "python scripts/ComputeQoS.py --session-dir test_output/reports",
        "Génération graphiques et rapports QoS"
    )
    
    if not success:
        print("\n⚠️  Génération QoS échouée, mais transcriptions OK")
    
    # Étape 4: Tests unitaires (optionnel)
    print("\n" + "🧪 ÉTAPE 4/4: TESTS UNITAIRES (Optionnel)")
    
    run_tests = input("Lancer les tests unitaires? (o/n): ").lower().strip()
    
    if run_tests == 'o':
        success = run_command(
            "python scripts/RunTests.py",
            "Exécution des tests unitaires"
        )
    else:
        print("⏩ Tests ignorés")
    
    # Résumé final
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "=" * 80)
    print("✅ PIPELINE TERMINÉ AVEC SUCCÈS")
    print("=" * 80)
    print(f"Durée totale: {duration/3600:.2f} heures ({duration/60:.1f} minutes)")
    print(f"Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n📁 Fichiers générés:")
    print("  - Transcriptions: dans le dossier source (bdd)")
    print("  - Rapports QoS: test_output/reports/")
    print("  - Graphiques: test_output/reports/*.png")
    print("  - Trackers: test_output/trackers/")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erreur fatale: {str(e)}")
        sys.exit(1)
