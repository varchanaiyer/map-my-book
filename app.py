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

# Custom CSS to match the style
st.markdown("""
    <style>
    .stApp {
        max-width: 100%;
        padding: 1rem;
    }
    .uploadedFile {
        margin-bottom: 2rem;
    }
    .main > div {
        padding: 0;
    }
    .stButton button {
        width: 100%;
        margin-top: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("📚 Book Location Mapper")
    
    with st.form("upload_form"):
        uploaded_file = st.file_uploader(
            "Upload PDF Book",
            type=['pdf'],
            help="Maximum file size: 200MB"
        )
        analyze_button = st.form_submit_button(
            "Analyze Locations",
            use_container_width=True
        )
    
    with st.expander("What is this?"):
        st.markdown("""
            This app extracts and maps locations mentioned in books:
            
            - Upload any PDF book
            - AI identifies location mentions
            - Interactive map shows where story takes place
            - See location frequency and distribution
            
            Perfect for analyzing travel books, novels, or any text with geographic references.
        """)

# Main content area with three columns
if 'locations_df' not in st.session_state:
    st.session_state.locations_df = None
    
map_col, stats_col = st.columns([7, 3])

with map_col:
    # Initialize empty map container
    map_container = st.empty()
    
    # Show default world map if no data
    if st.session_state.locations_df is None:
        fig = plot_locations.create_empty_map()
        map_container.plotly_chart(fig, use_container_width=True)

with stats_col:
    stats_container = st.empty()

# Process uploaded file
if analyze_button and uploaded_file is not None:
    try:
        with st.spinner("Processing PDF..."):
            # Extract text
            text = data_munging.extract_text_from_pdf(uploaded_file)
            
            # Extract locations
            locations = data_munging.extract_locations(text)
            
            if locations:
                # Create DataFrame for locations
                locations_df = pd.DataFrame([
                    {
                        'location': place,
                        'mentions': count
                    } for place, count in locations.items()
                ]).sort_values('mentions', ascending=False)
                
                # Geocode locations
                with st.spinner("Geocoding locations..."):
                    geocoded_places = data_munging.geocode_places(locations)
                    
                if geocoded_places:
                    # Create map
                    geo_df = pd.DataFrame(geocoded_places)
                    fig = plot_locations.create_location_map(geo_df)
                    map_container.plotly_chart(fig, use_container_width=True)
                    
                    # Update statistics
                    with stats_col:
                        st.subheader("📊 Statistics")
                        st.metric("Total Locations", len(locations))
                        st.metric("Mapped Locations", len(geocoded_places))
                        
                        if len(locations_df) > 0:
                            st.metric(
                                "Most Mentioned",
                                locations_df.iloc[0]['location'],
                                f"{locations_df.iloc[0]['mentions']} times"
                            )
                        
                        st.subheader("Top Locations")
                        st.dataframe(
                            locations_df.head(10),
                            hide_index=True,
                            use_container_width=True
                        )
                else:
                    st.error("Could not geocode any locations.")
            else:
                st.warning("No locations found in the text.")
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
