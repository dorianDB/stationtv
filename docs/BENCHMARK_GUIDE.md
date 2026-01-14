# Benchmark des Modèles Whisper

Ce document explique comment utiliser le script de benchmark pour tester les performances de différents modèles Whisper.

## 📋 Vue d'ensemble

Le script `BenchmarkModels.py` permet de :
- Tester plusieurs modèles Whisper (tiny, base, small, medium, large)
- Exécuter plusieurs répétitions pour chaque test (5-6 fois)
- Mesurer précisément les temps de traitement
- Exporter les résultats dans un fichier CSV prêt pour Excel

## 🚀 Utilisation

### 1. Préparer vos fichiers audio

Créez des fichiers audio de différentes durées dans le répertoire `bdd/` :
- `test_240s.mp3` (4 minutes)
- `test_480s.mp3` (8 minutes)
- `test_720s.mp3` (12 minutes)
- `test_960s.mp3` (16 minutes)
- `test_1200s.mp3` (20 minutes)

**Astuce** : Vous pouvez utiliser `ffmpeg` pour découper des fichiers audio :
```bash
# Extraire les 4 premières minutes (240 secondes)
ffmpeg -i fichier_source.mp3 -t 240 -c copy test_240s.mp3
```

### 2. Configurer le benchmark

Éditez le fichier `config/benchmark_config.yaml` :

```yaml
benchmark:
  # Modèles à tester
  models:
    - 'tiny'
    - 'base'
    - 'small'
    - 'medium'
    - 'large'  # Optionnel
  
  # Nombre de répétitions
  repetitions: 5
  
  # Fichiers audio à tester
  audio_files:
    - 'bdd/test_240s.mp3'
    - 'bdd/test_480s.mp3'
    - 'bdd/test_720s.mp3'
    - 'bdd/test_960s.mp3'
    - 'bdd/test_1200s.mp3'
  
  # Cœurs CPU à utiliser
  cpu_cores: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
```

### 3. Lancer le benchmark

```bash
# Utiliser la config par défaut
python scripts/BenchmarkModels.py

# Ou spécifier une config personnalisée
python scripts/BenchmarkModels.py --config config/benchmark_config.yaml

# Tester seulement certains modèles
python scripts/BenchmarkModels.py --models tiny base small

# Changer le nombre de répétitions
python scripts/BenchmarkModels.py --repetitions 6

# Spécifier un fichier de sortie
python scripts/BenchmarkModels.py --output results/mon_benchmark.csv
```

### 4. Résultats

Le script génère deux fichiers CSV :

#### a) Fichier détaillé : `benchmark_results.csv`

Contient toutes les informations de chaque test :

| file | duration_s | duration_min | model | repetitions | avg_time_s | min_time_s | max_time_s | std_dev_s | throughput | run_1 | run_2 | run_3 | run_4 | run_5 |
|------|------------|--------------|-------|-------------|------------|------------|------------|-----------|------------|-------|-------|-------|-------|-------|
| test_240s.mp3 | 240 | 4.00 | tiny | 5 | 55.35 | 54.12 | 56.89 | 1.05 | 4.34 | 55.35 | 54.12 | 56.89 | 55.01 | 55.20 |
| test_240s.mp3 | 240 | 4.00 | base | 5 | 97.04 | 95.23 | 99.12 | 1.52 | 2.47 | 97.04 | 95.23 | 99.12 | 96.87 | 97.45 |

#### b) Résumé matriciel : `benchmark_results_summary.csv`

Format similaire à votre image Excel :

| Duration (s) | tiny | base | small | medium | large |
|--------------|------|------|-------|--------|-------|
| 0 | 0 | 0 | 0 | 0 | 0 |
| 240 | 55.35 | 97.04 | 270.48 | 778.76 | |
| 480 | 97.55 | 176.23 | 545.26 | 1435.22 | |
| 720 | 183.90 | 317.53 | 752.30 | 2181.12 | |
| 960 | 264.14 | 378.22 | 1311.25 | 2861.25 | |
| 1200 | 301.51 | 478.76 | 1420.10 | 3630.68 | |
| Th (avg) | 3.98 | 2.51 | 0.85 | 0.33 | |
| 1/Th (avg) | 0.251 | 0.399 | 1.183 | 3.026 | |

