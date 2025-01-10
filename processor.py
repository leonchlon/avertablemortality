import numpy as np
import pandas as pd


class Processor:
    @staticmethod
    def process_measure(data, measure, hic_countries):
        """
        Process data for a specific measure.
        
        Args:
            data (pd.DataFrame): The aggregated data.
            measure (str): The measure to process (e.g., 'Deaths', 'DALYs').
            hic_countries (list): List of high-income countries for benchmarks.
        
        Returns:
            pd.DataFrame: Processed data for the specified measure.
        """
        if measure == 'Deaths':
            return Processor._process_deaths(data, hic_countries)
        else:
            return Processor._process_other_measure(data, measure, hic_countries)

    @staticmethod
    def _process_deaths(data, hic_countries):
        """
        Process data for the 'Deaths' measure, including counterfactual calculations.
        
        Args:
            data (pd.DataFrame): The aggregated data.
            hic_countries (list): List of high-income countries for benchmarks.
        
        Returns:
            pd.DataFrame: Processed data for 'Deaths'.
        """
        final_data = None
        for sub_measure in ['Deaths', 'Prevalence']:
            measure_data = data[data['Measure'] == sub_measure].set_index(['Location', 'Sex', 'Age', 'Cause'])
            measure_data = measure_data.pivot(columns='Metric', values='Value')
            measure_data.columns = [f'{sub_measure}', f'{sub_measure} Rate']
            if final_data is None:
                final_data = measure_data
            else:
                final_data = final_data.merge(measure_data, left_index=True, right_index=True, how='inner')

        # Calculate HIC mean counterfactual CF
        hic_mean_cf = (
            final_data.loc[final_data.index.get_level_values('Location').isin(hic_countries)]
            .groupby(['Sex', 'Age', 'Cause'])
            .apply(lambda x: np.nanmean(x['Deaths Rate'] / x['Prevalence Rate']))
            .rename("Counterfactual CF")
        )

        final_data = final_data.join(hic_mean_cf, on=['Sex', 'Age', 'Cause'], how='inner')
        final_data = final_data[final_data[['Prevalence', 'Deaths']].min(axis=1) > 10]

        # Calculate adjusted deaths and avertable deaths
        final_data['Adjusted Deaths'] = final_data['Prevalence'] * final_data['Counterfactual CF']
        final_data['Avertable Deaths'] = final_data['Deaths'] - final_data['Adjusted Deaths']
        final_data['Avertable Deaths'] = np.where(final_data['Avertable Deaths'] < 0, 0, final_data['Avertable Deaths'])

        return final_data[['Deaths', 'Counterfactual CF', 'Adjusted Deaths', 'Avertable Deaths']]

    @staticmethod
    def _process_other_measure(data, measure, hic_countries):
        """
        Process data for measures other than 'Deaths'.
        
        Args:
            data (pd.DataFrame): The aggregated data.
            measure (str): The measure to process.
            hic_countries (list): List of high-income countries for benchmarks.
        
        Returns:
            pd.DataFrame: Processed data for the specified measure.
        """
        measure_data = data[data['Measure'] == measure].set_index(['Location', 'Sex', 'Age', 'Cause'])

        # Pivot data to get metrics as columns
        pivoted_data = measure_data.pivot(columns='Metric', values='Value')
        pivoted_data.columns = [measure, "Rate"]

        # Filter out rows with very low values
        filtered_data = pivoted_data[pivoted_data[measure] > 10]

        # Calculate HIC mean rate
        hic_mean_rate = (
            filtered_data.loc[filtered_data.index.get_level_values('Location').isin(hic_countries)]
            .groupby(['Sex', 'Age', 'Cause'])['Rate']
            .mean()
            .rename('HIC_mean_rate')
        )

        # Merge HIC mean rate with filtered data
        filtered_data = filtered_data.merge(hic_mean_rate, left_index=True, right_index=True)

        # Calculate adjustment ratio
        filtered_data[f'AdjustRatio {measure}'] = (filtered_data['HIC_mean_rate'] / filtered_data['Rate']).clip(upper=1)

        # Calculate adjusted values and avertable values
        filtered_data[f'Adjusted {measure}'] = filtered_data[measure] * filtered_data[f'AdjustRatio {measure}']
        filtered_data[f'Avertable {measure}'] = filtered_data[measure] - filtered_data[f'Adjusted {measure}']

        return filtered_data[[measure, f'AdjustRatio {measure}', f'Adjusted {measure}', f'Avertable {measure}']]
