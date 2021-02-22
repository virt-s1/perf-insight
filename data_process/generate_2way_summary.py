#!/usr/bin/env python
"""
Generate the 2-way benchmark report summary.
"""

import argparse
import logging
import yaml
import json
import pandas as pd
import numpy as np
from scipy.stats import ttest_rel
from scipy.stats import ttest_ind

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(message)s')

ARG_PARSER = argparse.ArgumentParser(
    description='Generate the 2-way benchmark report summary.')
ARG_PARSER.add_argument('--benchmark-csv',
                        dest='benchmark_csv',
                        action='store',
                        help='The 2way benchmark comparison.',
                        default='2way_benchmark.csv',
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
                        help='The file to store 2way benchmark summary.',
                        default='2way_summary.csv',
                        required=False)

ARGS = ARG_PARSER.parse_args()


class benchmark_summary_generator():
    """Generate 2-way benchmark report summary."""
    def __init__(self, ARGS):
        # load the 2way benchmark comparison
        self.df_benchmark = pd.read_csv(ARGS.benchmark_csv)
        if 'Unnamed: 0' in self.df_benchmark.columns:
            self.df_benchmark = self.df_benchmark.drop(columns=['Unnamed: 0'])

        # parse parameters
        self.output = ARGS.output
        self.output_format = ARGS.output_format

        if self.output is None:
            self.output = '2way_summary.{0}'.format(self.output_format)

        # init
        self.datatable = []
        self.dataframe = None
        self._parse_data()

    def _parse_data(self):
        """Parse data from the 2way benchmark comparison.

        Input:
            - self.df_benchmark: the 2way benchmark comparison.
        Update:
            - self.datatable: the 2way benchmark summary.
        """
        # Convert dataframe to json
        result = self.df_benchmark.to_json(orient="split")
        parsed = json.loads(result)
        #print(json.dumps(parsed, indent=4))

        columns = parsed['columns']
        entries = parsed['data']

        if 'IOPS-%DF' in columns:
            test_type = 'fio'
            indicator_name = 'IOPS'
            indicator_value = '0%'
            indicator_index = columns.index('IOPS-%DF')

        # get overall performance
        values = [x[indicator_index] for x in entries]
        print('overall performance: ', np.mean(values))

        # get total and regression case number
        case_num_total = case_num_regression = 0
        for item in entries:
            case_num_total += 1
            if 'DR' in item:
                case_num_regression += 1

        print('case_num_total: ', case_num_total)
        print('case_num_regression: ', case_num_regression)

        exit(0)

        self.dataframe = pd.DataFrame(self.datatable)

    def dump_to_csv(self):
        """Dump the report dataframe to a CSV file."""
        with open(self.output, 'w') as f:
            f.write(self.dataframe.to_csv())

    def dump_to_html(self):
        """Dump the report dataframe to a HTML file."""
        with open(self.output, 'w') as f:
            f.write(self.dataframe.to_html())

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

        _show('self.df_benchmark', self.config)
        _show('self.datatable', self.datatable)
        _show('self.dataframe', self.dataframe)


if __name__ == '__main__':
    gen = benchmark_summary_generator(ARGS)
    gen.dump_to_file()

exit(0)
