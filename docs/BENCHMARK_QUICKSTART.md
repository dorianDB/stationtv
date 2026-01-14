# 🚀 Quick Start - Benchmark Whisper

Guide rapide pour lancer un benchmark des modèles Whisper.

## 📦 Installation des dépendances (une seule fois)

```bash
# Pour générer les rapports Excel (optionnel)
pip install openpyxl pandas
```

## 🎯 Workflow complet en 4 étapes

### Étape 1: Préparer les fichiers de test

```bash
# Créer des fichiers de test à partir d'un fichier audio source
python scripts/PrepareTestFiles.py --source "chemin/vers/votre_fichier.mp3"

# Ou avec des durées personnalisées
python scripts/PrepareTestFiles.py --source "fichier.mp3" --durations 60 120 300 600
```

Cela créera dans le dossier `bdd/`:
- `test_240s.mp3` (4 min)
- `test_480s.mp3` (8 min)
- `test_720s.mp3` (12 min)
- `test_960s.mp3` (16 min)
- `test_1200s.mp3` (20 min)

### Étape 2: Configurer le benchmark

Éditez `config/benchmark_config.yaml` pour ajuster:
- Les modèles à tester (`tiny`, `base`, `small`, `medium`, `large`)
- Le nombre de répétitions (5 ou 6)
- Les cœurs CPU à utiliser

### Étape 3: Lancer le benchmark

```bash
# Benchmark complet (peut prendre plusieurs heures)
python scripts/BenchmarkModels.py

# Ou commencer petit (tests rapides)
python scripts/BenchmarkModels.py --models tiny base --repetitions 3
```

### Étape 4: Générer le rapport Excel

```bash
# Créer un fichier Excel avec graphiques
python scripts/GenerateExcelReport.py
```

Vous obtenez:
- `output/benchmark_results.csv` - Données CSV
- `output/benchmark_results_summary.csv` - Matrice résumé
- `output/benchmark_report.xlsx` - Rapport Excel formaté

## 📊 Exemple rapide (test en 5 minutes)

```bash
# 1. Préparer un petit fichier de test
python scripts/PrepareTestFiles.py --source "votre_fichier.mp3" --durations 60 120

# 2. Tester seulement le modèle tiny (rapide)
python scripts/BenchmarkModels.py --models tiny --repetitions 3

# 3. Voir les résultats
cat output/benchmark_results_summary.csv
```

## 🔧 Options avancées

### Tester seulement certains modèles

```bash
# Petits modèles uniquement
python scripts/BenchmarkModels.py --models tiny base small

# Grands modèles uniquement
python scripts/BenchmarkModels.py --models medium large
```

### Modifier le nombre de répétitions

```bash
# 3 répétitions (plus rapide)
python scripts/BenchmarkModels.py --repetitions 3

# 6 répétitions (plus précis)
python scripts/BenchmarkModels.py --repetitions 6
```

### Spécifier un fichier de sortie

```bash
python scripts/BenchmarkModels.py --output results/test_2026_01_14.csv
```

## 📂 Structure des fichiers

```
stationtv/
├── config/
│   └── benchmark_config.yaml    # Configuration du benchmark
├── scripts/
│   ├── PrepareTestFiles.py      # Prépare les fichiers de test
│   ├── BenchmarkModels.py       # Lance le benchmark
│   └── GenerateExcelReport.py   # Crée le rapport Excel
├── bdd/
│   ├── test_240s.mp3            # Fichiers de test
│   ├── test_480s.mp3
│   └── ...
└── output/
    ├── benchmark_results.csv     # Résultats détaillés
    ├── benchmark_results_summary.csv  # Matrice résumé
    └── benchmark_report.xlsx     # Rapport Excel
```

## ⚠️ Important

1. **Durée**: Un benchmark complet peut prendre plusieurs heures
2. **Mémoire**: Les modèles large/medium nécessitent beaucoup de RAM
3. **Interruption**: Vous pouvez arrêter avec Ctrl+C - les résultats partiels seront sauvegardés

## 📚 Documentation complète

Pour plus de détails, consultez:
- `docs/BENCHMARK_GUIDE.md` - Guide complet
- `config/benchmark_config.yaml` - Configuration détaillée

## 💡 Conseils

### Pour des résultats cohérents:
1. Fermez les autres applications
2. Débranchez les périphériques non essentiels
3. Désactivez les programmes en arrière-plan
4. Lancez les tests lorsque le CPU est froid

### Pour économiser du temps:
1. Commencez par 1-2 répétitions pour valider
2. Testez d'abord les petits modèles (tiny, base)
3. Utilisez des fichiers courts au début (60s, 120s)

## 🆘 Dépannage

### "Fichier introuvable"
→ Vérifiez que les fichiers sont dans le dossier `bdd/`

### "ffmpeg non trouvé"
→ Installez ffmpeg: https://ffmpeg.org/download.html

### "Mémoire insuffisante"
→ Testez les modèles séparément avec `--models tiny`

### Le benchmark est trop long
→ Réduisez les répétitions avec `--repetitions 3`
