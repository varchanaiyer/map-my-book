import plotly.express as px
import plotly.graph_objects as go

def create_empty_map():
    """Create an empty world map"""
    fig = go.Figure(go.Scattergeo())
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
            projection_type='equirectangular'
        ),
        height=600,
        margin=dict(l=0, r=0, t=0, b=0)
    )
    return fig

def create_location_map(df):
    """Create a map with location markers sized by mention count"""
    fig = px.scatter_geo(
        df,
        lat='lat',
        lon='lon',
        size='count',
        hover_name='name',
        hover_data={'count': True, 'lat': False, 'lon': False},
        projection='natural earth',
        size_max=30,
        color_discrete_sequence=['rgb(0, 100, 0)']
    )
    
    fig.update_layout(
        showlegend=False,
        geo=dict(
            showland=True,
            showcountries=True,
            showocean=True,
            countrycolor='rgb(204, 204, 204)',
            landcolor='rgb(243, 243, 243)',
            oceancolor='rgb(230, 230, 250)',
            projection_type='equirectangular'
        ),
        height=600,
        margin=dict(l=0, r=0, t=0, b=0)
    )
    
    return fig
