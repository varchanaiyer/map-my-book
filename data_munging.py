import spacy
from spacy.matcher import Matcher
import fitz
from geopy.geocoders import Nominatim
import streamlit as st
import time
import importlib.util

def extract_text_from_pdf(pdf_file):
    """Extract text from uploaded PDF file"""
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_locations(text):
    """Extract location entities from text using spaCy with custom rules"""
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        st.error("Installing spaCy model...")
        import subprocess
        subprocess.check_call(["python", "-m", "spacy", "download", "en_core_web_sm"])
        nlp = spacy.load("en_core_web_sm")
    
    # Custom location patterns
    matcher = Matcher(nlp.vocab)
    # Add patterns for streets, districts, landmarks etc.
    patterns = [
        [{"ENT_TYPE": "GPE"}],  # Cities, countries, etc.
        [{"ENT_TYPE": "LOC"}],  # Non-GPE locations
        [{"LOWER": {"IN": ["street", "avenue", "road", "alley", "square", "bridge", "gate", "palace", "cathedral", "church"]}}, 
         {"IS_ALPHA": True, "OP": "+"}],
    ]
    matcher.add("LOCATION_PATTERNS", patterns)
    
    doc = nlp(text)
    locations = {}
    
    # Get locations from both NER and pattern matching
    for ent in doc.ents:
        if ent.label_ in ['GPE', 'LOC']:
            if ent.text not in locations:
                locations[ent.text] = 1
            else:
                locations[ent.text] += 1
                
    matches = matcher(doc)
    for match_id, start, end in matches:
        span = doc[start:end].text
        if span not in locations:
            locations[span] = 1
        else:
            locations[span] += 1
            
    return locations

def geocode_places(locations):
    """Geocode places using Nominatim"""
    geolocator = Nominatim(user_agent="book_mapper")
    geocoded_places = []
    
    total = len(locations)
    progress_bar = st.progress(0)
    
    for idx, (place, count) in enumerate(locations.items()):
        try:
            # Try with Berlin context first for places likely to be in Berlin
            location = geolocator.geocode(f"{place}, Berlin")
            if not location:
                # Try without context
                location = geolocator.geocode(place)
                
            if location:
                geocoded_places.append({
                    "name": place,
                    "lat": location.latitude,
                    "lon": location.longitude,
                    "count": count
                })
                st.success(f"📍 Found: {place} (mentioned {count} times)")
            time.sleep(1)  # Respect API rate limits
            progress_bar.progress((idx + 1) / total)
        except Exception as e:
            st.error(f"Error finding {place}: {str(e)}")
    
    return geocoded_places
