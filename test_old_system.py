"""
Test de Comparaison - Ancien vs Nouveau Système
Lance une transcription avec l'ancien WhisperTranscriptor (simplifié) pour comparer les performances
"""

import time
import whisper
import os

# Configuration
audio_file = "C:/Users/Dorian/Documents/Perso/PRI/StationTV/app/bdd/Le témoignage dun surveillant du Louvre présent pendant le cambriolage du musée.mp3"
model_name = "small"

print("=" * 80)
print("TEST ANCIEN SYSTÈME (WhisperTranscriptor - Version Simplifiée)")
print("=" * 80)
print(f"Fichier: {os.path.basename(audio_file)}")
print(f"Modèle: {model_name}")
print()

# Charger le modèle
print("Chargement du modèle Whisper...")
model = whisper.load_model(model_name)

# Lancer la transcription
print("Début de la transcription...")
start_time = time.time()

result = model.transcribe(audio_file, language="fr", word_timestamps=True)

end_time = time.time()
execution_time = end_time - start_time

print()
print("=" * 80)
print("RÉSULTATS")
print("=" * 80)
print(f"Temps de traitement: {execution_time:.2f} secondes")
print(f"Durée audio: ~314 secondes")
print(f"Throughput: {314/execution_time:.2f}× temps réel")  
print()
print(f"Texte transcrit (premiers 200 caractères):")
print(result["text"][:200] + "...")
print()
print("=" * 80)

# Écrire le résultat dans un fichier pour comparaison
with open("test_output/OLD_SYSTEM_RESULT.txt", "w", encoding="utf-8") as f:
    f.write(f"ANCIEN SYSTÈME - WhisperTranscriptor\n")
    f.write(f"=" * 80 + "\n\n")
    f.write(f"Temps de traitement: {execution_time:.2f} secondes\n")
    f.write(f"Throughput: {314/execution_time:.2f}× temps réel\n\n")
    f.write(f"Transcription:\n{result['text']}\n")

print(f"✅ Résultat sauvegardé dans: test_output/OLD_SYSTEM_RESULT.txt")
