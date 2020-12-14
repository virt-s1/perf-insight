#!/usr/bin/env python
"""
Generate the 2-way benchmark comparison for the TEST and BASE testruns.
"""

import argparse
import logging
import json
import yaml
import os
import pandas as pd

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
                        help='The metadata JSON file for TEST testrun.',
                        default='test.testrun_metadata.json',
                        required=False)
ARG_PARSER.add_argument('--base',
                        dest='base',
                        action='store',
                        help='The metadata JSON file for BASE testrun.',
                        default='base.testrun_metadata.json',
                        required=False)
ARG_PARSER.add_argument('--output-format',
                        dest='output_format',
                        action='store',
                        help='The output format, available in [csv, ].',
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

        if self.output is None and self.output_format == 'csv':
            fpath = os.path.dirname(ARGS.test)
            fname = '2way_benchmark.csv'
            self.output = os.path.join(fpath, fname)

        # init
        self.df_report = None
        self._parse_data()

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
                'T-mean', 'T-%sd', 'B-mean', 'B-%sd', '%diff', 'sign',
                'speculate'
            ]
            for suffix in expansion:
                self.df_report.insert(len(self.df_report.columns),
                                      kpi_cfg['name'] + '-' + suffix, 0)

    def _parse_data(self):
        """Parse data from the testrun results.

        Input:
            - self.df_test: dataframe for the TEST samples.
            - self.df_base: dataframe for the BASE samples.
            - self.config: customized configuration.
        Updates:
            - self.df_report: report dataframe to be updated.
        """
        # init the report dataframe
        self._init_df_report()
        #self._fill_df_report()

    def dump_to_csv(self):
        with open(self.output, 'w') as f:
            pass
            #f.write(self.dataframe.to_csv())

    def show_vars(self):
        """Print the value of varibles to the stdout."""
        def _show(name, value):
            print('\n> _show(%s):\n' % name)
            print(value)

        # _show('self.config', self.config)
        # _show('self.keys_cfg', self.keys_cfg)
        # _show('self.kpis_cfg', self.kpis_cfg)
        _show('self.df_test', self.df_test)
        # _show('self.df_base', self.df_base)
        # _show('self.output', self.output)
        # _show('self.output_format', self.output_format)
        # _show('self.df_params', self.df_params)
        _show('self.df_report', self.df_report)


if __name__ == '__main__':
    gen = benchmark_comparison_generator(ARGS)
    gen.show_vars()
    gen.dump_to_csv()

exit(0)
