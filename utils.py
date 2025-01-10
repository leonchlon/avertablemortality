import os
import pandas as pd
import numpy as np
import zipfile

DOWNLOAD_FOLDER = './'
DATA_FOLDER = os.path.join(DOWNLOAD_FOLDER, 'data')
YEAR = 2021
AGGREGATED_FILE = f'aggregatedGDB_{YEAR}.csv'

measures = ['DALYs (Disability-Adjusted Life Years)',
            'YLDs (Years Lived with Disability)',
            'Deaths',
            'YLLs (Years of Life Lost)']

def load_life_expectancy_data():
    file_path = os.path.join(DATA_FOLDER, 'LifeExpectancy.csv')
    data = pd.read_csv(file_path, index_col='Country Name')
    return data[str(YEAR)]

def process_file(file_path, year):
    """Process a single CSV file and return a cleaned DataFrame."""
    df = pd.read_csv(file_path)
    return df.query("year == @year")[['measure', 'location', 'sex', 'age', 'cause', 'metric', 'val']]