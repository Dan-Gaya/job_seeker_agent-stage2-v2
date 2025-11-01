from keybert import KeyBERT
from sentence_transformers import SentenceTransformer

# Load sentence-BERT model for KeyBERT
model = SentenceTransformer("all-MiniLM-L6-v2")
kw_model = KeyBERT(model=model)

def extract_keywords(text, top_n=5):
    keywords = kw_model.extract_keywords(
        text,
        keyphrase_ngram_range=(1,2),
        stop_words='english',
        top_n=top_n
    )
    return [kw for kw, score in keywords]
