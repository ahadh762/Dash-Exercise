# run this app with 'python app.py' and 
# visit http://127.0.0.1:8050/ in your web browswer

import dash
from dash import dcc,html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import pymssql

# Config.py contains all information for your database
from config import database
from config import table
from config import user
from config import password
from config import server

app = dash.Dash(__name__)

# assume you havea "long-form" DataFrame
# see https://plotly.com/python/px-arguments/ for more options

def Get_Data():

    conn = pymssql.connect(server, user, password, database)

    cursor = conn.cursor()
    # select rows from SQL table to insert in DataFrame

    cursor.execute(f"SELECT * FROM {table}")

    # I purposely used this for loop instead of the method in class to avoid a User Warning raised by Python
    row_list = []
    for row in cursor:
        row_list.append(row)
    
    # Get 1000 rows and convert them to Pandas DataFrame
    df = pd.DataFrame(row_list, columns = ['Species','Type','Height','Weight','ID','Location','Latitude','Longitude','Timestamp'])

    # Dictionary contains all of the abbreviations for each State in the USA
    us_state_to_abbrev = {
        "Alabama": "AL",
        "Alaska": "AK",
        "Arizona": "AZ",
        "Arkansas": "AR",
        "California": "CA",
        "Colorado": "CO",
        "Connecticut": "CT",
        "Delaware": "DE",
        "Florida": "FL",
        "Georgia": "GA",
        "Hawaii": "HI",
        "Idaho": "ID",
        "Illinois": "IL",
        "Indiana": "IN",
        "Iowa": "IA",
        "Kansas": "KS",
        "Kentucky": "KY",
        "Louisiana": "LA",
        "Maine": "ME",
        "Maryland": "MD",
        "Massachusetts": "MA",
        "Michigan": "MI",
        "Minnesota": "MN",
        "Mississippi": "MS",
        "Missouri": "MO",
        "Montana": "MT",
        "Nebraska": "NE",
        "Nevada": "NV",
        "New Hampshire": "NH",
        "New Jersey": "NJ",
        "New Mexico": "NM",
        "New York": "NY",
        "North Carolina": "NC",
        "North Dakota": "ND",
        "Ohio": "OH",
        "Oklahoma": "OK",
        "Oregon": "OR",
        "Pennsylvania": "PA",
        "Rhode Island": "RI",
        "South Carolina": "SC",
        "South Dakota": "SD",
        "Tennessee": "TN",
        "Texas": "TX",
        "Utah": "UT",
        "Vermont": "VT",
        "Virginia": "VA",
        "Washington": "WA",
        "West Virginia": "WV",
        "Wisconsin": "WI",
        "Wyoming": "WY",
        "D.C.": "DC",
        "District of Columbia": "DC",
        "American Samoa": "AS",
        "Guam": "GU",
        "Northern Mariana Islands": "MP",
        "Puerto Rico": "PR",
        "United States Minor Outlying Islands": "UM",
        "U.S. Virgin Islands": "VI",
    }
    df[['City','State']] = df['Location'].str.split(', ', expand=True)

    df['State'] = df.State.map(lambda x: us_state_to_abbrev[x])

    # Split Pokemon Type into Primary and Secondary Type
    df[['Primary Type','Secondary Type']] = df['Type'].str.split('/', expand=True)


    return df


def Make_Plots():

    df = Get_Data()

    # Plot Points of Pokemon on Map
    fig1 = px.scatter_mapbox(df, lat="Latitude", lon="Longitude", hover_name="Location",
                            color_discrete_sequence=["fuchsia"], zoom=3, height=300)
    fig1.update_layout(mapbox_style="open-street-map")
    fig1.update_layout(margin={"r":0,"t":0,"l":0,"b":0})


    # Plot Pokemon Heat Map
    # Group by State based on number of pokemon
    poke_count = df.groupby(['State'])['Species'].count().reset_index(name='Pokemon Count')
    fig2 = px.choropleth(poke_count,
                        locations='State', 
                        locationmode="USA-states", 
                        scope="usa",
                        color='Pokemon Count',
                        color_continuous_scale=["white", "green"], 
                        )


    # Plot Pokemon by Number of Appearances
    count_by_species = df.groupby(['Species'])['Species'].count().reset_index(name='Count').sort_values(by = 'Count',ascending=True)
    fig3 = px.bar(count_by_species.tail(15), x = 'Count', y = 'Species', title = 'Most Popular Pokemon by Number of Appearances', orientation='h')


    # Plot Pokemon by Type
    count_by_type = df.groupby(['Primary Type'])['Secondary Type'].count().reset_index(name='Count').sort_values(by = 'Count',ascending=True)
    fig4 = px.bar(count_by_type.tail(15), x = 'Count', y = 'Primary Type', title = 'Most Popular Pokemon by Primary Type', orientation='h')


    # Plot Dash Table with 100 Most Recent Pokemon
    time_df = df.sort_values(by = 'Timestamp', ascending=False).head(100)

    time_df['Timestamp'] = pd.to_datetime(time_df['Timestamp'], unit = 'ms').dt.strftime('%Y-%m-%d %H:%M:%S')

    fig5 = go.Figure(data=[go.Table(header=dict(values=df.drop(columns=['City','State','Primary Type','Secondary Type']).columns),
                    cells=dict(values=[time_df['Species'].tolist(), time_df['Type'].tolist(), time_df['Height'].tolist(), time_df['Weight'].tolist(), 
                    time_df['ID'].tolist(), time_df['Location'].tolist(), time_df['Latitude'].tolist(), time_df['Longitude'].tolist(), time_df['Timestamp'].tolist()]))
                        ])
    fig5.update_layout(
        title="100 Most Recently Added Pokemon")

    return fig1, fig2, fig3, fig4, fig5

fig1, fig2, fig3, fig4, fig5 = Make_Plots()

# CSS Styling

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(
    external_stylesheets=external_stylesheets
)

# Dash Application Layout
app.layout = html.Div(children = [
        
    html.H1(children = 'Dash Exercise'),

    html.Div(children=''' 
        Pokemon Dashboard by Ahad hussain
    '''),

    html.H2(children=''' 
    Points of Pokemon Appearances
    ''', style={'marginBottom': 50, 'marginTop': 25}),

    dcc.Graph(id = 'Pokemon Point Map',
    figure = fig1),

    html.H2(children=''' 
    Pokemon Heat Map
    ''', style={'marginBottom': 50, 'marginTop': 25}),

    dcc.Graph(id = 'Pokemon Heat Map',
    figure = fig2),

    dcc.Graph(id = 'Most Popular Pokemon',
    figure = fig3),
    
    dcc.Graph(id = 'Most Popular Type',
    figure = fig4),

    dcc.Graph(id = '100 Most-Recent Pokemon',
    figure = fig5),

    dcc.Interval(
    id='interval-component',
    interval=60000, # in milliseconds (once a minute)
    n_intervals=0

)])

# Update All Plots
@app.callback([Output('Pokemon Point Map', 'figure'),
                Output('Pokemon Heat Map', 'figure'),
                Output('Most Popular Pokemon', 'figure'),
                Output('Most Popular Type', 'figure'),
                Output('100 Most-Recent Pokemon', 'figure')],
              Input('interval-component', 'n_intervals'))

def Update_Plots(n):
    fig1, fig2, fig3, fig4, fig5 = Make_Plots()

    return fig1, fig2, fig3, fig4, fig5

# Execute Program
if __name__ == '__main__':
    app.run_server(debug=True)