## 📊 Importer dans Excel

1. Ouvrez Excel
2. `Données` → `Depuis un fichier CSV`
3. Sélectionnez `benchmark_results_summary.csv`
4. Configurez le séparateur (virgule)
5. Créez vos graphiques à partir des données

### Exemple de graphiques à créer

Comme dans votre document :
- **Graphique 1** : Temps de traitement en fonction de la durée audio (une ligne par modèle)
  - Axe X : Durée audio (s)
  - Axe Y : Temps de traitement (s)
  - Séries : tiny, base, small, medium, large

- **Graphique 2** : Throughput (Th) par modèle
  - Graphique en barres montrant le throughput moyen de chaque modèle

## 🔍 Comprendre les métriques

- **avg_time_s** : Temps moyen de traitement (moyenne des répétitions)
- **min_time_s** : Temps minimum observé
- **max_time_s** : Temps maximum observé
- **std_dev_s** : Écart-type (variabilité des mesures)
- **throughput** : Ratio durée_audio / temps_traitement
  - Valeur > 1 : Traitement plus rapide que le temps réel
  - Valeur < 1 : Traitement plus lent que le temps réel
- **Th** : Throughput moyen pour un modèle
- **1/Th** : Inverse du throughput (temps de traitement / durée audio)

## ⚙️ Options avancées

### Modifier les cœurs CPU

Pour tester avec différentes configurations CPU :

```yaml
cpu_cores: [0, 1, 2, 3]  # 4 cœurs
# ou
cpu_cores: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]  # 12 cœurs
```

### Ajouter d'autres durées

Vous pouvez tester avec n'importe quelle durée :

```yaml
audio_files:
  - 'bdd/test_120s.mp3'   # 2 minutes
  - 'bdd/test_300s.mp3'   # 5 minutes
  - 'bdd/test_600s.mp3'   # 10 minutes
  - 'bdd/test_1800s.mp3'  # 30 minutes
```

### Benchmark partiel

Si vous voulez tester uniquement certains modèles :

```bash
# Seulement les petits modèles
python scripts/BenchmarkModels.py --models tiny base

# Seulement medium et large
python scripts/BenchmarkModels.py --models medium large
```

## 💡 Conseils

1. **Commencez petit** : Testez d'abord avec 1-2 répétitions sur les petits modèles
2. **Cohérence** : Fermez les autres applications pour des mesures cohérentes
3. **Température CPU** : Laissez le CPU refroidir entre les tests longs
4. **Interruption** : Vous pouvez arrêter avec Ctrl+C - les résultats partiels seront sauvegardés

## 📝 Exemple de workflow complet

```bash
# 1. Préparer les fichiers de test
ffmpeg -i source.mp3 -t 240 -c copy bdd/test_240s.mp3
ffmpeg -i source.mp3 -t 480 -c copy bdd/test_480s.mp3
ffmpeg -i source.mp3 -t 720 -c copy bdd/test_720s.mp3
ffmpeg -i source.mp3 -t 960 -c copy bdd/test_960s.mp3
ffmpeg -i source.mp3 -t 1200 -c copy bdd/test_1200s.mp3

# 2. Vérifier la configuration
cat config/benchmark_config.yaml

# 3. Lancer le benchmark (commence par les petits modèles)
python scripts/BenchmarkModels.py --models tiny base small --repetitions 5

# 4. Si tout va bien, tester les gros modèles
python scripts/BenchmarkModels.py --models medium large --repetitions 3

# 5. Vérifier les résultats
cat output/benchmark_results_summary.csv
```

## 🐛 Dépannage

### Erreur "Fichier introuvable"
- Vérifiez que les fichiers audio existent dans le répertoire `bdd/`
- Utilisez des chemins absolus si nécessaire

### Mémoire insuffisante
- Testez les modèles séparément (`--models tiny`)
- Réduisez le nombre de répétitions (`--repetitions 3`)

### Temps de traitement trop long
- Commencez par des fichiers courts
- Testez d'abord les petits modèles (tiny, base)

## 📚 Références

Ces tests sont inspirés de la méthodologie du document de recherche sur le ASR scalable avec WhisperAI.
