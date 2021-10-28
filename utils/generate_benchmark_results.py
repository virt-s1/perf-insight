#!/usr/bin/env python3
"""
Generate the benchmark results for the TEST and BASE testruns.
"""

import argparse
import logging
import yaml
import os
import pandas as pd
import numpy as np
from scipy.stats import ttest_rel
from scipy.stats import ttest_ind

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(message)s')

ARG_PARSER = argparse.ArgumentParser(
    description="Generate the benchmark results for the TEST and BASE testruns.")
ARG_PARSER.add_argument('--config',
                        dest='config',
                        action='store',
                        help='The yaml config file for generating results.',
                        default='generate_benchmark_results.yaml',
                        required=False)
ARG_PARSER.add_argument('--test',
                        dest='test',
                        action='store',
                        help='The results CSV file for TEST testrun.',
                        default='test.testrun_results.csv',
                        required=False)
ARG_PARSER.add_argument('--base',
                        dest='base',
                        action='store',
                        help='The results CSV file for BASE testrun.',
                        default='base.testrun_results.csv',
                        required=False)
ARG_PARSER.add_argument('--output-format',
                        dest='output_format',
                        action='store',
                        choices=('csv', 'html'),
                        help='The output file format.',
                        default='csv',
                        required=False)
ARG_PARSER.add_argument('--output',
                        dest='output',
                        action='store',
                        help='The file to store benchmark results.',
                        default=None,
                        required=False)

ARGS = ARG_PARSER.parse_args()


