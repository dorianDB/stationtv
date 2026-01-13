# Évaluation de la Qualité sans Texte de Référence - Station TV

## 🎯 Le Problème

**WER classique** nécessite un texte de référence (vérité terrain) :
```
WER = Erreurs / Nombre de mots de référence
```

❌ Pas de référence humaine disponible pour 588h d'audio

---

## ✅ Solutions Alternatives

### 1. Échantillonnage Manuel (Recommandé)

**Méthode :**
- Sélectionner **10-20 échantillons** de 1-2 minutes chacun
- Transcrire **manuellement** ces courts extraits (référence)
- Comparer avec transcriptions Whisper
- Calculer le WER sur ces échantillons

**Avantages :**
- ✅ WER précis sur échantillon représentatif
- ✅ ~2-3h de travail manuel pour 20 échantillons
- ✅ Permet de comparer Small vs Medium

**Script fourni :**
```python
# Utiliser qos/metrics.py
from qos.metrics import MetricsCalculator

calc = MetricsCalculator()
wer = calc.calculate_wer(
    reference_text="texte manuel",
    hypothesis_text="transcription whisper"
)
print(f"WER: {wer*100:.2f}%")
```

---

### 2. Comparaison Small vs Medium (WER Relatif)

**Méthode :**
- Transcrire le **même fichier** avec Small ET Medium
- Comparer les deux transcriptions
- Les différences indiquent où Medium améliore

**Avantages :**
- ✅ Pas de travail manuel
- ✅ Identifie les zones d'amélioration
- ⚠️ Ne donne pas un WER absolu

**Pour votre fichier test :**
```
Small  : fichier_transcript_ws.txt
Medium : fichier_transcript_wm.txt
```

Vous pouvez les comparer visuellement ou avec un script de diff.

---

### 3. Scores de Confiance Whisper

**Méthode :**
- Whisper fournit un **score de confiance** pour chaque segment
- Les segments avec confiance < 0.6 sont suspects
- Réviser manuellement ces segments

**Implémentation :**

Le système peut être modifié pour extraire ces scores :

```python
# Dans core/transcription.py, modifier transcribe_on_specific_cores()
result = model.transcribe(audio_path, language=self.language)

# Accéder aux scores de confiance
for segment in result["segments"]:
    if segment.get("confidence", 1.0) < 0.6:
        print(f"⚠️ Segment suspect: {segment['text']}")
```

**Avantages :**
- ✅ Automatique
- ✅ Identifie zones problématiques
- ⚠️ Ne donne pas un WER précis

---

### 4. Métriques Linguistiques Automatiques

**Perplexité** : Mesure la "fluidité" linguistique
- Texte fluide = bon
- Texte incohérent = erreurs probables

**Cohérence sémantique** : 
- Vérifier la cohérence du contexte
- Détecter phrases sans sens

**Outils disponibles :**
- `language-tool-python` (corrections grammaticales)
- `spacy` (analyse linguistique)

---

### 5. Validation Croisée (Cross-Model)

**Méthode :**
- Utiliser 2-3 modèles différents (small, medium, large)
- Comparer leurs transcriptions
- Consensus = probable correct
- Divergence = zone d'erreur possible

**Exemple :**
```
Small  : "le chat mange"
Medium : "le chat mange"  ✅ Consensus
Large  : "le chat mange"

vs

Small  : "il va à la maison"
Medium : "il va à la mairie"  ⚠️ Divergence
Large  : "il va à la mairie"  → Probable = "mairie"
```

---

## 🎯 Recommandation pour Station TV

### Approche Hybride (Optimal)

**Étape 1 - Échantillonnage (1 fois)**
```
1. Sélectionner 20 extraits de 1 min (variété de chaînes/émissions)
2. Transcrire manuellement (2-3h de travail)
3. Calculer WER réel sur ces échantillons
4. Benchmarker Small vs Medium
```

**Résultats attendus :**
- WER Small : ~8-12% (segments clairs)
- WER Medium : ~5-8% (segments clairs)
- WER sur audio bruité : +5-10%

**Étape 2 - Production (Quotidien)**
```
1. Utiliser scores de confiance Whisper
2. Flaguer segments < 0.6 de confiance
3. Révision manuelle spot-check (5% du contenu)
```

---

## 📊 WER Attendus (Littérature)

Basé sur les benchmarks Whisper OpenAI :

| Modèle | WER (Audio Propre) | WER (Audio Bruité) |
|--------|-------------------|-------------------|
| **Tiny** | 15-20% | 25-35% |
| **Small** | 8-12% | 15-22% |
| **Medium** | 5-8% | 10-15% |
| **Large** | 3-5% | 7-12% |

**Pour TNT française :**
- Qualité audio : Généralement bonne (studio)
- WER attendu Medium : **~6-8%** ✅
- WER attendu Small : **~10-12%**

---

## 💡 Solution Pratique Immédiate

### Script de Comparaison Small vs Medium

Je peux créer un script qui :
1. Lit les deux transcriptions (small et medium)
2. Compare mot à mot
3. Calcule un "WER relatif"
4. Génère un rapport HTML avec différences colorées

**Voulez-vous que je crée ce script ?**

---

## 📝 Synthèse

**Sans texte de référence :**

✅ **Faisable** : Échantillonnage manuel (20 extraits × 1 min)
- Effort : 2-3h de travail
- Résultat : WER précis sur échantillon représentatif

✅ **Automatique** : Comparaison Small vs Medium
- Effort : 0 (déjà fait)
- Résultat : Différences qualitatives

✅ **Continu** : Scores de confiance Whisper
- Effort : Intégrer dans le code
- Résultat : Détection automatique des zones suspectes

**Ma recommandation** : Commencer par comparer visuellement vos deux transcriptions existantes (small vs medium) pour voir la différence de qualité, puis faire un échantillonnage manuel si vous voulez un WER précis.
