#!/usr/bin/env python
"""
Generate the 2-way benchmark statistics.
"""

import argparse
import logging
import json
import pandas as pd
import numpy as np

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(message)s')

ARG_PARSER = argparse.ArgumentParser(
    description='Generate the 2-way benchmark statistics.')
ARG_PARSER.add_argument('--benchmark-csv',
                        dest='benchmark_csv',
                        action='store',
                        help='The 2way benchmark comparison.',
                        default='2way_benchmark.csv',
                        required=False)
ARG_PARSER.add_argument('--output',
                        dest='output',
                        action='store',
                        help='The file to store 2-way benchmark statistics.',
                        default='2way_statistics.json',
                        required=False)

ARGS = ARG_PARSER.parse_args()


class benchmark_statistics_generator():
    """Generate 2-way benchmark statistics."""
    def __init__(self, ARGS):
        # load the 2way benchmark comparison
        self.df_benchmark = pd.read_csv(ARGS.benchmark_csv, index_col=0)

        # parse parameters
        self.output = ARGS.output

        # init
        self.statistics = {}
        self._parse_data()

    def _parse_data(self):
        """Parse data from the 2way benchmark comparison.

        Input:
            - self.df_benchmark: the 2way benchmark comparison.
        Update:
            - self.statistics: the 2way benchmark statistics.
        """
        # convert dataframe to json
        result = self.df_benchmark.to_json(orient="split")
        parsed = json.loads(result)

        columns = parsed['columns']
        entries = parsed['data']

        # get benchmark type
        if 'IOPS-%DF' in columns:
            benchmark_type = 'fio'
            indicator_name = 'IOPS-%DF'
            overall_indicator = 'IOPS'

        # get overall performance
        index = columns.index(indicator_name)
        indicator_value = np.mean([x[index] for x in entries])
        sign = '' if indicator_value < 0 else '+'
        overall_performance = '{}{:.2f}%'.format(sign, indicator_value)

        # get test result
        FAILURE_THRESHOLD = 0.0
        test_result = 'PASS' if indicator_value > FAILURE_THRESHOLD else 'FAIL'

        # get case numbers
        total_case_num = failed_case_num = 0
        for item in entries:
            total_case_num += 1
            if 'DR' in item or 'Dramatic Regression' in item:
                failed_case_num += 1
        failed_case_rate = '{:.2%}'.format(failed_case_num / total_case_num)

        # save statistics
        self.statistics['test_result'] = test_result
        self.statistics['benchmark_type'] = benchmark_type
        self.statistics['indicator_name'] = indicator_name
        self.statistics['overall_indicator'] = overall_indicator
        self.statistics['overall_performance'] = overall_performance
        self.statistics['total_case_num'] = total_case_num
        self.statistics['failed_case_num'] = failed_case_num
        self.statistics['failed_case_rate'] = failed_case_rate

    def dump_to_file(self):
        """Dump the statistics to a JSON file."""
        with open(self.output, 'w') as f:
            json.dump(self.statistics, f, indent=3)

    def show_vars(self):
        """Print the value of varibles to the stdout."""
        def _show(name, value):
            print('\n> _show(%s):\n' % name)
            print(value)

        _show('self.output', self.output)
        _show('self.df_benchmark', self.df_benchmark)
        _show('self.statistics', self.statistics)


if __name__ == '__main__':
    gen = benchmark_statistics_generator(ARGS)
    gen.dump_to_file()

exit(0)
