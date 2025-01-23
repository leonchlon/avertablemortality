import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import pandas as pd
import os
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

# Constants
DOWNLOAD_FOLDER = '/Users/leo/Downloads/avertableMortality/'
DATA_FOLDER = os.path.join(DOWNLOAD_FOLDER, 'data')
YEARS = [2018, 2019, 2020, 2021]
RESULTS_FILES = [os.path.join(DATA_FOLDER, f'results_aggregatedGDB_{year}.csv') for year in YEARS]

# Load and combine data for all years
data_frames = []
for year, file in zip(YEARS, RESULTS_FILES):
    if os.path.exists(file):
        df = pd.read_csv(file)
        df['Year'] = year
        data_frames.append(df)
    else:
        print(f"File {file} not found!")

combined_data = pd.concat(data_frames, ignore_index=True)

# Initialize Dash app
app = dash.Dash(__name__)

# Split long titles into multiple lines
def split_title(title, max_length=50):
    if len(title) > max_length:
        breakpoint = title[:max_length].rfind(' ')
        return title[:breakpoint] + '<br>' + title[breakpoint + 1:]
    return title
app.layout = html.Div([
    # Selection Column
    html.Div([
        html.Div([
            html.Label("Select Sex:"),
            dcc.Dropdown(
                id='sex-dropdown',
                options=[{'label': sex, 'value': sex} for sex in combined_data['Sex'].unique()],
                multi=True,
                placeholder="Select Sex",
                value=['Female']
            )
        ], style={'margin-bottom': '5px'}),
        html.Div([
            html.Label("Select Age:"),
            dcc.Dropdown(
                id='age-dropdown',
                options=[{'label': age, 'value': age} for age in combined_data['Age'].unique()],
                multi=True,
                placeholder="Select Age",
                value=['55+ years']
            )
        ], style={'margin-bottom': '5px'}),
        html.Div([
            html.Label("Select Cause:"),
            dcc.Dropdown(
                id='cause-dropdown',
                options=[{'label': cause, 'value': cause} for cause in combined_data['Cause'].unique()],
                value=combined_data['Cause'].unique()[0],
                clearable=False
            )
        ], style={'margin-bottom': '5px'}),
        html.Div([
            html.Label("Select Metric:"),
            dcc.Dropdown(
                id='metric-dropdown',
                options=[
                    {'label': 'Avertable DALYs', 'value': 'Avertable DALYs (Disability-Adjusted Life Years)'},
                    {'label': 'Avertable YLDs', 'value': 'Avertable YLDs (Years Lived with Disability)'},
                    {'label': 'Avertable Deaths', 'value': 'Avertable Deaths'},
                    {'label': 'Avertable YLLs', 'value': 'Avertable YLLs (Years of Life Lost)'}
                ],
                value='Avertable DALYs (Disability-Adjusted Life Years)',
                clearable=False
            )
        ], style={'margin-bottom': '5px'})
    ], style={
        'width': '5%',
        'padding': '10px',
        'display': 'inline-block',
        'verticalAlign': 'top',
        'border-right': '1px solid #ddd'
    }),
    
    # Main Plot Area
    html.Div([
        # First Row: Geo Heatmap and Pie Charts
        html.Div([
            html.Div([
                dcc.Graph(
                    id='geomap-heatmap',
                    config={'displayModeBar': True},
                    style={'height': '60vh', 'width': '100%'}
                ),
                html.Div([
                    html.Label("Year Slider:"),
                    dcc.Slider(
                        id='year-slider',
                        min=int(combined_data['Year'].min()),
                        max=int(combined_data['Year'].max()),
                        step=1,
                        value=int(combined_data['Year'].min()),
                        marks={int(year): str(year) for year in combined_data['Year'].unique()}
                    ),
                    html.Button("Play", id="play-button", n_clicks=0)
                ], style={'margin-top': '10px'}),
                dcc.Interval(
                    id='interval-component',
                    interval=1000,
                    n_intervals=0,
                    disabled=True
                )
            ], style={'width': '50%', 'display': 'inline-block', 'padding': '10px'}),
            html.Div([
                html.Div([
                    dcc.Graph(id='age-distribution', style={'height': '40vh'}),
                    dcc.Graph(id='top-countries-distribution', style={'height': '40vh'})
                ], style={'margin-bottom': '5px'}),
            ], style={'width': '25%', 'display': 'inline-block', 'padding': '5px'})
        ], style={'height': '40vh','display': 'flex', 'flex-direction': 'row'}),
        
        # Second Row: Time Evolution, Gender Comparison, and Global Disparity
        html.Div([
            html.Div([dcc.Graph(id='time-evolution-by-age')], style={'flex': 1, 'margin-right': '10px'}),
            html.Div([dcc.Graph(id='gender-comparison')], style={'flex': 1, 'margin-right': '10px'}),
            html.Div([dcc.Graph(id='global-disparity')], style={'flex': 1})
        ], style={'display': 'flex', 'flex-direction': 'row', 'margin-top': '20px', 'width': '100%'})
    ], style={'width': '75%', 'display': 'inline-block', 'padding': '10px'})
], style={'display': 'flex', 'flex-direction': 'row'})


# Toggle the interval component (play/pause functionality)
@app.callback(
    Output('interval-component', 'disabled'),
    Input('play-button', 'n_clicks'),
    State('interval-component', 'disabled'),
    prevent_initial_call=True
)
def toggle_interval(n_clicks, is_disabled):
    # Toggle interval enabled/disabled state
    return not is_disabled

