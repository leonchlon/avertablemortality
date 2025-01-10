import os
import zipfile
import pandas as pd
from tqdm import tqdm
from utils import DATA_FOLDER, DOWNLOAD_FOLDER

class DataManager:
    @staticmethod
    def ensure_data_folder():
        if not os.path.exists(DATA_FOLDER):
            os.mkdir(DATA_FOLDER)
            zip_files = [f for f in os.listdir(DOWNLOAD_FOLDER) if f.startswith('IHM')]
            for zip_file in zip_files:
                with zipfile.ZipFile(os.path.join(DOWNLOAD_FOLDER, zip_file), 'r') as zip_ref:
                    zip_ref.extractall(DATA_FOLDER)

    @staticmethod
    def load_or_aggregate_data(aggregated_file, process_file_func, year):
        if aggregated_file not in os.listdir(DATA_FOLDER):
            csv_files = [
                os.path.join(DATA_FOLDER, f) for f in os.listdir(DATA_FOLDER)
                if f.startswith('IHM') and f.endswith('.csv')
            ]
            processed_data = (process_file_func(file, year) for file in tqdm(csv_files))
            aggregated_data = pd.concat(processed_data, ignore_index=True)
            aggregated_data.columns = ['Measure', 'Location', 'Sex', 'Age', 'Cause', 'Metric', 'Value']
            aggregated_data.to_csv(os.path.join(DATA_FOLDER, aggregated_file), index=False)
        else:
            aggregated_data = pd.read_csv(os.path.join(DATA_FOLDER, aggregated_file))
        return aggregated_data
