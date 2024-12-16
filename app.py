# app.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from logzero import logger
import fitz
from geopy.geocoders import Nominatim
import time
from collections import Counter
import spacy

# Page config
st.set_page_config(page_title="Book Location Mapper", layout="wide", page_icon="📚")

# Custom styling to match the reference
st.markdown("""
    <style>
    .main > div {
        padding: 0;
    }
    .stButton button {
        width: 100%;
        background-color: #4B3BFF;
        color: white;
    }
    div[data-testid="stSidebarNav"] {
        background-color: #f5f5f5;
        padding: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

def extract_text_from_pdf(pdf_file):
    """Extract text from uploaded PDF file"""
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_locations(text):
    """Extract location entities from text using spaCy"""
    try:
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(text)
        locations = [ent.text for ent in doc.ents if ent.label_ in ['GPE', 'LOC']]
        return Counter(locations)
    except OSError:
        st.error("Please install spaCy model using: python -m spacy download en_core_web_sm")
        return None

def geocode_places(locations):
    """Geocode places using Nominatim"""
    geolocator = Nominatim(user_agent="book_mapper")
    geocoded_places = []
    
    for place, count in locations.items():
        try:
            location = geolocator.geocode(place)
            if location:
                geocoded_places.append({
                    "name": place,
                    "lat": location.latitude,
                    "lon": location.longitude,
                    "count": count
                })
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error geocoding {place}: {e}")
    
    return geocoded_places

def create_map(geocoded_places=None):
    """Create the map visualization"""
    fig = go.Figure()
    
    if geocoded_places:
        # Add markers for locations
        lons = [p['lon'] for p in geocoded_places]
        lats = [p['lat'] for p in geocoded_places]
        texts = [f"{p['name']} ({p['count']} mentions)" for p in geocoded_places]
        sizes = [min(p['count'] * 5, 30) for p in geocoded_places]
        
        fig.add_trace(go.Scattergeo(
            lon=lons,
            lat=lats,
            text=texts,
            mode='markers',
            marker=dict(
                size=sizes,
                color='rgb(0, 100, 0)',
                opacity=0.8
            ),
            hoverinfo='text'
        ))

    fig.update_layout(
        showlegend=False,
        geo=dict(
            scope='world',
            showland=True,
            showcountries=True,
            landcolor='rgb(243, 243, 243)',
            countrycolor='rgb(204, 204, 204)',
            showocean=True,
            oceancolor='rgb(230, 230, 250)',
            projection_type='equirectangular',
            showcoastlines=True,
            coastlinecolor='rgb(204, 204, 204)',
            showframe=False
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=600
    )
    
    return fig

# Main app layout
title, _, _ = st.columns([6, 1, 3])
title.title("📚 Book Location Mapper")

# Create upload form in the left panel
with st.sidebar:
    uploaded_file = st.file_uploader(
        "Upload PDF Book",
        type=['pdf'],
        help="Limit 200MB per file • PDF"
    )
    
    analyze_button = st.button(
        "Analyze Locations",
        use_container_width=True,
        disabled=not uploaded_file
    )
    
    with st.expander("What is this?"):
        st.write("""
        This app analyzes PDF books to find and map mentioned locations. 
        Upload any PDF book to see where the story takes place.
        """)

# Create the main content area with map
if uploaded_file:
    if analyze_button:
        try:
            # Process the PDF
            text = extract_text_from_pdf(uploaded_file)
            locations = extract_locations(text)
            
            if locations:
                geocoded_places = geocode_places(locations)
                if geocoded_places:
                    fig = create_map(geocoded_places)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show locations table below map
                    st.subheader("📍 Found Locations")
                    location_df = pd.DataFrame([
                        {"Location": place, "Mentions": count}
                        for place, count in locations.items()
                    ]).sort_values("Mentions", ascending=False)
                    
                    st.dataframe(location_df, use_container_width=True)
                else:
                    st.warning("Could not find coordinates for any locations.")
            else:
                st.info("No locations found in the text.")
                
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
else:
    # Show empty map
    fig = create_map()
    st.plotly_chart(fig, use_container_width=True)
