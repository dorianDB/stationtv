# Diagrammes UML - Station TV

Ce répertoire contient les diagrammes PlantUML documentant l'architecture et les flux d'exécution du projet Station TV.

## 📋 Contenu

### 1. Diagramme de Classes (`class_diagram.puml`)

Représente l'architecture complète du système avec :

- **Package `core`** : Classes de transcription Whisper
  - `WhisperTranscriber` : Classe principale de transcription
  - `ModelManager` : Gestion des modèles Whisper et de la mémoire
  - `CPUAffinityManager` : Répartition des tâches sur les cœurs CPU
  - `Audio` : Représentation d'un fichier audio

- **Package `qos`** : Monitoring et métriques de qualité
  - `SystemMonitor` : Surveillance CPU/RAM en temps réel
  - `MetricsCalculator` : Calcul des KPI (throughput, WER, etc.)
  - `QoSReporter` : Génération de rapports et graphiques

- **Package `utils`** : Utilitaires
  - `FileHandler` : Gestion des fichiers audio
  - `Logger` : Système de logging centralisé

- **Package `export`** : Export multi-formats
  - `TranscriptionExporter` : Export JSON/CSV avec métadonnées

- **Package `preprocessing`** : Prétraitement audio
  - `AudioConverter` : Conversion et normalisation audio

### 2. Diagramme de Séquence - Batch (`sequence_batch_transcription.puml`)

Décrit le flux complet d'une transcription **batch multi-process** :

1. **Initialisation** : Configuration, validation mémoire
2. **Scan** : Découverte et analyse des fichiers audio
3. **Équilibrage** : Répartition optimale sur N processus
4. **Monitoring** : Démarrage surveillance CPU/RAM
5. **Transcription parallèle** : 3 processus simultanés avec affinité CPU
6. **Génération rapports** : Métriques QoS et graphiques
7. **Résultats** : Statistiques finales

**Cas d'usage** : `RunBatchWhisper.py` - Traitement de masse (1000+ fichiers)

### 3. Diagramme de Séquence - Simple (`sequence_simple_transcription.puml`)

Décrit le flux d'une transcription **unitaire** :

1. **Initialisation** : Configuration minimale
2. **Chargement modèle** : Téléchargement et mise en cache
3. **Transcription** : Traitement d'un seul fichier
4. **Export multi-formats** : TXT, SRT, JSON
5. **Résultats** : Métriques de performance

**Cas d'usage** : `BasicTestWhisper.py` - Tests unitaires

## 🛠️ Génération des diagrammes

### Prérequis

Installer PlantUML :

```bash
# Windows (Chocolatey)
choco install plantuml

# Linux (apt)
sudo apt-get install plantuml

# macOS (Homebrew)
brew install plantuml
```

### Générer les images PNG

```bash
# Depuis le répertoire diagrams/
plantuml class_diagram.puml
plantuml sequence_batch_transcription.puml
plantuml sequence_simple_transcription.puml

# Ou générer tous les diagrammes d'un coup
plantuml *.puml
```

### Générer les images SVG (vectoriel)

```bash
plantuml -tsvg *.puml
```

## 📖 Visualisation en ligne

Si vous n'avez pas PlantUML installé, vous pouvez visualiser les diagrammes en ligne :

1. Copier le contenu d'un fichier `.puml`
2. Aller sur : http://www.plantuml.com/plantuml/uml/
3. Coller le code dans l'éditeur
4. Visualiser et télécharger l'image

**Ou utiliser l'URL encoder** :

```bash
# Encoder le fichier
plantuml -encodeurl class_diagram.puml

# Ouvrir l'URL générée dans le navigateur
```

## 🔧 Édition avec VSCode

### Extension recommandée

Installer l'extension **PlantUML** pour VSCode :

```
Name: PlantUML
Id: jebbs.plantuml
Publisher: jebbs
```

### Prévisualisation en temps réel

1. Ouvrir un fichier `.puml`
2. Appuyer sur `Alt + D` (Windows/Linux) ou `Option + D` (macOS)
3. La prévisualisation s'affiche à droite

### Raccourcis utiles

- `Alt + D` : Aperçu
- `Ctrl + Shift + P` → "PlantUML: Export Current Diagram" : Exporter en PNG/SVG

## 📐 Conventions utilisées

### Diagramme de Classes

- **Couleurs par package** :
  - Bleu (`CORE_COLOR`) : Package `core`
  - Orange (`QOS_COLOR`) : Package `qos`
  - Vert (`UTILS_COLOR`) : Package `utils`
  - Violet (`EXPORT_COLOR`) : Package `export`
  - Rose (`PREPROCESSING_COLOR`) : Package `preprocessing`

- **Relations** :
  - `*--` : Composition (forte dépendance)
  - `..>` : Dépendance d'utilisation
  - `{static}` : Méthode statique

### Diagrammes de Séquence

- **Thème** : `!theme plain` pour une meilleure lisibilité
- **Sections** : `== Phase X ==` pour structurer les flux
- **Notes** : Explications contextuelles
- **Conditions** : `alt/else/end` pour les branches conditionnelles
- **Parallélisme** : `par/else/end` pour les processus simultanés

## 📚 Références

- **PlantUML Documentation** : https://plantuml.com/
- **PlantUML Class Diagram** : https://plantuml.com/class-diagram
- **PlantUML Sequence Diagram** : https://plantuml.com/sequence-diagram
- **Cheatsheet** : https://plantuml.com/vizjs

## 🔄 Maintenance

Les diagrammes doivent être mis à jour lorsque :

- ✅ Ajout d'une nouvelle classe publique
- ✅ Modification d'une interface publique
- ✅ Changement dans les flux d'exécution principaux
- ✅ Ajout d'un nouveau module/package

**Ne pas mettre à jour pour** :

- ❌ Méthodes privées internes
- ❌ Variables temporaires
- ❌ Détails d'implémentation sans impact architectural

---

**Auteur** : Dorian Brisson  
**Date** : Décembre 2025  
**Projet** : Station TV - LIFAT (Polytech Tours)
