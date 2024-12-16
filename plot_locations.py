# plot_locations.py
import plotly.express as px
import plotly.graph_objects as go

def create_empty_map():
    """Create an empty world map"""
    fig = go.Figure()
    
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
        height=500,
        margin=dict(l=0, r=0, t=0, b=0)
    )
    
    return fig

def create_location_map(df):
    """Create a map with location markers sized by mention count"""
    fig = px.scatter_geo(
        df,
        lat='lat',
        lon='lon',
        size='count',  # Size points by mention count
        hover_name='name',
        hover_data={
            'count': True,
            'lat': False,
            'lon': False
        },
        title='Location Mentions',
        size_max=30,
    )
    
    # Update layout for better visibility
    fig.update_layout(
        showlegend=False,
        geo=dict(
            scope='world',
            showland=True,
            showcountries=True,
            showocean=True,
            countrycolor='rgb(204, 204, 204)',
            landcolor='rgb(243, 243, 243)',
            oceancolor='rgb(230, 230, 250)',
            projection_type='equirectangular',
            showcoastlines=True,
            coastlinecolor='rgb(204, 204, 204)',
            showframe=False
        ),
        height=500,
        margin=dict(l=0, r=0, t=0, b=0)
    )
    
    # Update marker style
    fig.update_traces(
        marker=dict(
            color='rgb(0, 100, 0)',
            line=dict(width=1, color='rgb(40, 40, 40)'),
        )
    )
    
    return fig
