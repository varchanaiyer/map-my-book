import spacy
import fitz
from geopy.geocoders import Nominatim
import streamlit as st
from collections import Counter
import time

@st.cache_resource
def load_nlp_model():
    """Load spaCy model for named entity recognition"""
    return spacy.load("en_core_web_sm")

def extract_text_from_pdf(pdf_file):
    """Extract text from uploaded PDF file"""
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_locations(text, nlp):
    """Extract location entities from text using spaCy"""
    doc = nlp(text)
    locations = [ent.text for ent in doc.ents if ent.label_ in ['GPE', 'LOC']]
    # Count frequency of locations
    location_counts = Counter(locations)
    return location_counts

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
                st.success(f"📍 Found: {place} (mentioned {count} times)")
            else:
                st.warning(f"⚠️ Could not find: {place}")
            time.sleep(1)  # Respect API limits
            progress_bar.progress((idx + 1) / total)
        except Exception as e:
            st.error(f"❌ Error finding {place}: {str(e)}")
    
    return geocoded_places
