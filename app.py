import streamlit as st
import pandas as pd
import plotly.express as px
import fitz
from geopy.geocoders import Nominatim
import time
import sys

# Page config
st.set_page_config(page_title="Book Location Mapper", layout="wide", page_icon="📚")

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

# Create the split layout
col1, col2 = st.columns([1, 2])

# Load the model at startup
nlp = load_nlp_model()

with col1:
    st.title("📚 Book Location Mapper")
    st.markdown("---")
    
    # Load spaCy model at startup
    nlp = load_spacy_model()
    
    # File upload section
    st.subheader("Upload Your Book")
    uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])
    
    if uploaded_file and nlp:
        st.info(f"File uploaded: {uploaded_file.name}")
        
        # Show analysis button
        if st.button("Analyze Locations"):
            # Process the PDF
            with st.spinner('Extracting text from PDF...'):
                try:
                    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                    text = ""
                    for page in doc:
                        text += page.get_text()

                    
                    # Extract locations
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
