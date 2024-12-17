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
import os

# Page config
st.set_page_config(page_title="Book Location Mapper", layout="wide", page_icon="📚")

def install_spacy_model():
    try:
        # First try to load the model
        nlp = spacy.load('en_core_web_sm')
        return True
    except OSError:
        try:
            # If loading fails, try to install using pip instead of spacy download
            st.info("Installing required language model...")
            subprocess.run([
                sys.executable, 
                "-m", 
                "pip", 
                "install", 
                "--no-cache-dir",
                "en-core-web-sm@https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.0/en_core_web_sm-3.7.0-py3-none-any.whl"
            ], check=True, capture_output=True)
            st.success("Model installed successfully!")
            return True
        except subprocess.CalledProcessError as e:
            st.error(f"""Failed to install spaCy model. 
            If you're running this locally, try running:
            python -m spacy download en_core_web_sm
            from your command line first.
            
            Error: {str(e)}""")
            return False
        except Exception as e:
            st.error(f"Unexpected error during installation: {str(e)}")
            return False

# Create the split layout
col1, col2 = st.columns([1, 2])

with col1:
    st.title("📚 Book Location Mapper")
    st.markdown("---")
    
    # File upload section
    st.subheader("Upload Your Book")
    uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])
    
    if uploaded_file:
        st.info(f"File uploaded: {uploaded_file.name}")
        
        # Show analysis button
        if st.button("Analyze Locations"):
            # Install spacy model if needed
            if install_spacy_model():
                # Process the PDF
                with st.spinner('Extracting text from PDF...'):
                    try:
                        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                        text = ""
                        for page in doc:
                            text += page.get_text()
                        
                        # Extract locations
                        nlp = spacy.load('en_core_web_sm')
                        doc = nlp(text)
                        
                        locations = {}
                        for ent in doc.ents:
                            if ent.label_ in ['GPE', 'LOC', 'FAC']:
                                loc_name = ent.text.strip()
                                locations[loc_name] = locations.get(loc_name, 0) + 1
                        
                        # Store results in session state
                        st.session_state['locations'] = locations
                        st.success("✅ Analysis complete!")
                        
                    except Exception as e:
                        st.error(f"Error processing PDF: {str(e)}")
            else:
                st.error("Cannot proceed without the required language model.")
    
    # Display locations list if available
    if 'locations' in st.session_state:
        st.markdown("---")
        st.subheader("📍 Locations Found")
        locations_df = pd.DataFrame([
            {"Location": k, "Mentions": v} 
            for k, v in st.session_state['locations'].items()
        ]).sort_values("Mentions", ascending=False)
        
        st.dataframe(locations_df, use_container_width=True)

with col2:
    st.title("Location Map")
    
    # Show map
    if 'locations' in st.session_state:
        with st.spinner('Creating map...'):
            geolocator = Nominatim(user_agent="book-mapper")
            geocoded = []
            
            # Create a progress bar
            progress = st.progress(0)
            locations = st.session_state['locations']
            total = len(locations)
            
            for idx, (place, count) in enumerate(locations.items()):
                try:
                    # Try with general geocoding
                    location = geolocator.geocode(place)
                    if location:
                        geocoded.append({
                            "name": place,
                            "lat": location.latitude,
                            "lon": location.longitude,
                            "count": count
                        })
                    
                    progress.progress((idx + 1) / total)
                    time.sleep(1)  # Respect API limits
                    
                except Exception:
                    continue
            
            if geocoded:
                geo_df = pd.DataFrame(geocoded)
                
                fig = px.scatter_mapbox(
                    geo_df,
                    lat="lat",
                    lon="lon",
                    size="count",
                    hover_name="name",
                    hover_data={"count": True},
                    zoom=2,
                    mapbox_style="carto-positron",
                    title="Locations Mentioned in Book"
                )
                
                fig.update_layout(
                    height=700,
                    margin={"t": 0, "b": 0, "l": 0, "r": 0}
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No locations could be mapped.")
    else:
        # Show empty map or placeholder
        st.info("Upload a PDF and click 'Analyze Locations' to see the map.")
