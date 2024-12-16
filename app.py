from logzero import logger
import pandas as pd
import streamlit as st
import data_munging
import plot_locations

# Page config
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

st.title("📚 Book Location Mapper")

# Create three columns like in the State Movement app
sidebar_place, map_place, descriptor = st.columns([2, 6, 2])

# Sidebar content
with sidebar_place:
    with st.form(key="upload_form"):
        uploaded_file = st.file_uploader("Upload PDF Book", type=['pdf'])
        analyze_button = st.form_submit_button("Analyze Locations")

    # Add the "What is this?" expander in sidebar
    with st.expander("What is this?"):
        st.write("""
        This app analyzes PDF books to find and map mentioned locations. It uses:
        - Natural Language Processing to identify location names
        - Geocoding to find coordinates
        - Interactive mapping to visualize mentions
        
        The size of each marker indicates how frequently the location is mentioned.
        """)

# Initialize empty map container
map_loc = map_place.empty()

# Main logic
if analyze_button and uploaded_file is not None:
    try:
        # Process the PDF
        with st.spinner('Extracting text from PDF...'):
            text = data_munging.extract_text_from_pdf(uploaded_file)
            sidebar_place.success("✅ Text extracted")
        
        # Extract and display locations
        with st.spinner('Finding locations in text...'):
            locations = data_munging.extract_locations(text)
            
        if locations:
            # Display location counts in descriptor column
            with descriptor:
                st.subheader("📊 Location Mentions")
                location_df = pd.DataFrame(
                    [(place, count) for place, count in locations.items()],
                    columns=['Location', 'Mentions']
                ).sort_values('Mentions', ascending=False)
                
                st.dataframe(location_df, height=400)
            
            # Geocode locations
            with sidebar_place:
                st.subheader("🗺️ Geocoding Progress")
                geocoded_places = data_munging.geocode_places(locations)
            
            if geocoded_places:
                # Create and display map
                fig = plot_locations.build_location_chart(geocoded_places)
                map_loc.plotly_chart(fig, use_container_width=True)
                
                # Statistics in descriptor
                with descriptor:
                    st.subheader("📊 Statistics")
                    st.write(f"Total locations: {len(locations)}")
                    st.write(f"Geocoded: {len(geocoded_places)}")
                    if len(location_df) > 0:
                        st.write(f"Most mentioned: {location_df.iloc[0]['Location']} ({location_df.iloc[0]['Mentions']} times)")
            else:
                map_place.warning("No locations could be geocoded.")
        else:
            map_place.warning("No locations found in the text.")
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
