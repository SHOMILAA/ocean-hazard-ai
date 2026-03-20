from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import spacy

# Load spaCy NLP model, fallback safely if not downloaded
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # We will simulate if model isn't downloaded yet to prevent server crash
    nlp = None

# Synthetic training data for fake vs real news classification
corpus = [
    "A massive tsunami is approaching the coast, evacuate immediately!",
    "Breaking: Severe cyclone hitting the eastern shores tonight.",
    "Oil spill reported near the harbor, marine life in danger.",
    "Just heard there's a storm but the sky is clear, probably fake.",
    "Don't worry, the flood warning was a hoax.",
    "High waves taking over the beach, be careful everyone.",
    "There are aliens in the ocean causing huge waves.",
    "Water levels are normal, no floods here.",
    "Tsunami warning cancelled, it was a false alarm.",
    "The cyclone is destroying homes, real footage here."
]
labels = [1, 1, 1, 0, 0, 1, 0, 0, 0, 1]  # 1 for Real, 0 for Fake

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(corpus)
model = LogisticRegression()
model.fit(X, labels)

HAZARD_KEYWORDS = ['tsunami', 'cyclone', 'oil spill', 'storm', 'flood', 'high waves']

def analyze_text(text):
    if not text.strip():
        return {
            'is_real': True,
            'confidence': 1.0,
            'detected_hazards': [],
            'location': None,
            'explanation': 'No text provided for analysis.'
        }
        
    text_lower = text.lower()
    
    # 1. Fake or Real Classification
    vec = vectorizer.transform([text])
    pred = model.predict(vec)[0]
    prob = model.predict_proba(vec)[0][pred]
    is_real = bool(pred == 1)
    
    # 2. Extract Hazards
    detected_hazards = [kw for kw in HAZARD_KEYWORDS if kw in text_lower]
    
    # 3. Location Extraction (NER)
    detected_location = None
    if nlp is not None:
        doc = nlp(text)
        locations = [ent.text for ent in doc.ents if ent.label_ in ['GPE', 'LOC', 'FAC']]
        if locations:
            detected_location = locations[0]  # Just take the first valid location found
    else:
        # Fallback keyword logic if spacy model is missing
        if "california" in text_lower: detected_location = "California"
        elif "japan" in text_lower: detected_location = "Japan"
        elif "florida" in text_lower: detected_location = "Florida"
    
    # 4. Explainable AI Reasoning Construction
    reasons = []
    if detected_hazards:
        reasons.append(f"Hazard keywords detected: {', '.join(detected_hazards)}")
    else:
        reasons.append("No common hazard keywords found in text.")
        
    if is_real:
        reasons.append("Text semantics align with credible hazard reporting (No blatant misinformation signals).")
    else:
        reasons.append("Text semantics show patterns typical of rumors, hoaxes, or false alarms.")
        
    if detected_location:
        reasons.append(f"Location entity named '{detected_location}' identified.")

    return {
        'is_real': is_real,
        'confidence': float(prob),
        'detected_hazards': detected_hazards,
        'location': detected_location,
        'explanation': reasons
    }
