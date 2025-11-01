# services/skill_extractor.py
import os
import pickle
import warnings
from typing import Dict, List, Optional
from requests.exceptions import ConnectionError, ReadTimeout

try:
    import spacy
    from keybert import KeyBERT
except Exception:
    spacy = None
    KeyBERT = None

ROOT = os.path.dirname(os.path.dirname(__file__))
DP_DIR = os.path.join(ROOT, "dp_model")
os.makedirs(DP_DIR, exist_ok=True)

MODEL_PATH = os.path.join(DP_DIR, "nlp_model.pkl")
KEYBERT_PATH = os.path.join(DP_DIR, "keybert_model.pkl")

# --------------------------
# Load spaCy
# --------------------------
if spacy is None:
    raise RuntimeError("spaCy not installed. Please pip install spacy and download en_core_web_sm.")
if not os.path.exists(MODEL_PATH):
    print("🔹 Loading spaCy model for first time (this may take a moment)...")
    nlp = spacy.load("en_core_web_sm")
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(nlp, f)
else:
    with open(MODEL_PATH, "rb") as f:
        nlp = pickle.load(f)

# --------------------------
# Load KeyBERT safely
# --------------------------
def safe_load_keybert():
    if KeyBERT is None:
        return None
    try:
        print("🔹 Initializing KeyBERT (may take time)...")
        model = KeyBERT()
        with open(KEYBERT_PATH, "wb") as f:
            pickle.dump(model, f)
        print("✅ KeyBERT loaded successfully.")
        return model
    except (ConnectionError, ReadTimeout, TimeoutError) as e:
        warnings.warn(f"⚠️ KeyBERT download failed: {e}\nFalling back to basic keyword extraction.")
        return None
    except Exception as e:
        warnings.warn(f"⚠️ Unexpected error loading KeyBERT: {e}")
        return None

if not os.path.exists(KEYBERT_PATH):
    kw_model = safe_load_keybert()
else:
    try:
        with open(KEYBERT_PATH, "rb") as f:
            kw_model = pickle.load(f)
    except Exception:
        kw_model = safe_load_keybert()

# --------------------------
# Keyword extraction logic
# --------------------------
def extract_keywords(text: str, use_semantic: bool = True) -> Dict[str, Optional[List[str]]]:
    if not text or not isinstance(text, str):
        return {"keywords": [], "location": None, "role": None}

    doc = nlp(text)
    keywords, location, role = [], None, None

    for ent in doc.ents:
        if ent.label_ in ["GPE", "LOC"]:
            location = ent.text
        elif ent.label_ in ["ORG", "PERSON", "WORK_OF_ART"] and not role:
            role = ent.text

    for token in doc:
        if token.pos_ in ["NOUN", "PROPN", "ADJ"] and not token.is_stop:
            keywords.append(token.lemma_.lower())

    if use_semantic and kw_model:
        try:
            semantic_keywords = [kw[0] for kw in kw_model.extract_keywords(text, top_n=5)]
            keywords.extend(semantic_keywords)
        except Exception as e:
            warnings.warn(f"Semantic extraction failed: {e}")

    keywords = list(set(k for k in keywords if len(k) > 2))

    if not role:
        for word in keywords:
            if any(job in word for job in ["developer", "engineer", "designer", "scientist", "manager", "analyst"]):
                role = word
                break

    return {"keywords": keywords, "location": location, "role": role}
