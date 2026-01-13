# Station TV - Transcription Audio Haute Performance

**Système de transcription audio haute performance basé sur Whisper (OpenAI)**  
Développé pour la plateforme Station TV du LIFAT (Laboratoire d'Informatique Fondamentale et Appliquée de Tours)

---

## 📋 Vue d'ensemble

Ce projet permet la transcription automatique à grande échelle de flux audio issus de la TNT française. Il est conçu pour fonctionner sur une infrastructure haute performance (Dell Precision 5820 - 256 Go RAM - Xeon W-2295 36 threads).

### Caractéristiques principales

- ✅ **Transcription multi-process** optimisée avec répartition CPU intelligente
- ✅ **Support multi-modèles** Whisper (tiny → large)
- ✅ **Monitoring QoS** temps réel (CPU, RAM, throughput, WER)
- ✅ **Export multi-formats** (TXT, SRT, CSV, JSON)
- ✅ **Architecture modulaire** et extensible
- ✅ **Configuration centralisée** via fichiers YAML

---

## 🏗️ Architecture

```
stationtv/
├── config/                     # Configuration YAML
├── core/                       # Module de transcription Whisper
│   ├── transcription.py        # WhisperTranscriber
│   ├── models.py               # ModelManager
│   └── affinity.py             # CPUAffinityManager
├── qos/                        # Module QoS
│   ├── monitor.py              # SystemMonitor
│   ├── metrics.py              # MetricsCalculator
│   └── reporter.py             # QoSReporter
├── utils/                      # Utilitaires
│   ├── logger.py               # Système de logging
│   └── file_handler.py         # Gestion fichiers audio
├── preprocessing/              # Prétraitement audio (futur)
├── export/                     # Export et intégration (futur)
├── scripts/                    # Scripts principaux
│   ├── BasicTestWhisper.py     # Tests unitaires
│   ├── RunBatchWhisper.py      # Traitement batch
│   └── ComputeQoS.py           # Génération rapports QoS
└── WhisperTranscriptor.py      # Script original (référence)
```

---

## 🚀 Installation

### Prérequis

- **Python 3.10+**
- **256 Go RAM** (recommandé pour modèles large)
- **CPU multi-cœurs** (18+ cœurs physiques)
- **FFmpeg** (pour prétraitement audio)

### Installation des dépendances

```powershell
# Créer un environnement virtuel
python -m venv venv
.\venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

---

## ⚙️ Configuration

La configuration se fait via le fichier `config/default_config.yaml`.

**Paramètres principaux :**

```yaml
hardware:
  cpu_threads: 36                # Threads disponibles
  max_parallel_processes: 3      # Processus simultanés

whisper:
  model: "small"                 # Modèle (tiny/base/small/medium/large)
  language: "fr"                 # Langue
  output_formats:
    txt: true                    # Transcription texte
    srt: true                    # Sous-titres horodatés
    json: true                   # Format structuré

qos:
  enabled: true                  # Activer le monitoring
  monitoring_interval: 2         # Intervalle (secondes)

paths:
  input_audio_dir: "bdd"         # Répertoire audio TNT
  output_dir: "output"           # Répertoire de sortie
```

---

## 📖 Utilisation

### 1. Test unitaire d'un modèle

```powershell
python scripts/BasicTestWhisper.py --input fichier_test.mp3 --model small
```

### 2. Transcription batch multi-process

```powershell
# Scanner les fichiers audio
python scripts/RunBatchWhisper.py --scan-only

# Lancer la transcription batch
python scripts/RunBatchWhisper.py --config config/default_config.yaml
```

### 3. Génération des rapports QoS

```powershell
python scripts/ComputeQoS.py --session-dir output/reports
```

---

## 📊 Métriques QoS

Le système génère automatiquement :

- **Graphiques CPU/RAM** (PNG haute résolution)
- **Métriques de performance** : throughput, temps moyen, taux de réussite
- **Word Error Rate (WER)** sur échantillons
- **Rapports textuels** détaillés

**Objectifs de performance :**
- Throughput ≥ 5× (modèle small)
- Throughput ≥ 1× (modèle medium)
- Utilisation CPU > 85%
- Utilisation RAM < 90%
- Taux de réussite ≥ 99%

---

## 🔧 Développement

### Structure modulaire

Chaque module est indépendant et réutilisable :

- `core/` : Logique de transcription
- `qos/` : Supervision et métriques
- `utils/` : Fonctions utilitaires
- `scripts/` : Points d'entrée

### Logging

Le système utilise un logger centralisé :

```python
from utils.logger import setup_logger

logger = setup_logger("MonModule", level="INFO")
logger.info("Message informationnel")
logger.warning("Avertissement")
logger.error("Erreur")
```

---

## 📝 Références

- **WhisperTranscriptor.py** : Script original ayant servi de base
- **Whisper (OpenAI)** : https://github.com/openai/whisper
- **Station TV (LIFAT)** : Projet de recherche RFAI

---

## 👥 Auteurs

- **Dorian Brisson** - Étudiant 5A ISIE, Polytech Tours (2025-2026)
- **Encadrant** : M. Mathieu Delalandre (LIFAT)
- **Base de code** : T. Bourdeau (2024-2025)

---

## 📄 Licence

Projet académique - Polytech Tours / LIFAT
