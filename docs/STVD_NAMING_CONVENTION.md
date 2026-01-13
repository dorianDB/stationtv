# Convention de Nommage STVD-MNER

## 📝 Format des Fichiers de Transcription

Le système utilise maintenant la **convention STVD-MNER** pour nommer les fichiers de transcription.

### Format Standard STVD-MNER

```
{timestamp}_transcript_{model_suffix}.{extension}
```

**Composants** :
- `timestamp` : `YYYYMMDD_HH_MM` (date et heure de l'événement/transcription)
- `model_suffix` : `{wt, wb, ws, wm, wl}` selon le modèle Whisper
- `extension` : `{txt, srt}`

---

## 🔤 Suffixes des Modèles

| Modèle Whisper | Suffixe STVD-MNER | Description |
|----------------|-------------------|-------------|
| tiny | `wt` | Tiny model |
| base | `wb` | Base model |
| small | `ws` | Small model |
| **medium** | **`wm`** | Medium model ⭐ |
| large | `wl` | Large model |

---

## 📋 Exemples de Noms de Fichiers

### Fichiers générés

```
20250109_12_30_transcript_ws.txt       # Transcription Small (TXT)
20250109_12_30_transcript_st_ws.srt    # Sous-titres Small (SRT)
20250109_12_30_transcript_wm.txt       # Transcription Medium (TXT)
20250109_12_30_transcript_st_wm.srt    # Sous-titres Medium (SRT)
```

### Fichiers originaux (avec timestamp)
```
20250109_12_30_video.mp4    → 20250109_12_30_transcript_ws.txt
20250109_14_00_audio.mp4    → 20250109_14_00_transcript_ws.txt
```

### Fichiers originaux (sans timestamp)
```
interview.mp3               → 20250109_23_55_transcript_ws.txt
emission_france2.mp4        → 20250109_23_55_transcript_ws.txt
```

**Note** : Si le fichier original n'a pas de timestamp, le système utilise l'**heure de transcription**.

---

## 🔄 Détection Automatique du Timestamp

Le système détecte automatiquement les timestamps dans les noms de fichiers :

```python
# Regex de détection
timestamp_pattern = r'^(\d{8}_\d{2}_\d{2})'  # YYYYMMDD_HH_MM

# Si détecté → utilise le timestamp du fichier
# Si absent → génère nouveau timestamp
```

---

## 📂 Structure STVD-MNER Complète

### Organisation Recommandée

```
CX/                              # Chaîne TV (France2, TF1, etc.)
├── collection_name/             # Nom de collection
│   ├── NEs_list_imdb.json
│   ├── NEs_list_stvdkgall.json
│   ├── NEs_list_stvdkgstr.json
│   └── 20250109/                # Jour (YYYYMMDD)
│       ├── 20250109_09_55_epg.csv
│       ├── 20250109_09_55_video.mp4
│       ├── 20250109_09_55_audio.mp4
│       ├── 20250109_09_55_transcript_ws.txt      ← Généré
│       ├── 20250109_09_55_transcript_st_ws.srt   ← Généré
│       ├── 20250109_14_30_video.mp4
│       ├── 20250109_14_30_audio.mp4
│       ├── 20250109_14_30_transcript_wm.txt      ← Généré
│       └── 20250109_14_30_transcript_st_wm.srt   ← Généré
```

---

## ⚙️ Configuration

### Format des Sorties

Dans `config/default_config.yaml` :

```yaml
whisper:
  model: "medium"  # Génère suffixe "wm"
  
  output_formats:
    txt: true      # Fichiers .txt
    srt: true      # Fichiers .srt avec sous-titres
    csv: false     # (Non-STVD-MNER)
    json: false    # (Non-STVD-MNER)
```

---

## 🔍 Comportement Détaillé

### Cas 1 : Fichier avec Timestamp STVD-MNER
```
Entrée  : 20250109_12_30_audio.mp4
Sortie  : 20250109_12_30_transcript_ws.txt
          20250109_12_30_transcript_st_ws.srt
```
✅ **Timestamp préservé**

### Cas 2 : Fichier sans Timestamp
```
Entrée  : interview_macron.mp3
Sortie  : 20250109_23_55_transcript_ws.txt  (heure de transcription)
          20250109_23_55_transcript_st_ws.srt
```
✅ **Timestamp généré automatiquement**

### Cas 3 : Fichier avec autre format de date
```
Entrée  : 2025-01-09_emission.mp4
Sortie  : 20250109_23_55_transcript_ws.txt  (converti + heure ajoutée)
          20250109_23_55_transcript_st_ws.srt
```
✅ **Timestamp normalisé**

---

## 📊 Compatibilité STVD-MNER

### Formats Générés

| Format | Extension | Conforme STVD-MNER | Généré |
|--------|-----------|-------------------|--------|
| Texte brut | `.txt` | ✅ Oui | Toujours |
| Sous-titres | `.srt` | ✅ Oui | Si activé |
| CSV tabulaire | `.csv` | ❌ Extension | Si activé |
| JSON métadonnées | `.json` | ❌ Extension | Si activé |

**Recommandation** : Désactiver CSV et JSON pour compatibilité 100% STVD-MNER.

---

## ✅ Avantages de la Convention

1. **Compatibilité** : Fichiers directement utilisables dans STVD-MNER
2. **Traçabilité** : Timestamp indique quand l'événement a été diffusé/transcrit
3. **Organisation** : Tri chronologique automatique
4. **Standards** : Conforme aux spécifications STVD-MNER
5. **Multimodèle** : Suffixe identifie le modèle Whisper utilisé

---

## 🔄 Migration depuis Ancien Format

**Ancien format** :
```
fichier_transcript_ws.txt
fichier_transcript_st_ws.srt
```

**Nouveau format** (STVD-MNER) :
```
20250109_23_55_transcript_ws.txt
20250109_23_55_transcript_st_ws.srt
```

Les anciens fichiers restent valides, mais **nouveaux fichiers utilisent le format STVD-MNER**.

---

## 📝 Notes Techniques

### Regex de Détection
```python
r'^(\d{8}_\d{2}_\d{2})'  # Match: 20250109_12_30
```

### Génération Timestamp
```python
datetime.now().strftime("%Y%m%d_%H_%M")
# Exemple: "20250109_23_55"
```

### Suffixes Modèles
```python
{
    'tiny': 'wt',
    'base': 'wb', 
    'small': 'ws',
    'medium': 'wm',
    'large': 'wl'
}
```

---

## 🎯 Conclusion

Le système Station TV est maintenant **100% compatible** avec la convention de nommage STVD-MNER, permettant une intégration directe avec le jeu de données et les outils de la plateforme STVD.

**Format** : `{YYYYMMDD_HH_MM}_transcript_{wX}.{txt|srt}` ✅
