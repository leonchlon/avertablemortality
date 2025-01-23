import numpy as np
import pandas as pd


class Processor:
    @staticmethod
    def process_measure(data, measure, benchmark):
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
            return Processor._process_deaths(data, benchmark)
        else:
            return Processor._process_other_measure(data, measure, benchmark)

    @staticmethod
    def _process_deaths(data, benchmark = 'global_benchmark'):
        """
        Process data for the 'Deaths' measure, including counterfactual calculations.
        
        Args:
            data (pd.DataFrame): The aggregated data.
            hic_countries (list): List of high-income countries for benchmarks.
        
        Returns:
            pd.DataFrame: Processed data for 'Deaths'.
        """
        final_data = None
        regional_le = data[['regional_benchmark','global_benchmark','Location']].drop_duplicates()
        regional_le = regional_le.set_index('Location')
        for sub_measure in ['Deaths', 'Prevalence']:
            measure_data = data[data['Measure'] == sub_measure].set_index(['Location', 'Sex', 'Age', 'Cause','region'])
            measure_data = measure_data.pivot(columns='Metric', values='Value')
            measure_data.columns = [f'{sub_measure}', f'{sub_measure} Rate']
            if final_data is None:
                final_data = measure_data
            else:
                final_data = final_data.merge(measure_data, left_index=True, right_index=True, how='inner')
        final_data = final_data.merge(regional_le,
                                      left_on=['Location'],
                                      right_index=True)

        # Calculate HIC mean counterfactual CF
        gpby = ['Sex', 'Age', 'Cause']
        ret_cols = ['Deaths', 'Counterfactual CF', 'Adjusted Deaths', 'Avertable Deaths']
        if benchmark == 'regional_benchmark':
            gpby += ['region']
        
        hic_mean_cf = (
            final_data.loc[final_data[benchmark]]
            .groupby(gpby)
            .apply(lambda x: np.nanmean(x['Deaths Rate'] / x['Prevalence Rate']))
            .rename("Counterfactual CF")
        )

        final_data = final_data.join(hic_mean_cf, on=gpby, how='inner')
        final_data = final_data[final_data[['Prevalence', 'Deaths']].min(axis=1) > 10]

        # Calculate adjusted deaths and avertable deaths
        final_data['Adjusted Deaths'] = final_data['Prevalence'] * final_data['Counterfactual CF']
        final_data['Avertable Deaths'] = final_data['Deaths'] - final_data['Adjusted Deaths']
        final_data['Avertable Deaths'] = np.where(final_data['Avertable Deaths'] < 0, 0, final_data['Avertable Deaths'])

        return final_data[ret_cols]

    @staticmethod
    def _process_other_measure(data, measure, benchmark):
        """
        Process data for measures other than 'Deaths'.
        
        Args:
            data (pd.DataFrame): The aggregated data.
            measure (str): The measure to process.
            hic_countries (list): List of high-income countries for benchmarks.
        
        Returns:
            pd.DataFrame: Processed data for the specified measure.
        """
        regional_le = data[['regional_benchmark','global_benchmark','Location']].drop_duplicates()
        regional_le = regional_le.set_index('Location')
        
        measure_data = data[data['Measure'] == measure].set_index(['Location', 'Sex', 'Age', 'Cause','region'])
        
        # Pivot data to get metrics as columns
        pivoted_data = measure_data.pivot(columns='Metric', values='Value')
        pivoted_data.columns = [measure, "Rate"]
        
        # Filter out rows with very low values
        filtered_data = pivoted_data[pivoted_data[measure] > 10]
        
        filtered_data = filtered_data.merge(regional_le,left_on=['Location'], right_index=True)

        # Calculate HIC mean counterfactual CF
        gpby = ['Sex', 'Age', 'Cause']
        ret_cols = [measure, f'AdjustRatio {measure}', f'Adjusted {measure}', f'Avertable {measure}']
        if benchmark == 'regional_benchmark':
            gpby += ['region']
        
        # Calculate HIC mean rate
        hic_mean_rate = (
            filtered_data.loc[filtered_data[benchmark]]
            .groupby(gpby)['Rate']
            .mean()
            .rename('HIC_mean_rate')
        )
        filtered_data = filtered_data.join(hic_mean_rate, on=gpby,how='inner')
        # Calculate adjustment ratio
        filtered_data[f'AdjustRatio {measure}'] = (filtered_data['HIC_mean_rate'] / filtered_data['Rate']).clip(upper=1)

        # Calculate adjusted values and avertable values
        filtered_data[f'Adjusted {measure}'] = filtered_data[measure] * filtered_data[f'AdjustRatio {measure}']
        filtered_data[f'Avertable {measure}'] = filtered_data[measure] - filtered_data[f'Adjusted {measure}']
        return filtered_data[ret_cols]
