# Guide - Monitoring de Consommation Énergétique

## ⚡ Nouvelles Fonctionnalités Ajoutées

### Métriques Énergétiques

Le système monitore maintenant :
1. **Puissance instantanée** (Watts)
2. **Énergie cumulée** (kWh)
3. **Coût électricité** (€)
4. **Impact carbone** (kg CO2)

---

## 📊 Fichiers Générés

Après une session de transcription, vous trouverez dans `test_output/reports/` :

### Nouveaux fichiers
- `monitoring_power.csv` - Données brutes (Timestamp, Power_W, Energy_kWh, Cost_EUR, Carbon_kgCO2)
- `power_usage.png` - Graphique haute résolution (300 DPI)

### Fichiers existants
- `monitoring_cpu.csv` + `cpu_usage.png`
- `monitoring_memory.csv` + `memory_usage.png`

---

## ⚙️ Configuration

### Dans `config/default_config.yaml`

```yaml
qos:
  power:
    enabled: true              # Activer/désactiver
    tdp_watts: null            # null = auto-détection, ou valeur manuelle (ex: 125)
    cost_per_kwh: 0.18         # Tarif électricité en €/kWh
    carbon_kg_per_kwh: 0.1     # Intensité carbone (France: 0.1, Allemagne: 0.4)
```

### Auto-détection TDP

Si `tdp_watts: null`, le système estime le TDP selon le nombre de cœurs :
- 1-2 cœurs : 15W (mobile)
- 3-4 cœurs : 35W (desktop entry)
- 5-8 cœurs : 65W (desktop mainstream)
- 9-12 cœurs : 95W (desktop high-end)
- 13-18 cœurs : 125W (workstation - **Xeon W-2295**)
- 19-32 cœurs : 165W (server)

**Pour la Dell Precision 5820** : Auto-détecté à **125W** ✅

---

## 📈 Méthodes de Mesure

### Option 1 : RAPL (Intel) - Si disponible
- Mesure **précise** de la consommation CPU
- Utilise les compteurs matériels Intel
- Disponible sur Linux avec `pyRAPL`
- Précision : ±5%

### Option 2 : Estimation CPU (Par défaut)
- Estimé via utilisation CPU
- Formule : `P = TDP × (CPU% / 100) + P_idle`
- Disponible sur **Windows et Linux**
- Précision : ±20-30%

**Sur Windows** : Utilise l'estimation (RAPL non disponible)

---

## 💰 Calcul des Coûts

### Formule
```
Énergie (kWh) = Puissance (W) × Temps (h) / 1000
Coût (€) = Énergie (kWh) × Tarif (€/kWh)
```

### Exemple pour 70h de traitement (588h audio)
```
Puissance moyenne : 95W (Xeon W-2295 à 76% CPU)
Énergie : 95W × 70h / 1000 = 6.65 kWh
Coût : 6.65 kWh × 0.18 €/kWh = 1.20 €
Impact CO2 : 6.65 kWh × 0.1 kg/kWh = 0.67 kg CO2
```

**Pour 588h audio** : ~1.20€ d'électricité ⚡

---

## 🌍 Impact Carbone

### Facteurs d'émission par pays (kg CO2/kWh)

| Pays | Intensité | Mix énergétique |
|------|-----------|-----------------|
| **France** | 0.1 | Nucléaire (70%) |
| Suisse | 0.03 | Hydraulique |
| Allemagne | 0.4 | Charbon/renouvelable |
| Pologne | 0.8 | Charbon |
| Moyenne UE | 0.3 | Mix |

**Configurez selon votre pays** dans `carbon_kg_per_kwh`

---

## 📊 Graphique Généré

### power_usage.png contient 2 sous-graphiques :

**1. Puissance Instantanée**
- Courbe orange : Watts en temps réel
- Ligne bleue : Moyenne de session

**2. Énergie & Coût Cumulés**
- Courbe verte : kWh (axe gauche)
- Courbe rouge : € (axe droit)
- Annotation finale : Total kWh, €, kg CO2

### Résolution
- **300 DPI** (impression qualité)
- Format PNG

---

## 🚀 Utilisation

### Automatique
Le monitoring énergétique démarre automatiquement avec `RUN_PIPELINE.bat` ou `RunBatchWhisper.py`

### Manuel
```powershell
# Lancer transcription avec monitoring complet
python scripts/RunBatchWhisper.py

# Générer graphs après coup
python scripts/ComputeQoS.py --session-dir test_output/reports
```

### Désactiver
```yaml
qos:
  power:
    enabled: false  # Monitoring énergétique désactivé
```

---

## 📝 Bilan Énergétique dans les Logs

À la fin de la session, vous verrez :
```
============================================================
BILAN ÉNERGÉTIQUE
============================================================
Durée session    : 70.00 heures
Énergie totale   : 6.650 kWh
Puissance moyenne: 95.0 W
Coût électricité : 1.20 €
Impact carbone   : 0.67 kg CO2
============================================================
```

---

## 🎯 Cas d'Usage

### Comparaison Modèles
- **Small** : Plus rapide → Moins d'énergie totale
- **Medium** : Plus lent → Plus d'énergie totale
- Mais **Medium** peut être plus efficient par heure audio traitée

### Optimisation Coûts
- Identifier les pics de consommation
- Ajuster `max_parallel_processes` pour équilibrer vitesse/consommation
- Planifier les sessions pendant les heures creuses (tarif réduit)

### Bilan Environnemental
- Rapport RSE (Responsabilité Sociétale)
- Carbon footprint de l'infrastructure IA
- Comparaison avec solutions cloud (AWS Transcribe, etc.)

---

## 🔧 Dépendances

### Optionnel (pour RAPL sur Linux)
```bash
pip install pyRAPL
```

### Requis (déjà installé)
```bash
pip install psutil  # Détection CPU, RAM
```

---

## ✅ Résumé

**Nouvelles métriques** :
- ⚡ Puissance instantanée
- 🔋 Énergie cumulée
- 💰 Coût électricité
- 🌍 Impact carbone

**Configuration** : `config/default_config.yaml` section `qos.power`

**Graphique** : `test_output/reports/power_usage.png`

**Automatique** : Intégré dans le pipeline existant

Prêt pour vos bilans énergétiques ! 🚀
