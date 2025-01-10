import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns
import zipfile

DOWNLOAD_FOLDER = './'
DATA_FOLDER = os.path.join(DOWNLOAD_FOLDER, 'data')

measures = ['DALYs (Disability-Adjusted Life Years)',
            'YLDs (Years Lived with Disability)',
            'Deaths',
            'YLLs (Years of Life Lost)']

def load_life_expectancy_data(year):
    file_path = os.path.join(DATA_FOLDER, 'LifeExpectancy.csv')
    data = pd.read_csv(file_path, index_col='Country Name')
    return data[str(year)]

def process_file(file_path, year):
    """Process a single CSV file and return a cleaned DataFrame."""
    df = pd.read_csv(file_path)
    return df.query("year == @year")[['measure', 'location', 'sex', 'age', 'cause', 'metric', 'val']]

    # Function to create a separate figure for each top N and measure
def create_figure_for_top_n_and_measure(data, countries, top_n, measure,PLOT_FOLDER, output_file_prefix):
    fig, axs = plt.subplots(1, 2, figsize=(20, 12), sharey=True)

    # Define colors for causes, ensuring each cause has a unique color
    cause_colors = {
        'COVID-19': '#ff6666',  # Red for COVID-19
    }
    # Generate additional colors for other causes
    default_colors = list(mcolors.TABLEAU_COLORS.values()) + list(mcolors.CSS4_COLORS.values())
    for i, cause in enumerate(data['Cause'].unique()):
        if cause not in cause_colors:
            cause_colors[cause] = default_colors[i % len(default_colors)]


    # Plot for 2018
    plot_avertable_by_condition(data, 2018, countries, top_n, axs[0], cause_colors, measure)

    # Plot for 2021 using the same countries as 2018
    plot_avertable_by_condition(data, 2021, countries, top_n, axs[1], cause_colors, measure)

    # Create a single legend below the subplots
    handles, labels = axs[0].get_legend_handles_labels()  # Get legend handles and labels
    fig.legend(handles, labels, loc='lower center', ncol=5, title="Causes")

    # Remove legends from individual subplots
    axs[0].get_legend().remove()
    axs[1].get_legend().remove()

    # Adjust layout and save the figure
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_FOLDER,f'{output_file_prefix}_top_{top_n}_{measure}_2018_2021.png'))
    plt.close()


# Define function to calculate and plot percentage distributions for a given measure
def plot_avertable_by_condition(data, year, countries, top_n, ax, colors, measure):
    # Filter data for the specified year, countries, and measure
    filtered_data = data[
        (data['Year'] == year) & (data['Location'].isin(countries))
    ]
    filtered_data = filtered_data.dropna(subset=measure,axis=0)

    # Group by cause to calculate total for the given measure
    top_causes = (
        filtered_data.groupby('Cause')[measure]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .index
    )

    # Filter for the top N causes
    filtered_data = filtered_data[filtered_data['Cause'].isin(top_causes)]

    # Add COVID-19 if not already in the data for consistency
    if 'COVID-19' not in filtered_data['Cause'].unique():
        filtered_data = pd.concat([
            filtered_data,
            pd.DataFrame({'Year': [year], 'Location': [countries[0]], 'Cause': ['COVID-19'], measure: [0]})
        ])

    # Group by country and cause to get total for the measure
    cause_distribution = (
        filtered_data.groupby(['Location', 'Cause'])[measure]
        .sum()
        .unstack(fill_value=0)
    )

    # Normalize to get percentages
    cause_percentages = cause_distribution.div(cause_distribution.sum(axis=1), axis=0) * 100

    # Ensure COVID-19 is included in the chart
    if 'COVID-19' not in cause_percentages.columns:
        cause_percentages['COVID-19'] = 0

    # Plot the stacked bar chart
    cause_percentages = cause_percentages[cause_percentages.columns.sort_values()]  # Sort causes alphabetically
    cause_percentages.plot(kind='bar', stacked=True, ax=ax, color=[colors.get(cause, '#cccccc') for cause in cause_percentages.columns])
    ax.set_title(f'Top {top_n} Causes of {measure} (Top 20 Countries, {year})')
    ax.set_ylabel(f'Rateage of {measure}')
    ax.set_xlabel('Country')
    ax.tick_params(axis='x', rotation=90)
