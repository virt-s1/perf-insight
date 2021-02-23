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
        self.df_benchmark = pd.read_csv(ARGS.benchmark_csv, index_col=0)

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
            benchmark_type = 'fio'
            indicator_name = 'IOPS'
            indicator_value = 'n/a'
            indicator_index = columns.index('IOPS-%DF')

        # get overall performance
        values = [x[indicator_index] for x in entries]
        mean = np.mean(values)
        sign = '' if mean < 0 else '+'
        overall_performance = '{}{:.2f}%'.format(sign, mean)

        print('overall_indicator: ', indicator_name)
        print('overall_performance: ', overall_performance)

        # get case numbers
        total_case_num = failed_case_num = 0
        for item in entries:
            total_case_num += 1
            if 'DR' in item or 'Dramatic Regression' in item:
                failed_case_num += 1
        failed_case_rate = '{:.2%}'.format(failed_case_num / total_case_num)

        print('total_case_num: ', total_case_num)
        print('failed_case_num: ', failed_case_num)
        print('failed_case_rate: ', failed_case_rate)

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