class BenchmarkResultsGenerator():
    """Generate benchmark results report."""

    def __init__(self, ARGS):
        # load and expend config
        with open(ARGS.config, 'r') as f:
            c = yaml.safe_load(f)
            self.config = c['benchmark_results_generator']

        self.keys_cfg = self.config.get('keys')
        for item in self.keys_cfg:
            if not item.get('name'):
                print('Error: "name" must be given.')
                return 1
            if 'from' not in item:
                item['from'] = item['name']
            if 'unit' not in item:
                item['unit'] = None

        self.kpis_cfg = self.config.get('kpis')
        for item in self.kpis_cfg:
            if not item.get('name'):
                print('Error: "name" must be given.')
                return 1
            if 'from' not in item:
                item['from'] = item['name']
            if 'unit' not in item:
                item['unit'] = None

            kpi_defaults = self.config.get('kpi_defaults', {})
            if 'higher_is_better' not in item:
                item['higher_is_better'] = kpi_defaults.get(
                    'higher_is_better', True)
            if 'max_pctdev_threshold' not in item:
                item['max_pctdev_threshold'] = kpi_defaults.get(
                    'max_pctdev_threshold', 0.10)
            if 'confidence_threshold' not in item:
                item['confidence_threshold'] = kpi_defaults.get(
                    'confidence_threshold', 0.95)
            if 'negligible_threshold' not in item:
                item['negligible_threshold'] = kpi_defaults.get(
                    'negligible_threshold', 0.05)
            if 'regression_threshold' not in item:
                item['regression_threshold'] = kpi_defaults.get(
                    'regression_threshold', 0.10)

    # load testrun results for test and base samples
        self.df_test = pd.read_csv(ARGS.test, index_col=0)
        self.df_base = pd.read_csv(ARGS.base, index_col=0)

        # parse parameters
        self.output = ARGS.output
        self.output_format = ARGS.output_format

        if self.output is None:
            self.output = 'benchmark_results.{0}'.format(self.output_format)

        # init
        self.df_report = None
        self._parse_data()

    def _parse_data(self):
        """Parse data from the testrun results.

        Input:
            - self.df_test: dataframe for the TEST samples.
            - self.df_base: dataframe for the BASE samples.
            - self.config: customized configuration.
        Updates:
            - self.df_report: report dataframe to be updated.
        """
        # build the report dataframe
        self._init_df_report()
        self._fill_df_report()
        # format the report dataframe
        self._format_df_report()

    def _init_df_report(self):
        """Init the report dataframe.

        Create a basic report dataframe with:
        1. KEYs and KPIs as columns;
        2. Deduplicated KEYs from test dataframe as rows.

        Input:
            - self.df_test: dataframe for the TEST samples.
            - self.df_base: dataframe for the BASE samples.
            - self.keys_cfg: customized configuration for KEYs.
            - self.kpis_cfg: customized configuration for KPIs.

        Updates:
            - self.df_report: report dataframe to be updated.
        """
        # create a report dataframe with KEY columns only
        keys_name = [x['name'] for x in self.keys_cfg]
        keys_from = [x['from'] for x in self.keys_cfg]

        # init report dataframe
        if self.config.get('functions', {}).get(
                'report_items', 'combined_base') == 'test_only':
            # based on the test
            self.df_report = self.df_test[keys_from].drop_duplicates()
        else:
            # based on the combination of base and test
            self.df_report = pd.concat([self.df_base, self.df_test
                                        ])[keys_from].drop_duplicates()

        # rename the columns
        for key_name, key_from in zip(keys_name, keys_from):
            if key_name != key_from:
                self.df_report.rename(columns={key_from: key_name},
                                      inplace=True)

        # sort the report dataframe and reset its index
        self.df_report = self.df_report.sort_values(by=keys_name)
        self.df_report = self.df_report.reset_index().drop(columns=['index'])

        # insert column for case result if asked
        if self.config.get('functions', {}).get('case_conclusion', True):
            self.df_report.insert(len(self.df_report.columns), 'Conclusion', 0)

        # expaned the report dataframe with KPI columns
        for kpi_cfg in self.kpis_cfg:
            expansion = [
                'BASE-AVG', 'BASE-%SD', 'TEST-AVG', 'TEST-%SD', '%DF', 'SGN',
                'CON'
            ]
            for suffix in expansion:
                name = '{0}-{1}'.format(kpi_cfg['name'], suffix)
                self.df_report.insert(len(self.df_report.columns), name, 0)

    def _fill_df_report(self):
        """Fill up the report dataframe.

        Input:
            - self.df_test: dataframe for the TEST samples.
            - self.df_base: dataframe for the BASE samples.
            - self.keys_cfg: customized configuration for KEYs.
            - self.kpis_cfg: customized configuration for KPIs.

        Updates:
            - self.df_report: report dataframe to be updated.
        """
        def _get_statistics(df_base, df_test, kpi_cfg):
            """Calculate basic statistics for the specified KPI.

            Returns:
            1. mean of the base samples
            2. %stddev of the base samples
            3. mean of the test samples
            4. %stddev of the test samples
            5. %diff of the test mean over base mean
            """
            kpi_from = kpi_cfg['from']

            # calculate the "mean" and "%stddev"
            base_mean = df_base[kpi_from].mean()
            base_pctsd = df_base[kpi_from].std(
                ddof=1) / base_mean * 100 if base_mean != 0 else np.nan
            test_mean = df_test[kpi_from].mean()
            test_pctsd = df_test[kpi_from].std(
                ddof=1) / test_mean * 100 if test_mean != 0 else np.nan

            # calculate the "%diff"
            pctdiff = (test_mean - base_mean
                       ) / base_mean * 100 if base_mean != 0 else np.nan

            return (base_mean, base_pctsd, test_mean, test_pctsd, pctdiff)

        def _get_significance(df_base, df_test, kpi_cfg, paired=False):
            """Get the t-test significance for the specified KPI.

            Returns:
                The Significance which value between 0 and 1. When the
                calculation fails, it will return 'nan' instead.
            """
            kpi_from = kpi_cfg['from']
            array1 = df_base[kpi_from]
            array2 = df_test[kpi_from]

            if paired:
                (statistic, pvalue) = ttest_rel(array1, array2)
            else:
                (statistic, pvalue) = ttest_ind(array1, array2)

            significance = 1 - pvalue

            return significance

        def _get_conclusion(base_pctsd,
                            test_pctsd,
                            pctdiff,
                            significance,
                            kpi_cfg,
                            use_abbr=False):
            """Get the conclusion of the specified KPI.

            An algorithm helps reaching a preliminary conclusion for each KPI.
            ID - Invalid Data           Any of the input data is invalid.
            HV - High Variance          %SD > MAX_PCTDEV_THRESHOLD
            NS - No Significance        SGN < CONFIDENCE_THRESHOLD
            NC - Negligible Changes     abs(%DF) <= NEGLIGIBLE_THRESHOLD
            MI - Moderate Improvement   NEGLIGIBLE_THRESHOLD < abs(%DF) <=
                                        REGRESSION_THRESHOLD.
            MR - Moderate Regression    Same as above, but in the negative
                                        direction.
            DI - Dramatic Improvement   abs(%DF) > REGRESSION_THRESHOLD
            DR - Dramatic Regression    Same as above, but in the negative
                                        direction.

            Returns: any of the conclusion mentioned above or "np.nan".
            """

            abbrs = {
                'Invalid Data': 'ID',
                'High Variance': 'HV',
                'No Significance': 'NS',
                'Negligible Changes': 'NC',
                'Moderate Improvement': 'MI',
                'Moderate Regression': 'MR',
                'Dramatic Improvement': 'DI',
                'Dramatic Regression': 'DR'
            }

            higher_is_better = kpi_cfg['higher_is_better']
            MAX_PCTDEV_THRESHOLD = kpi_cfg['max_pctdev_threshold'] * 100
            NEGLIGIBLE_THRESHOLD = kpi_cfg['negligible_threshold'] * 100
            REGRESSION_THRESHOLD = kpi_cfg['regression_threshold'] * 100
            CONFIDENCE_THRESHOLD = kpi_cfg['confidence_threshold']

            # data check
            if MAX_PCTDEV_THRESHOLD < 0:
                raise ValueError('Invalid value: max_pctdev_threshold')
            if CONFIDENCE_THRESHOLD < 0 or CONFIDENCE_THRESHOLD > 1:
                raise ValueError('Invalid value: confidence_threshold')
            if NEGLIGIBLE_THRESHOLD < 0:
                raise ValueError('Invalid value: negligible_threshold')
            if REGRESSION_THRESHOLD < 0:
                raise ValueError('Invalid value: regression_threshold')

            # get conclusion
            conclusion = None

            # check for 'not available'
            if np.isnan(pctdiff):
                conclusion = np.nan

            # check for 'Invalid Data'
            if not conclusion:
                if np.isnan(significance):
                    conclusion = 'Invalid Data'
                elif significance < 0 or significance > 1:
                    conclusion = 'Invalid Data'
                elif base_pctsd < 0 or test_pctsd < 0:
                    conclusion = 'Invalid Data'

            # check for 'High Variance'
            if not conclusion and MAX_PCTDEV_THRESHOLD != 0:
                if max(base_pctsd, test_pctsd) > MAX_PCTDEV_THRESHOLD:
                    conclusion = 'High Variance'

            # check for 'No Significance'
            if not conclusion and significance < CONFIDENCE_THRESHOLD:
                conclusion = 'No Significance'

            # check for 'Negligible Changes'
            if not conclusion and abs(pctdiff) <= NEGLIGIBLE_THRESHOLD:
                conclusion = 'Negligible Changes'

            # check for 'Improvment' and 'Regression'
            if not conclusion:
                if abs(pctdiff) <= REGRESSION_THRESHOLD:
                    conclusion = 'Moderate '
                else:
                    conclusion = 'Dramatic '

                if (higher_is_better and pctdiff > 0) or (not higher_is_better
                                                          and pctdiff < 0):
                    conclusion += 'Improvement'
                else:
                    conclusion += 'Regression'

            # return conclusion or its abbreviation if asked
            return conclusion if not use_abbr else abbrs.get(
                conclusion, conclusion)

        def _get_case_conclusion(row, use_abbr=False):
            """Get the case result by anaylse each kpi's conclusion.

            Input:
                - row: the case data with conclusions in dictionary

            Returns:
                - conclusion: the conclusion of this case
            """

            abbrs = {
                'Invalid Data': 'ID',
                'High Variance': 'HV',
                'No Significance': 'NS',
                'Negligible Changes': 'NC',
                'Moderate Improvement': 'MI',
                'Moderate Regression': 'MR',
                'Dramatic Improvement': 'DI',
                'Dramatic Regression': 'DR'
            }

            # analyse the conclusion of each kpi
            conclusions = [row[x] for x in row.keys() if x.endswith('-CON')]
            if 'DR' in conclusions or 'Dramatic Regression' in conclusions:
                conclusion = 'Dramatic Regression'
            elif 'MR' in conclusions or 'Moderate Regression' in conclusions:
                conclusion = 'Moderate Regression'
            elif 'HV' in conclusions or 'High Variance' in conclusions:
                conclusion = 'High Variance'
            elif 'ID' in conclusions or 'Invalid Data' in conclusions:
                conclusion = 'Invalid Data'
            elif 'MI' in conclusions or 'Moderate Improvement' in conclusions:
                conclusion = 'Moderate Improvement'
            elif 'DI' in conclusions or 'Dramatic Improvement' in conclusions:
                conclusion = 'Dramatic Improvement'
            elif 'NC' in conclusions or 'Negligible Changes' in conclusions:
                conclusion = 'Negligible Changes'
            elif 'NS' in conclusions or 'No Significance' in conclusions:
                conclusion = 'No Significance'

            # return conclusion or its abbreviation if asked
            return conclusion if not use_abbr else abbrs.get(
                conclusion, conclusion)

        # walk each row of the report dataframe, get related data from the
        # test and base dataframes, calculate the KPIs and fill the results
        # back to the report dataframe.
        for (index, row) in self.df_report.iterrows():
            # spotlight to the related data in test and base dataframes
            df_test = self.df_test
            df_base = self.df_base

            for key_cfg in self.keys_cfg:
                # filter by each KEY
                key_name = key_cfg['name']
                key_from = key_cfg['from']
                df_test = df_test[df_test[key_from] == row[key_name]]
                df_base = df_base[df_base[key_from] == row[key_name]]

            for kpi_cfg in self.kpis_cfg:
                # calculate each KPI
                kpi_name = kpi_cfg['name']

                # calculate the "mean", "%SD" and "%DF"
                (base_mean, base_pctsd, test_mean, test_pctsd,
                 pctdiff) = _get_statistics(df_base, df_test, kpi_cfg)

                # calculate the significance
                significance = _get_significance(df_base, df_test, kpi_cfg)

                # calculate the conclusion
                use_abbr = self.config.get('defaults',
                                           {}).get('use_abbr', False)
                conclusion = _get_conclusion(base_pctsd, test_pctsd, pctdiff,
                                             significance, kpi_cfg, use_abbr)

                # update the current KPI
                row[kpi_name + '-BASE-AVG'] = base_mean
                row[kpi_name + '-BASE-%SD'] = base_pctsd
                row[kpi_name + '-TEST-AVG'] = test_mean
                row[kpi_name + '-TEST-%SD'] = test_pctsd
                row[kpi_name + '-%DF'] = pctdiff
                row[kpi_name + '-SGN'] = significance
                row[kpi_name + '-CON'] = conclusion

            # get case conclusion if asked
            if self.config.get('functions', {}).get('case_conclusion', True):
                use_abbr = self.config.get('functions', {}).get(
                    'case_conclusion_abbr', False)
                row['Conclusion'] = _get_case_conclusion(row, use_abbr)

            # write the row back
            self.df_report.iloc[index] = row

    def _format_df_report(self):
        """Format the report dataframe.

        Input:
            - self.config: customized configuration.

        Updates:
            - self.df_report: report dataframe to be updated.
        """
        # get defaults
        defaults = self.config.get('defaults', {})
        default_round = defaults.get('round')
        default_round_pct = defaults.get('round_pct')
        default_fillna = defaults.get('fillna', '')

        # apply rounds
        decimals_mapper = {}

        for column in self.keys_cfg:
            name = column['name']
            decimal = column.get('round', default_round)
            if decimal is not None:
                decimals_mapper.update({name: decimal})
        for column in self.kpis_cfg:
            for suffix in ('TEST-AVG', 'BASE-AVG'):
                name = '{0}-{1}'.format(column['name'], suffix)
                decimal = column.get('round', default_round)
                if decimal is not None:
                    decimals_mapper.update({name: decimal})
            for suffix in ('TEST-%SD', 'BASE-%SD', '%DF'):
                name = '{0}-{1}'.format(column['name'], suffix)
                decimal = column.get('round_pct', default_round_pct)
                if decimal is not None:
                    decimals_mapper.update({name: decimal})
            name = '{0}-{1}'.format(column['name'], 'SGN')
            decimals_mapper.update({name: 2})

        self.df_report = self.df_report.round(decimals=decimals_mapper)

        # fill non-values
        self.df_report = self.df_report.fillna(default_fillna)

        # add units to the column names
        columns_mapper = {}

        for column in self.keys_cfg:
            if column.get('unit'):
                old_name = column['name']
                new_name = '{0}({1})'.format(column['name'], column['unit'])
                columns_mapper.update({old_name: new_name})
        for column in self.kpis_cfg:
            if column.get('unit'):
                name = column['name']
                unit = column['unit']
                for suffix in ('TEST-AVG', 'BASE-AVG'):
                    old_name = '{0}-{1}'.format(name, suffix)
                    new_name = '{0}-{1}({2})'.format(name, suffix, unit)
                    columns_mapper.update({old_name: new_name})

        self.df_report.rename(columns=columns_mapper, inplace=True)

    def dump_to_csv(self):
        """Dump the report dataframe to a CSV file."""
        with open(self.output, 'w') as f:
            f.write(self.df_report.to_csv())

    def dump_to_html(self):
        """Dump the report dataframe to a HTML file."""
        with open(self.output, 'w') as f:
            f.write(self.df_report.to_html())

    def dump_to_file(self):
        """Dump the report dataframe to a file."""
        if self.output_format == 'csv':
            self.dump_to_csv()
        else:
            self.dump_to_html()

    def show_vars(self):
        """Print the value of varibles to the stdout."""
        def _show(name, value):
            print('\n> _show(%s):\n' % name)
            print(value)

        _show('self.config', self.config)
        _show('self.keys_cfg', self.keys_cfg)
        _show('self.kpis_cfg', self.kpis_cfg)
        _show('self.df_test', self.df_test)
        _show('self.df_base', self.df_base)
        _show('self.output', self.output)
        _show('self.output_format', self.output_format)
        _show('self.df_params', self.df_params)
        _show('self.df_report', self.df_report)


if __name__ == '__main__':
    gen = BenchmarkResultsGenerator(ARGS)
    # gen.show_vars()
    gen.dump_to_file()

exit(0)