# Update year-store on interval ticks
@app.callback(
    Output('year-slider', 'value'),
    Input('interval-component', 'n_intervals'),
    State('year-slider', 'value')
)
def update_year_store(n_intervals, current_year):
    # Increment year on each interval tick
    next_year = current_year + 1 if current_year < int(combined_data['Year'].max()) else int(combined_data['Year'].min())
    return next_year
    

@app.callback(
    Output('geomap-heatmap', 'figure'),
    [
        Input('sex-dropdown', 'value'),
        Input('age-dropdown', 'value'),
        Input('cause-dropdown', 'value'),
        Input('metric-dropdown', 'value'),
        Input('year-slider', 'value')
    ]
)

def update_geomap(selected_sex, selected_age, selected_cause, selected_metric, selected_year):
    # Filter and aggregate data
    filtered_data = combined_data[
        (combined_data['Sex'].isin(selected_sex)) &
        (combined_data['Age'].isin(selected_age)) &
        (combined_data['Cause'] == selected_cause) &
        (combined_data['Year'] == selected_year)
    ]
    filtered_data = filtered_data.groupby('Location')[selected_metric].sum().reset_index()

    # Compute global min and max
    global_data = combined_data[
        (combined_data['Sex'].isin(selected_sex)) &
        (combined_data['Age'].isin(selected_age)) &
        (combined_data['Cause'] == selected_cause)
    ]
    global_min = global_data[selected_metric].min()
    global_max = global_data[selected_metric].max()

    # Generate heatmap
    fig = px.choropleth(
        filtered_data,
        locations="Location",
        locationmode="country names",
        color=selected_metric,
        hover_name="Location",
        title=f"{selected_metric} for {selected_sex}, {selected_age}, {selected_cause} in {selected_year}",
        color_continuous_scale="Viridis",
        range_color=[global_min, global_max]
    )

    # Adjust legend layout for a smaller legend
    fig.update_layout(
        coloraxis_colorbar=dict(
            title='',
            orientation='h',  # Horizontal orientation
            yanchor='bottom',
            xanchor='center',
            x=0.5,  # Center the legend
            y=0.95
        ),
        title=dict(
            text=split_title(f"{selected_metric} for Selected Options in {selected_year}"),
            y=0.05,
            x=0.5,
            xanchor='center',
            yanchor='bottom',
            font=dict(size=13)
        )
    )

    return fig
    
# Callback for age distribution
@app.callback(
    Output('age-distribution', 'figure'),
    [
        Input('metric-dropdown', 'value'),
        Input('cause-dropdown', 'value'),
        Input('year-slider', 'value'),
        Input('sex-dropdown', 'value')
    ]
)
def update_age_distribution(selected_metric, selected_cause, selected_year, selected_sex):
    filtered_data = combined_data[
        (combined_data['Year'] == selected_year) &
        (combined_data['Cause'] == selected_cause) &
        (combined_data['Sex'].isin(selected_sex))
    ]
    age_distribution = filtered_data.groupby('Age')[selected_metric].sum().reset_index()
    fig = px.pie(age_distribution, names='Age', values=selected_metric, title='Distribution by Age Group')
    return fig

@app.callback(
    Output('top-countries-distribution', 'figure'),
    [
        Input('metric-dropdown', 'value'),
        Input('cause-dropdown', 'value'),
        Input('year-slider', 'value'),
        Input('sex-dropdown', 'value')
    ]
)
def update_top_countries_distribution(selected_metric, selected_cause, selected_year, selected_sex):
    filtered_data = combined_data[
        (combined_data['Year'] == selected_year) &
        (combined_data['Cause'] == selected_cause) &
        (combined_data['Sex'].isin(selected_sex))
    ]
    country_distribution = filtered_data.groupby('Location')[selected_metric].sum().reset_index()
    top_countries = country_distribution.nlargest(5, selected_metric)
    other = country_distribution[selected_metric].sum() - top_countries[selected_metric].sum()
    other_row = pd.DataFrame({'Location': ['Other'], selected_metric: [other]})
    top_countries = pd.concat([top_countries, other_row], ignore_index=True)
    
    fig = px.pie(top_countries, names='Location', values=selected_metric, title='Top 5 Countries Distribution')
    return fig

# Callback for side-by-side plots
@app.callback(
    [Output('time-evolution-by-age', 'figure'),
     Output('gender-comparison', 'figure'),
     Output('global-disparity', 'figure')],
    [
        Input('age-dropdown', 'value'),
        Input('sex-dropdown', 'value'),
        Input('cause-dropdown', 'value'),
        Input('metric-dropdown', 'value')
    ]
)
def update_side_plots(selected_ages, selected_sexes, selected_cause, selected_metric):
    filtered_data = combined_data[
        (combined_data['Age'].isin(selected_ages)) &
        (combined_data['Sex'].isin(selected_sexes)) &
        (combined_data['Cause'] == selected_cause)
    ]

    # Time Evolution
    time_evolution = filtered_data.groupby(['Year', 'Age'])[selected_metric].sum().reset_index()
    time_fig = px.line(time_evolution, x='Year', y=selected_metric, color='Age', title="Time Evolution by Age Group")

    # Gender Comparison
    gender_comparison = filtered_data.groupby(['Year', 'Sex'])[selected_metric].sum().reset_index()
    gender_fig = px.bar(gender_comparison, x='Year', y=selected_metric, color='Sex', barmode='group', title="Gender Comparison Over Time")

    # Global Disparity (Variance Proxy)
    disparity = filtered_data.groupby(['Year', 'Location'])[selected_metric].sum().groupby('Year').var().reset_index()
    disparity_fig = px.scatter(disparity, x='Year', y=selected_metric, title="Global Disparity Over Time")

    return time_fig, gender_fig, disparity_fig


if __name__ == '__main__':
    app.run_server(debug=True)
