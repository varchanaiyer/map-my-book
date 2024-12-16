from logzero import logger
import pandas as pd
import streamlit as st
import data_munging
import plot_locations

padding = 0
st.set_page_config(page_title="Book Location Mapper", layout="wide", page_icon="📚")

st.markdown(
    """
    <style>
    .small-font {
        font-size:12px;
        font-style: italic;
        color: #b1a7a6;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Main app layout
st.title("📚 Book Location Mapper")

with st.sidebar.expander("What is this?"):
    st.write("""
    This app analyzes PDF books to find and map mentioned locations. It uses:
    - Natural Language Processing to identify location names
    - Geocoding to find coordinates
    - Interactive mapping to visualize locations
    
    The size of each marker indicates how frequently the location is mentioned.
    """)

# Load NLP model
try:
    nlp = data_munging.load_nlp_model()
except Exception as e:
    st.error("Failed to load NLP model. Please make sure you have spaCy installed with 'en_core_web_sm'")
    st.stop()

# File upload
uploaded_file = st.file_uploader("Choose a PDF book", type=['pdf'])

if uploaded_file is not None:
    # Process the PDF
    with st.spinner('Extracting text from PDF...'):
        text = data_munging.extract_text_from_pdf(uploaded_file)
        st.success("✅ Text extracted successfully!")
    
    # Extract and display locations
    with st.spinner('Finding locations in text...'):
        locations = data_munging.extract_locations(text, nlp)
        
    if locations:
        # Display location counts
        st.subheader("📊 Location Mentions")
        location_df = pd.DataFrame(
            [(place, count) for place, count in locations.items()],
            columns=['Location', 'Mentions']
        ).sort_values('Mentions', ascending=False)
        
        st.dataframe(location_df)
        
        # Geocode locations
        st.subheader("🗺️ Geocoding Locations")
        geocoded_places = data_munging.geocode_places(locations)
        
        if geocoded_places:
            st.subheader("🌍 Location Map")
            fig = plot_locations.build_location_chart(geocoded_places)
            st.plotly_chart(fig, use_container_width=True)
            
            # Statistics in sidebar
            st.sidebar.subheader("📊 Statistics")
            st.sidebar.write(f"Total unique locations found: {len(locations)}")
            st.sidebar.write(f"Successfully geocoded: {len(geocoded_places)}")
            st.sidebar.write(f"Most mentioned location: {location_df.iloc[0]['Location']} ({location_df.iloc[0]['Mentions']} times)")
        else:
            st.warning("No locations could be geocoded.")
    else:
        st.warning("No locations found in the text.")
