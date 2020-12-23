#!/usr/bin/env python
"""
Generate the 2-way benchmark comparison for the TEST and BASE testruns.
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
    description="Generate the 2-way benchmark \
comparison for the TEST and BASE testruns.")
ARG_PARSER.add_argument('--config',
                        dest='config',
                        action='store',
                        help='The yaml config file for generating comparison.',
                        default='generate_2way_benchmark.yaml',
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
                        help='The file to store benchmark comparison.',
                        default=None,
                        required=False)

ARGS = ARG_PARSER.parse_args()


class benchmark_comparison_generator():
    """Generate 2-way benchmark comparison report."""
    def __init__(self, ARGS):
        # load and expend config
        codepath = os.path.split(os.path.abspath(__file__))[0]
        filename = os.path.join(codepath, ARGS.config)
        with open(filename, 'r') as f:
            c = yaml.safe_load(f)
            self.config = c[__class__.__name__]

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
            if 'max_percent_dev' not in item:
                item['max_percent_dev'] = kpi_defaults.get(
                    'max_percent_dev', 10)
            if 'regression_threshold' not in item:
                item['regression_threshold'] = kpi_defaults.get(
                    'regression_threshold', 5)
            if 'confidence_threshold' not in item:
                item['confidence_threshold'] = kpi_defaults.get(
                    'confidence_threshold', 0.95)

    # load testrun results for test and base samples
        self.df_test = pd.read_csv(ARGS.test)
        if 'Unnamed: 0' in self.df_test.columns:
            self.df_test = self.df_test.drop(columns=['Unnamed: 0'])
        self.df_base = pd.read_csv(ARGS.base)
        if 'Unnamed: 0' in self.df_base.columns:
            self.df_base = self.df_base.drop(columns=['Unnamed: 0'])

        # parse parameters
        self.output = ARGS.output
        self.output_format = ARGS.output_format

        if self.output is None:
            fpath = os.path.dirname(ARGS.test)
            fname = '2way_benchmark.{0}'.format(self.output_format)
            self.output = os.path.join(fpath, fname)

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

        # tailer the report dataframe from the test dataframe
        self.df_report = self.df_test[keys_from].drop_duplicates()

        # rename the columns
        for key_name, key_from in zip(keys_name, keys_from):
            if key_name != key_from:
                self.df_report.rename(columns={key_from: key_name},
                                      inplace=True)

        # sort the report dataframe and reset its index
        self.df_report = self.df_report.sort_values(by=keys_name)
        self.df_report = self.df_report.reset_index().drop(columns=['index'])

        # expaned the report dataframe with KPI columns
        for kpi_cfg in self.kpis_cfg:
            expansion = [
                'TEST-AVG', 'TEST-%SD', 'BASE-AVG', 'BASE-%SD', '%DIFF',
                'SIGN', 'SPEC'
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

            # calculate the "mean" and "%sd"
            base_mean = df_base[kpi_from].mean()
            base_pctsd = df_base[kpi_from].std(ddof=1) / base_mean * 100
            test_mean = df_test[kpi_from].mean()
            test_pctsd = df_test[kpi_from].std(ddof=1) / test_mean * 100

            # calculate the "%diff"
            pctdiff = (test_mean - base_mean) / base_mean * 100

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

        def _get_speculate(base_pctsd, test_pctsd, pctdiff, significance,
                           kpi_cfg):
            """Get the speculate of the specified KPI.

            To get the speculate, we need to consider the following conditions:
            1. The "%sd" for both samples should below MAX_PCT_DEV;
            2. Whether the "%diff" of the KPI beyonds REGRESSION_THRESHOLD;
            3. Whether the "significance" beyonds CONFIDENCE_THRESHOLD.

            Returns:
                - 'Data Invalid':         the input data is invalid;
                - 'Variance Too Large':   the "%sd" beyonds MAX_PCT_DEV;
                - 'No Difference':        the "%diff" is zero;
                - 'No Significance':      the "significance" is less than the
                                          CONFIDENCE_THRESHOLD;
                - 'Major Improvement' and 'Major Regression':
                    the "significance" beyonds CONFIDENCE_THRESHOLD and "%diff"
                    beyonds REGRESSION_THRESHOLD;
                - 'Minor Improvement' and 'Minor Regression':
                    the "significance" beyonds CONFIDENCE_THRESHOLD but "%diff"
                    is below REGRESSION_THRESHOLD;
            """

            higher_is_better = kpi_cfg['higher_is_better']
            MAX_PCT_DEV = kpi_cfg['max_percent_dev']
            REGRESSION_THRESHOLD = kpi_cfg['regression_threshold']
            CONFIDENCE_THRESHOLD = kpi_cfg['confidence_threshold']

            # data check
            if MAX_PCT_DEV < 0 or MAX_PCT_DEV > 100:
                raise ValueError('Invalid parameter: max_percent_dev')
            if CONFIDENCE_THRESHOLD < 0 or CONFIDENCE_THRESHOLD > 1:
                raise ValueError('Invalid parameter: confidence_threshold')
            if REGRESSION_THRESHOLD < 0 or REGRESSION_THRESHOLD > 1:
                raise ValueError('Invalid parameter: regression_threshold')

            if np.isnan(pctdiff):
                return np.nan

            if pctdiff == 0:
                return 'No Difference'

            if np.isnan(significance) or significance < 0 or significance > 1:
                return 'Data Invalid'

            if base_pctsd < 0 or test_pctsd < 0:
                return 'Data Invalid'

            if base_pctsd > MAX_PCT_DEV or test_pctsd > MAX_PCT_DEV:
                return 'Variance Too Large'

            if significance < CONFIDENCE_THRESHOLD:
                return 'No Significance'

            if (higher_is_better and pctdiff > 0) or (not higher_is_better
                                                      and pctdiff < 0):
                if abs(pctdiff) >= REGRESSION_THRESHOLD * 100:
                    return 'Major Improvement'
                else:
                    return 'Minor Improvement'
            else:
                if abs(pctdiff) >= REGRESSION_THRESHOLD * 100:
                    return 'Major Regression'
                else:
                    return 'Minor Regression'

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

                # calculate the "mean", "%sd" and "%diff"
                (base_mean, base_pctsd, test_mean, test_pctsd,
                 pctdiff) = _get_statistics(df_base, df_test, kpi_cfg)

                # calculate the significance
                significance = _get_significance(df_base, df_test, kpi_cfg)

                # calculate the speculate
                speculate = _get_speculate(base_pctsd, test_pctsd, pctdiff,
                                           significance, kpi_cfg)

                # update the current KPI
                row[kpi_name + '-BASE-AVG'] = base_mean
                row[kpi_name + '-BASE-%SD'] = base_pctsd
                row[kpi_name + '-TEST-AVG'] = test_mean
                row[kpi_name + '-TEST-%SD'] = test_pctsd
                row[kpi_name + '-%DIFF'] = pctdiff
                row[kpi_name + '-SIGN'] = significance
                row[kpi_name + '-SPEC'] = speculate

            # write the row back
            self.df_report.iloc[index] = row

    def _format_df_report(self):
        """Format the report dataframe.

        Input:
            - self.config: customized configuration.

        Updates:
            - self.df_report: report dataframe to be updated.
        """
        # format the dataframe
        defaults = self.config.get('defaults', {})
        dataframe_round = defaults.get('dataframe_round', 2)
        dataframe_fillna = defaults.get('dataframe_fillna', '')

        self.df_report = self.df_report.round(dataframe_round)
        self.df_report = self.df_report.fillna(dataframe_fillna)

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
    gen = benchmark_comparison_generator(ARGS)
    # gen.show_vars()
    gen.dump_to_file()

exit(0)
