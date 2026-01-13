# Guide de Démarrage Rapide - Station TV

## Installation Rapide

### 1. Installer les dépendances

```powershell
# Activer l'environnement virtuel (si vous en avez un)
.\venv\Scripts\activate

# Installer les packages
pip install -r requirements.txt
```

### 2. Configurer le projet

Éditer `config/default_config.yaml` et adapter les paramètres à votre environnement :

```yaml
paths:
  input_audio_dir: "C:/chemin/vers/vos/fichiers/audio"  # ← MODIFIER ICI
  
whisper:
  model: "small"  # tiny, base, small, medium, large
  
hardware:
  max_parallel_processes: 3  # Ajuster selon votre CPU
```

## Tests Rapides

### Test 1 : Vérifier qu'un modèle fonctionne

```powershell
# Télécharger un fichier audio de test court (1-2 min)
# puis lancer :
python scripts/BasicTestWhisper.py --input test.mp3 --model small
```

**Résultat attendu :** Transcription affichée + fichiers TXT/SRT créés

### Test 2 : Scanner vos fichiers audio

```powershell
python scripts/RunBatchWhisper.py --scan-only
```

**Résultat attendu :** Fichier `fichiers_audio.csv` créé avec la liste des fichiers

### Test 3 : Lancer un batch complet (sur 2-3 fichiers de test)

```powershell
python scripts/RunBatchWhisper.py
```

**Résultat attendu :** 
- Transcriptions générées dans les répertoires sources
- Fichiers de monitoring dans `output/reports/`

### Test 4 : Générer les rapports QoS

```powershell
python scripts/ComputeQoS.py
```

**Résultat attendu :**
- Graphiques PNG dans `output/reports/`
- Métriques de performance affichées

## Utilisation en Production

### Workflow Complet

```powershell
# 1. Scanner les fichiers audio TNT
python scripts/RunBatchWhisper.py --scan-only

# 2. Vérifier le CSV généré
type fichiers_audio.csv

# 3. Ajuster la config si nécessaire
notepad config/default_config.yaml

# 4. Lancer la transcription batch
python scripts/RunBatchWhisper.py

# 5. Générer les rapports QoS
python scripts/ComputeQoS.py

# 6. Consulter les résultats
explorer output/reports
```

### Configuration Recommandée par Modèle

**Modèle Small (rapide, qualité correcte)**
```yaml
whisper:
  model: "small"
hardware:
  max_parallel_processes: 6  # Plus de processus possibles
```
→ Throughput attendu : **5× temps réel**

**Modèle Medium (équilibré)**
```yaml
whisper:
  model: "medium"
hardware:
  max_parallel_processes: 3  # Moins de processus (+ RAM)
```
→ Throughput attendu : **1-2× temps réel**

**Modèle Large (haute qualité)**
```yaml
whisper:
  model: "large"
hardware:
  max_parallel_processes: 2  # Très consommateur en RAM
```
→ Throughput attendu : **0.5× temps réel**

## Dépannage

### Erreur : "Pas assez de RAM"

**Solution :**
1. Réduire `max_parallel_processes` dans la config
2. Utiliser un modèle plus petit (small au lieu de medium)
3. Fermer les applications consommatrices de RAM

### Erreur : "Modèle Whisper introuvable"

**Solution :**
```powershell
# Le modèle se télécharge automatiquement au 1er lancement
# Vérifier votre connexion internet
```

### Performance insuffisante

**Solutions :**
1. Vérifier que tous les cœurs CPU sont utilisés (voir monitoring)
2. Augmenter `max_parallel_processes` si RAM disponible
3. Vérifier qu'aucun autre processus lourd ne tourne

## Fichiers Générés

| Fichier | Localisation | Description |
|---------|--------------|-------------|
| Transcriptions TXT | À côté des MP3 | Texte brut de la transcription |
| Sous-titres SRT | À côté des MP3 | Sous-titres horodatés |
| fichiers_audio.csv | Racine | Liste des fichiers audio scannés |
| monitoring_cpu.csv | output/reports/ | Historique d'utilisation CPU |
| monitoring_memory.csv | output/reports/ | Historique d'utilisation RAM |
| cpu_usage.png | output/reports/ | Graphique CPU |
| memory_usage.png | output/reports/ | Graphique RAM |
| Tracker{N}.txt | trackers/ | Progression par processus |

## Commandes Utiles

```powershell
# Voir les logs en temps réel
Get-Content output/logs/stationtv.log -Wait

# Compter les fichiers transcrits
(Get-ChildItem -Recurse -Filter "*_transcript_*.txt").Count

# Afficher un résumé des métriques
python scripts/ComputeQoS.py --session-dir output/reports
```

## Support

**Documentation complète :** Voir [README.md](README.md)  
**Architecture détaillée :** Voir [walkthrough.md](C:\Users\Dorian\.gemini\antigravity\brain\1dc1ea13-d36c-42a9-8385-35a2f7ba2444\walkthrough.md)  
**Plan d'implémentation :** Voir [implementation_plan.md](C:\Users\Dorian\.gemini\antigravity\brain\1dc1ea13-d36c-42a9-8385-35a2f7ba2444\implementation_plan.md)
