# Guide d'Utilisation - Comparaison de Transcriptions

## 📋 Script: CompareTranscriptions.py

Ce script compare deux transcriptions (Small vs Medium) et génère un rapport détaillé.

## 🚀 Utilisation

### Commande

```powershell
python scripts/CompareTranscriptions.py --small "chemin/vers/transcript_ws.txt" --medium "chemin/vers/transcript_wm.txt"
```

### Exemple Concret

```powershell
# Trouvez d'abord vos fichiers de transcription
# Ils sont dans: C:\Users\Dorian\Documents\Perso\PRI\StationTV\app\bdd\

python scripts/CompareTranscriptions.py `
  --small "C:/Users/Dorian/Documents/Perso/PRI/StationTV/app/bdd/Le témoignage dun surveillant du Louvre présent pendant le cambriolage du musée_transcript_ws.txt" `
  --medium "C:/Users/Dorian/Documents/Perso/PRI/StationTV/app/bdd/Le témoignage dun surveillant du Louvre présent pendant le cambriolage du musée_transcript_wm.txt"
```

## 📊 Résultats Générés

Le script génère 2 fichiers dans `test_output/` :

### 1. **transcription_comparison.html**
- Visualisation côte-à-côte des deux transcriptions
- **Vert** = ajouts dans Medium
- **Rouge** = suppressions dans Medium  
- **Jaune** = modifications
- **Ouvrir dans un navigateur** pour voir les différences

### 2. **transcription_comparison.txt**
- Résumé textuel
- Statistiques (nombre de mots, WER, erreurs)
- Exemples de différences
- Format texte simple

## 📈 Métriques Affichées

- **WER Relatif** : Pourcentage de différence entre Small et Medium
- **Substitutions** : Mots remplacés
- **Insertions** : Mots ajoutés dans Medium
- **Suppressions** : Mots manquants dans Medium
- **Total erreurs** : Somme des différences

## 💡 Interprétation

| WER | Interprétation |
|-----|----------------|
| < 5% | Très similaires ✅ |
| 5-10% | Similaires ✅ |
| 10-20% | Quelques différences ⚠️ |
| > 20% | Différences importantes ⚠️ |

**Note** : Un WER de 5-10% entre Small et Medium est normal et attendu. Medium devrait être plus précis.

## 🔍 Ce que le Script Fait

1. Charge les deux fichiers TXT
2. Compare mot par mot avec l'algorithme de Levenshtein
3. Calcule le WER (Medium comme référence)
4. Génère un rapport HTML coloré
5. Sauvegarde les statistiques dans un fichier texte

## ⚙️ Prochaines Étapes

Après avoir vu les différences :

1. **Ouvrir le HTML** dans un navigateur pour visualiser
2. **Analyser les zones de différence** :
   - Medium corrige-t-il des erreurs de Small ?
   - Quels types d'erreurs sont corrigées ?
   - Y a-t-il des cas où Small est meilleur ?
3. **Décider** : Small suffit-il ou Medium justifie-t-il le temps supplémentaire ?

## 📝 Exemple de Sortie Attendue

```
================================================================================
COMPARAISON TRANSCRIPTIONS - Small vs Medium
================================================================================

STATISTIQUES
========================================
Small  : 2134 caractères, 342 mots
Medium : 2156 caractères, 345 mots
Différence : 3 mots

WER RELATIF (Medium comme référence)
========================================
WER: 6.25%
Interprétation: Small diffère de Medium de 6.25%
✅ Similaires (5-10% de différence)

ANALYSE DES DIFFÉRENCES
========================================
Substitutions : 18
Insertions    : 2
Suppressions  : 1
Total erreurs : 21

✅ COMPARAISON TERMINÉE

Fichiers générés:
  - test_output/transcription_comparison.html
  - test_output/transcription_comparison.txt
```
