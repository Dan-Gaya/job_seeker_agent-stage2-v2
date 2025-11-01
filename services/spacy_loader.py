import spacy

# Load small English NLP model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # If model isn't installed, install automatically
    import subprocess, sys
    subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

def extract_spacy_keywords(text, limit=10):
    """
    Extracts simple keywords based on nouns and proper-nouns
    """
    doc = nlp(text)
    keywords = {token.text.lower() for token in doc if token.pos_ in ["NOUN", "PROPN"]}
    return list(keywords)[:limit]
