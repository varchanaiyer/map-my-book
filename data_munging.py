import spacy
import fitz
from geopy.geocoders import Nominatim
import streamlit as st
from collections import Counter
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
    """Extract location entities from text using spaCy"""
    # Check if spacy is installed
    if importlib.util.find_spec("spacy") is None:
        st.error("spaCy is not installed. Installing required packages...")
        import subprocess
        subprocess.check_call(["pip", "install", "spacy"])
        subprocess.check_call(["python", "-m", "spacy", "download", "en_core_web_sm"])
        
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        st.error("Downloading spaCy model...")
        import subprocess
        subprocess.check_call(["python", "-m", "spacy", "download", "en_core_web_sm"])
        nlp = spacy.load("en_core_web_sm")
    
    doc = nlp(text)
    locations = [ent.text for ent in doc.ents if ent.label_ in ['GPE', 'LOC']]
    return Counter(locations)

def geocode_places(locations):
    """Geocode places using Nominatim"""
    geolocator = Nominatim(user_agent="book_mapper")
    geocoded_places = []
    
    total = len(locations)
    progress_bar = st.progress(0)
    
    for idx, (place, count) in enumerate(locations.items()):
        try:
            location = geolocator.geocode(place)
            if location:
                geocoded_places.append({
                    "name": place,
                    "lat": location.latitude,
                    "lon": location.longitude,
                    "count": count
                })
                st.success(f"📍 {place}: {count} mentions")
            time.sleep(1)
            progress_bar.progress((idx + 1) / total)
        except Exception as e:
            st.error(f"Error finding {place}: {str(e)}")
    
    return geocoded_places
