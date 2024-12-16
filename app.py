import streamlit as st
import plotly.express as px
import pandas as pd
from logzero import logger
import data_munging
import plot_locations

# Page configuration
st.set_page_config(
    page_title="Book Location Mapper",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title in main area
st.title("📚 Book Location Mapper")

# Initialize session state
if 'locations' not in st.session_state:
    st.session_state.locations = None
if 'geocoded_places' not in st.session_state:
    st.session_state.geocoded_places = None
if 'extracted_text' not in st.session_state:
    st.session_state.extracted_text = None

# File uploader
uploaded_file = st.file_uploader(
    "Upload PDF Book",
    type=['pdf'],
    help="Maximum file size: 200MB",
)

# Analyze button
analyze_button = st.button("Analyze Locations", type="primary", use_container_width=True)

# Add expander for what is this
with st.expander("What is this?"):
    st.write("""
    This app analyzes PDF books to find and map mentioned locations. It uses:
    - Natural Language Processing to identify location names
    - Geocoding to find coordinates
    - Interactive mapping to visualize locations
    
    The size of each marker indicates how frequently the location is mentioned.
    """)

# Main content
if analyze_button and uploaded_file is not None:
    try:
        with st.spinner('Processing PDF...'):
            # Extract text
            text = data_munging.extract_text_from_pdf(uploaded_file)
            st.session_state.extracted_text = text
            
            # Extract locations
            locations = data_munging.extract_locations(text)
            st.session_state.locations = locations
            
            if locations:
                # Geocode locations
                with st.spinner('Finding locations on map...'):
                    geocoded_places = data_munging.geocode_places(locations)
                    st.session_state.geocoded_places = geocoded_places

    except Exception as e:
        st.error(f"Error processing file: {str(e)}")

# Create columns for layout
map_col, stats_col = st.columns([7, 3])

with map_col:
    # Show map if we have geocoded places
    if st.session_state.geocoded_places:
        geo_df = pd.DataFrame(st.session_state.geocoded_places)
        fig = plot_locations.create_location_map(geo_df)
        st.plotly_chart(fig, use_container_width=True)
    else:
        # Show empty world map
        fig = plot_locations.create_empty_map()
        st.plotly_chart(fig, use_container_width=True)
    
    # Add text area below map to show extracted locations
    if st.session_state.locations:
        st.subheader("📍 Extracted Locations")
        locations_text = "\n".join([
            f"• {place}: {count} mentions"
            for place, count in st.session_state.locations.items()
        ])
        st.text_area(
            "Found locations with mention counts:",
            value=locations_text,
            height=200,
            disabled=True
        )

with stats_col:
    if st.session_state.locations:
        st.subheader("📊 Statistics")
        
        # Create DataFrame for locations
        locations_df = pd.DataFrame([
            {'Location': place, 'Mentions': count}
            for place, count in st.session_state.locations.items()
        ]).sort_values('Mentions', ascending=False)
        
        # Display metrics
        total_locations = len(st.session_state.locations)
        mapped_locations = len(st.session_state.geocoded_places) if st.session_state.geocoded_places else 0
        
        st.metric("Total Locations Found", total_locations)
        st.metric("Successfully Mapped", mapped_locations)
        
        if len(locations_df) > 0:
            st.metric(
                "Most Mentioned Location",
                locations_df.iloc[0]['Location'],
                f"{locations_df.iloc[0]['Mentions']} mentions"
            )
        
        # Display top locations table
        st.subheader("Top Locations")
        st.dataframe(
            locations_df.head(10),
            hide_index=True,
            use_container_width=True
        )
