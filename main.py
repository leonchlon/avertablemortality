import os
from tqdm import tqdm
from data_manager import DataManager
from processor import Processor
from utils import YEAR, AGGREGATED_FILE, load_life_expectancy_data, measures, DATA_FOLDER

def main():
    # Load life expectancy benchmarks
    le_benchmarks = load_life_expectancy_data()
    hic_countries = le_benchmarks[le_benchmarks > 80].index.tolist()

    # Ensure data folder exists
    DataManager.ensure_data_folder()

    # Load or aggregate data
    aggregated_data = DataManager.load_or_aggregate_data(AGGREGATED_FILE, process_file, YEAR)

    # Process each measure
    all_results = None
    for measure in tqdm(measures):
        final_data = Processor.process_measure(aggregated_data, measure, hic_countries)
        if all_results is None:
            all_results = final_data
        else:
            all_results = all_results.merge(final_data, left_index=True, right_index=True, how='outer')

    # Save results
    result_file = f'results_aggregatedGDB_{YEAR}.csv'
    all_results.to_csv(os.path.join(DATA_FOLDER, result_file))

if __name__ == '__main__':
    main()
