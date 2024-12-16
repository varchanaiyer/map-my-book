# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import subprocess
import sys
import spacy
import fitz
from geopy.geocoders import Nominatim
import time

# Page config
st.set_page_config(page_title="Book Location Mapper", layout="wide", page_icon="📚")

def install_spacy_model():
    try:
        spacy.load('en_core_web_sm')
    except OSError:
        st.info("Installing required language model...")
        subprocess.check_call([
            f"{sys.executable}", "-m", "spacy", "download", "en_core_web_sm"
        ])
        st.success("Model installed successfully!")

def extract_text(pdf_file):
    """Extract text from uploaded PDF"""
    try:
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        st.error(f"Error extracting text: {str(e)}")
        return None

def extract_locations(text):
    """Extract locations using spaCy"""
    nlp = spacy.load('en_core_web_sm')
    doc = nlp(text)
    
    # Dictionary to store locations and their counts
    locations = {}
    
    # Custom location patterns to catch specific Berlin locations
    berlin_locations = [
        "Alexanderplatz", "Brandenburg Gate", "Unter den Linden",
        "Friedrichstraße", "Potsdamer Platz", "Karl-Marx-Allee",
        "Prenzlauer Berg", "Kreuzberg", "Mitte", "Pankow"
    ]
    
    # Process entities
    for ent in doc.ents:
        if ent.label_ in ['GPE', 'LOC', 'FAC']:
            loc_name = ent.text.strip()
            locations[loc_name] = locations.get(loc_name, 0) + 1
            
    # Add Berlin-specific locations
    for loc in berlin_locations:
        if loc.lower() in text.lower():
            locations[loc] = text.lower().count(loc.lower())
    
    return locations

def geocode_locations(locations):
    """Geocode locations"""
    geolocator = Nominatim(user_agent="book-mapper")
    geocoded = []
    
    progress = st.progress(0)
    total = len(locations)
    
    for idx, (place, count) in enumerate(locations.items()):
        try:
            # Try with Berlin context first
            location = geolocator.geocode(f"{place}, Berlin, Germany")
            if not location:
                location = geolocator.geocode(place)
                
            if location:
                geocoded.append({
                    "name": place,
                    "lat": location.latitude,
                    "lon": location.longitude,
                    "count": count
                })
                st.success(f"📍 Found: {place} (mentioned {count} times)")
            
            progress.progress((idx + 1) / total)
            time.sleep(1)  # Respect API limits
            
        except Exception as e:
            st.warning(f"Could not geocode {place}: {e}")
            continue
            
    return geocoded

def create_map(locations_df):
    """Create the map visualization"""
    if not locations_df.empty:
        fig = px.scatter_mapbox(
            locations_df,
            lat="lat",
            lon="lon",
            size="count",
            hover_name="name",
            hover_data={"count": True},
            zoom=11,
            center={"lat": 52.52, "lon": 13.405},  # Center on Berlin
            mapbox_style="carto-positron",
            title="Locations Mentioned in Book"
        )
        
        fig.update_layout(height=600, margin={"t": 0, "b": 0, "l": 0, "r": 0})
        return fig
    return None

# Main app
st.title("📚 Book Location Mapper")

# Check and install spacy model if needed
install_spacy_model()

# File upload
uploaded_file = st.file_uploader("Upload PDF Book", type=['pdf'])

if uploaded_file:
    # Process the PDF
    with st.spinner('Extracting text from PDF...'):
        text = extract_text(uploaded_file)
        if text:
            st.success("✅ Text extracted successfully!")
            
            # Find locations
            with st.spinner('Finding locations...'):
                locations = extract_locations(text)
                
                if locations:
                    # Display locations found
                    st.subheader("📍 Locations Found")
                    locations_df = pd.DataFrame([
                        {"name": k, "count": v} 
                        for k, v in locations.items()
                    ]).sort_values("count", ascending=False)
                    
                    st.dataframe(locations_df)
                    
                    # Geocode locations
                    with st.spinner('Creating map...'):
                        geocoded = geocode_locations(locations)
                        if geocoded:
                            geo_df = pd.DataFrame(geocoded)
                            
                            # Create and display map
                            fig = create_map(geo_df)
                            if fig:
                                st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.warning("Could not geocode any locations.")
                else:
                    st.info("No locations found in the text.")
else:
    st.info("Please upload a PDF book to analyze.")
