# Recommandations Configuration - Sessions Longues (588h audio)

## ⏱️ Intervalles de Monitoring Optimaux

### Pour Sessions Courtes (< 10h traitement)
```yaml
qos:
  monitoring_interval: 2  # Toutes les 2 secondes
```
- **Points de données** : ~18,000 pour 10h
- **Usage** : Tests, développement, petits lots

### Pour Sessions Moyennes (10-50h traitement)
```yaml
qos:
  monitoring_interval: 10  # Toutes les 10 secondes
```
- **Points de données** : ~18,000 pour 50h
- **Usage** : Transcriptions moyennes (~200-300h audio)

### Pour Sessions Longues (50h+ traitement) ⭐ RECOMMANDÉ
```yaml
qos:
  monitoring_interval: 30  # Toutes les 30 secondes
```
- **Points de données** : ~8,400 pour 70h
- **Usage** : Transcriptions massives (588h audio)
- **Avantages** :
  - ✅ Fichiers CSV plus petits (~500 KB au lieu de 15 MB)
  - ✅ Graphiques plus rapides à générer
  - ✅ Moins d'I/O disque
  - ✅ Tendances toujours visibles

### Pour Sessions Extra-Longues (> 100h traitement)
```yaml
qos:
  monitoring_interval: 60  # Toutes les minutes
```
- **Points de données** : ~6,000 pour 100h
- **Usage** : Campagnes très longues

---

## 📊 Impact sur les Fichiers

### Avec intervalle 2 secondes (70h de traitement)
```
Nombre de points : 70h × 3600s/h / 2s = 126,000 points
Taille CSV       : ~15-20 MB
Temps génération : ~20-30 secondes
```

### Avec intervalle 30 secondes (70h de traitement) ✅
```
Nombre de points : 70h × 3600s/h / 30s = 8,400 points
Taille CSV       : ~500 KB
Temps génération : ~2-3 secondes
```

**Réduction** : 93% moins de données, 10× plus rapide !

---

## 🎯 Configuration Actuelle (Station TV)

**Fichier** : `config/default_config.yaml`

```yaml
qos:
  enabled: true
  monitoring_interval: 30  # ✅ Optimisé pour 588h audio
  calculate_throughput: true
  calculate_wer: true
  save_detailed_metrics: true
```

---

## 💡 Recommandations par Volume

| Volume Audio | Durée Traitement | Intervalle Recommandé | Points de Données |
|--------------|------------------|----------------------|-------------------|
| < 50h | < 5h | 2s | ~9,000 |
| 50-200h | 5-20h | 5-10s | ~7,200-14,400 |
| 200-500h | 20-60h | 15-30s | ~7,200-14,400 |
| **588h** | **~70h** | **30s** ✅ | **~8,400** |
| > 1000h | > 120h | 60s | ~7,200 |

---

## ⚙️ Autres Optimisations pour Sessions Longues

### Réduire la fréquence de logging console
```yaml
logging:
  console_level: "WARNING"  # Au lieu de INFO
  file_level: "INFO"        # Garder INFO dans fichier
```

### Désactiver les métriques détaillées si non nécessaires
```yaml
qos:
  save_detailed_metrics: false  # Économise de l'espace
```

### Augmenter l'intervalle de sauvegarde des trackers
```python
# Dans RunBatchWhisper.py, sauvegarder toutes les 10 transcriptions
# Au lieu de chaque transcription
```

---

## 📈 Visualisation des Données

Avec **30 secondes d'intervalle**, les graphiques montrent toujours :
- ✅ Tendances globales CPU/RAM
- ✅ Pics d'utilisation
- ✅ Moyennes sur la session
- ✅ Zones de stress système

**Perte de précision** : Minimale pour sessions > 1h

---

## 🔧 Modification Dynamique (Avancé)

Si vous voulez **ajuster pendant l'exécution** :

```python
# Dans qos/monitor.py, modifier self.interval
monitor = SystemMonitor(interval=30)  # Au lieu de lire depuis config
```

Ou créer une config spéciale :

```yaml
# config/production_config.yaml (sessions longues)
qos:
  monitoring_interval: 30

# config/dev_config.yaml (tests courts)
qos:
  monitoring_interval: 2
```

Puis lancer avec :
```powershell
python scripts/RunBatchWhisper.py --config config/production_config.yaml
```

---

## ✅ Configuration Finale Recommandée

**Pour vos 588h sur la DELL :**

```yaml
qos:
  enabled: true
  monitoring_interval: 30          # ✅ Optimisé
  calculate_throughput: true
  calculate_wer: true
  save_detailed_metrics: true      # Ou false si espace limité
  
  thresholds:
    cpu_warning: 85
    cpu_critical: 95
    memory_warning: 80
    memory_critical: 90
```

**Résultat attendu** :
- 📊 Graphiques clairs et lisibles
- 💾 Fichiers CSV ~500 KB (faciles à partager)
- ⚡ Génération rapports QoS en < 5 secondes
- ✅ Toutes les informations importantes capturées
