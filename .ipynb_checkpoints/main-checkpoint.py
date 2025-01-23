import os
from tqdm import tqdm
from data_manager import DataManager
from processor import Processor
import pandas as pd
import matplotlib.colors as mcolors
from utils import process_file
from utils import create_figure_for_top_n_and_measure,plot_avertable_by_condition

def main():
    DOWNLOAD_FOLDER = './'
    DATA_FOLDER = os.path.join(DOWNLOAD_FOLDER, 'data')
    measures = ['DALYs (Disability-Adjusted Life Years)',
                'YLDs (Years Lived with Disability)',
                'Deaths',
                'YLLs (Years of Life Lost)']
    YEARS = [2018,2019,2020,2021]
    benchmark = 'regional_benchmark'

    # Ensure data folder exists
    DataManager.ensure_data_folder()
    
    for YEAR in YEARS:
        print(f'Running year {YEAR}')
    
        AGGREGATED_FILE = f'aggregatedGDB_{YEAR}.csv'
    # Load or aggregate data
        aggregated_data = DataManager.load_or_aggregate_data(AGGREGATED_FILE, process_file, YEAR)
    
        # Process each measure
        all_results = None
        for measure in tqdm(['DALYs (Disability-Adjusted Life Years)',
            'YLDs (Years Lived with Disability)',
            'Deaths',
            'YLLs (Years of Life Lost)']):
            final_data = Processor.process_measure(aggregated_data, measure, benchmark)
            if all_results is None:
                all_results = final_data
            else:
                all_results = all_results.merge(final_data, left_index=True, right_index=True, how='outer')
    
        # Save results
        result_file = f'results_aggregatedGDB_{YEAR}.csv'
        all_results.to_csv(os.path.join(DATA_FOLDER, result_file))
    
    #Time to plot
    print('Plotting')
    
    # Constants
    
    DOWNLOAD_FOLDER = './'
    DATA_FOLDER = os.path.join(DOWNLOAD_FOLDER, 'data')
    PLOT_FOLDER = os.path.join(DOWNLOAD_FOLDER, 'plots')
    if not os.path.isdir(PLOT_FOLDER):
        os.mkdir(PLOT_FOLDER)
    
    RESULTS_FILES = [os.path.join(DATA_FOLDER,f'results_aggregatedGDB_{year}.csv') for year in YEARS]

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


    for measure in measures:
        m = f'Avertable {measure}'
        top_20_countries_2018 = (
            combined_data[combined_data['Year'] == 2018]
            .groupby('Location')[m]
            .sum()
            .sort_values(ascending=False)
            .head(20)
            .index)
        create_figure_for_top_n_and_measure(combined_data, top_20_countries_2018, 5, m,PLOT_FOLDER, f'top_5_causes_{m}')
        create_figure_for_top_n_and_measure(combined_data, top_20_countries_2018, 10, m,PLOT_FOLDER, f'top_10_causes_{m}')
        create_figure_for_top_n_and_measure(combined_data, top_20_countries_2018, 20, m,PLOT_FOLDER, f'top_20_causes_{m}')


if __name__ == '__main__':
    main()
