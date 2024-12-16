import plotly.graph_objects as go

def build_location_chart(geocoded_places):
    """Create plotly map with markers sized by mention count"""
    fig = go.Figure()

    # Add markers
    sizes = [place['count'] for place in geocoded_places]
    max_size = max(sizes)
    normalized_sizes = [20 + (size/max_size)*30 for size in sizes]  # Scale marker sizes

    fig.add_trace(go.Scattergeo(
        lon=[place['lon'] for place in geocoded_places],
        lat=[place['lat'] for place in geocoded_places],
        text=[f"{place['name']} ({place['count']} mentions)" for place in geocoded_places],
        mode='markers',
        marker=dict(
            size=normalized_sizes,
            color='rgb(0, 200, 0)',
            opacity=0.8,
            line=dict(width=1, color='rgb(40, 40, 40)'),
        ),
        hovertemplate="<b>%{text}</b><extra></extra>"
    ))

    fig.update_layout(
        showlegend=False,
        geo=go.layout.Geo(
            scope='world',
            projection_type='natural earth',
            showland=True,
            landcolor='rgb(243, 243, 243)',
            countrycolor='rgb(204, 204, 204)',
            showcoastlines=True,
            coastlinecolor='rgb(204, 204, 204)',
        ),
        margin=dict(l=0, r=0, t=0, b=0)
    )

    return fig
