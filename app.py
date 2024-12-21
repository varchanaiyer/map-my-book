import streamlit as st
import sys
import re

# First, ensure numpy is loaded
try:
    import numpy
except ImportError:
    st.error("Required dependencies not found. Please check your installation.")
    st.stop()

import pandas as pd
import plotly.express as px
import fitz
from geopy.geocoders import Nominatim
import time

# Page config
st.set_page_config(page_title="Book Location Mapper", layout="wide", page_icon="📚")

def clear_session_state():
    """Clear all relevant session state variables"""
    keys_to_clear = ['locations', 'tour_stops', 'previous_file', 'text_content']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

@st.cache_resource
def load_nlp_model():
    """Load spaCy model with caching and proper error handling"""
    try:
        import spacy
        import en_core_web_sm
        return en_core_web_sm.load()
    except ImportError as e:
        st.error(f"""
        Unable to load required dependencies. Error: {str(e)}
        Please check your deployment configuration and ensure all requirements are properly installed.
        """)
        st.stop()
    except Exception as e:
        st.error(f"Unexpected error loading NLP model: {str(e)}")
        st.stop()


def extract_context(text, location, window_size=200):
    """Extract context around location mentions"""
    contexts = []
    location_pattern = re.compile(r'\b' + re.escape(location) + r'\b', re.IGNORECASE)
    
    for match in location_pattern.finditer(text):
        start = max(0, match.start() - window_size)
        end = min(len(text), match.end() + window_size)
        
        # Get the context
        context = text[start:end]
        
        # Clean up the context
        context = context.replace('\n', ' ')
        context = re.sub(r'\s+', ' ', context)
        context = context.strip()
        
        # Add ellipsis if we're not at the start/end of the text
        if start > 0:
            context = '...' + context
        if end < len(text):
            context = context + '...'
            
        contexts.append(context)
    
    return contexts

def create_tour_guide(text, locations):
    """Create a tour guide from the extracted locations and their contexts"""
    tour_stops = {}
    
    for location, count in locations.items():
        contexts = extract_context(text, location)
        if contexts:
            # Keep only unique contexts
            unique_contexts = list(set(contexts))
            tour_stops[location] = {
                'mentions': count,
                'contexts': unique_contexts[:3]  # Limit to 3 most relevant contexts
            }
    
    return tour_stops
# Create the split layout
col1, col2 = st.columns([1, 2])

# Load the model at startup
nlp = load_nlp_model()

with col1:
    st.title("📚 Book Location Mapper")
    st.markdown("---")
    
    # File upload section
    st.subheader("Upload Your Book")
    uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])
    
    # Clear state if a new file is uploaded
    if uploaded_file:
        if 'current_file' not in st.session_state or st.session_state['current_file'] != uploaded_file.name:
            clear_session_state()
            st.session_state['current_file'] = uploaded_file.name
        
        st.info(f"File uploaded: {uploaded_file.name}")
        
        # Show analysis button
        if st.button("Create Literary Tour"):
            with st.spinner('Creating your literary tour guide...'):
                try:
                    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                    text = ""
                    for page in doc:
                        text += page.get_text()
                        page.close()  # Close each page after reading
                    doc.close()  # Close the document

                    # Process text in chunks for NLP
                    chunk_size = 100000  # Process 100KB at a time
                    locations = {}

                    for i in range(0, len(text), chunk_size):
                        chunk = text[i:i + chunk_size]
                        doc = nlp(chunk)

                        for ent in doc.ents:
                            if ent.label_ in ['GPE', 'LOC', 'FAC']:
                                loc_name = ent.text.strip()
                                locations[loc_name] = locations.get(loc_name, 0) + 1
                    
                    # Create tour guide
                    tour_stops = create_tour_guide(text, locations)
                    
                    # Store results in session state
                    st.session_state['locations'] = locations
                    st.session_state['tour_stops'] = tour_stops
                    st.success("✅ Tour guide created!")
                    
                except Exception as e:
                    st.error(f"Error processing PDF: {str(e)}")

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
        st.info("Upload a PDF and click 'Create Literary Tour' to see the map.")

    # Display tour guide under the map if available
    if 'tour_stops' in st.session_state:
        st.markdown("---")
        st.subheader("📚 Literary Tour Guide")
        st.markdown("### Follow the footsteps of the characters through these locations:")
        
        for location, details in st.session_state['tour_stops'].items():
            with st.expander(f"📍 {location} ({details['mentions']} mentions)"):
                for i, context in enumerate(details['contexts'], 1):
                    st.markdown(f"**Scene {i}:**")
                    st.markdown(f"_{context}_")
                    if i < len(details['contexts']):
                        st.markdown("---")



