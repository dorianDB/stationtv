"""
Station TV - Compare Transcriptions
Compare deux transcriptions (Small vs Medium) et calcule un WER relatif
"""

import sys
from pathlib import Path
import difflib

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from qos.metrics import MetricsCalculator
from utils.logger import setup_logger

logger = setup_logger("CompareTranscriptions", level="INFO")


def load_transcription(file_path: str) -> str:
    """Charge une transcription depuis un fichier TXT."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        logger.error(f"Erreur lors du chargement de {file_path}: {str(e)}")
        return ""


def generate_html_diff(text1: str, text2: str, label1: str, label2: str, output_file: str):
    """Génère un rapport HTML avec les différences entre deux textes."""
    
    # Créer le diff HTML
    diff = difflib.HtmlDiff(wrapcolumn=80)
    
    lines1 = text1.split('\n')
    lines2 = text2.split('\n')
    
    html_content = diff.make_file(
        lines1, 
        lines2,
        fromdesc=label1,
        todesc=label2,
        context=True,
        numlines=3
    )
    
    # Sauvegarder
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"Rapport HTML généré: {output_file}")


def compare_transcriptions(file_small: str, file_medium: str):
    """
    Compare deux transcriptions et génère un rapport.
    
    Args:
        file_small: Chemin vers transcription Small
        file_medium: Chemin vers transcription Medium
    """
    logger.info("=" * 80)
    logger.info("COMPARAISON TRANSCRIPTIONS - Small vs Medium")
    logger.info("=" * 80)
    
    # Charger les transcriptions
    logger.info(f"\nChargement Small: {file_small}")
    text_small = load_transcription(file_small)
    
    logger.info(f"Chargement Medium: {file_medium}")
    text_medium = load_transcription(file_medium)
    
    if not text_small or not text_medium:
        logger.error("Impossible de charger les fichiers")
        return
    
    # Statistiques de base
    words_small = text_small.split()
    words_medium = text_medium.split()
    
    logger.info("\n" + "=" * 80)
    logger.info("STATISTIQUES")
    logger.info("=" * 80)
    logger.info(f"Small  : {len(text_small)} caractères, {len(words_small)} mots")
    logger.info(f"Medium : {len(text_medium)} caractères, {len(words_medium)} mots")
    logger.info(f"Différence : {abs(len(words_medium) - len(words_small))} mots")
    
    # Calculer le WER relatif (Medium comme référence)
    calc = MetricsCalculator()
    wer = calc.calculate_wer(text_medium, text_small)
    
    logger.info("\n" + "=" * 80)
    logger.info("WER RELATIF (Medium comme référence)")
    logger.info("=" * 80)
    logger.info(f"WER: {wer*100:.2f}%")
    logger.info(f"Interprétation: Small diffère de Medium de {wer*100:.2f}%")
    
    if wer < 0.05:
        logger.info("✅ Très similaires (< 5% de différence)")
    elif wer < 0.10:
        logger.info("✅ Similaires (5-10% de différence)")
    elif wer < 0.20:
        logger.info("⚠️ Quelques différences notables (10-20%)")
    else:
        logger.info("⚠️ Différences importantes (> 20%)")
    
    # Analyser les différences
    logger.info("\n" + "=" * 80)
    logger.info("ANALYSE DES DIFFÉRENCES")
    logger.info("=" * 80)
    
    # Comparer mot à mot
    matcher = difflib.SequenceMatcher(None, words_small, words_medium)
    
    substitutions = 0
    insertions = 0
    deletions = 0
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace':
            substitutions += max(i2 - i1, j2 - j1)
        elif tag == 'delete':
            deletions += i2 - i1
        elif tag == 'insert':
            insertions += j2 - j1
    
    logger.info(f"Substitutions : {substitutions}")
    logger.info(f"Insertions    : {insertions}")
    logger.info(f"Suppressions  : {deletions}")
    logger.info(f"Total erreurs : {substitutions + insertions + deletions}")
    
    # Générer rapport HTML
    output_html = "test_output/transcription_comparison.html"
    logger.info(f"\nGénération du rapport HTML...")
    generate_html_diff(
        text_small,
        text_medium,
        "Small (ws)",
        "Medium (wm)",
        output_html
    )
    
    # Rapport texte
    output_txt = "test_output/transcription_comparison.txt"
    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write("COMPARAISON TRANSCRIPTIONS - Small vs Medium\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Small  : {len(words_small)} mots\n")
        f.write(f"Medium : {len(words_medium)} mots\n\n")
        f.write(f"WER Relatif: {wer*100:.2f}%\n\n")
        f.write(f"Substitutions : {substitutions}\n")
        f.write(f"Insertions    : {insertions}\n")
        f.write(f"Suppressions  : {deletions}\n\n")
        f.write("=" * 80 + "\n")
        f.write("EXTRAIT DES DIFFÉRENCES (premiers 500 caractères)\n")
        f.write("=" * 80 + "\n\n")
        
        # Afficher quelques exemples de différences
        sample_count = 0
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != 'equal' and sample_count < 10:
                f.write(f"\n{tag.upper()}:\n")
                f.write(f"  Small  : {' '.join(words_small[i1:i2])}\n")
                f.write(f"  Medium : {' '.join(words_medium[j1:j2])}\n")
                sample_count += 1
    
    logger.info(f"Rapport texte généré: {output_txt}")
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ COMPARAISON TERMINÉE")
    logger.info("=" * 80)
    logger.info(f"\nFichiers générés:")
    logger.info(f"  - {output_html} (visualisation des différences)")
    logger.info(f"  - {output_txt} (résumé texte)")


def main():
    """Fonction principale."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Compare deux transcriptions Whisper (Small vs Medium)"
    )
    parser.add_argument(
        '--small',
        required=True,
        help="Chemin vers transcription Small (_ws.txt)"
    )
    parser.add_argument(
        '--medium',
        required=True,
        help="Chemin vers transcription Medium (_wm.txt)"
    )
    
    args = parser.parse_args()
    
    compare_transcriptions(args.small, args.medium)


if __name__ == "__main__":
    main()
