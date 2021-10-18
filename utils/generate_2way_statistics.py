#!/usr/bin/env python3
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
ARG_PARSER.add_argument('--primary-metric',
                        dest='primary_metrics',
                        action='append',
                        help='Primary metric(s) of the comparison.',
                        default=None,
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
        self.primary_metrics = ARGS.primary_metrics

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
        result = self.df_benchmark.to_json(orient="records")
        records = json.loads(result)

        # get primary metric(s) if not specified
        if not self.primary_metrics:
            columns = records[0].keys()
            if 'IOPS-%DF' in columns:
                self.primary_metrics = ['IOPS']
            if 'Throughput-%DF' in columns:
                self.primary_metrics = ['Throughput', 'Trans']

        # calculate overall performance
        values = []
        for record in records:
            for metric in self.primary_metrics:
                conclusion = record.get(metric + '-CON')
                # only put meaningful results into statistics
                if conclusion in ('NC', 'Negligible Changes', 'MI',
                                  'Moderate Improvement', 'MR',
                                  'Moderate Regression', 'DI',
                                  'Dramatic Improvement', 'DR',
                                  'Dramatic Regression'):
                    value = record.get(metric + '-%DF')
                    if value is not None:
                        values.append(value)

        mean = np.mean(values) if values else 0
        sign = '+' if mean > 0 else ''
        overall_performance = '{}{:.2f}%'.format(sign, mean)

        # get test result
        FAILURE_THRESHOLD = 0.0
        test_result = 'PASS' if mean > FAILURE_THRESHOLD else 'FAIL'

        # get case numbers
        total_case_num = failed_case_num = 0
        for record in records:
            total_case_num += 1
            values = record.values()
            if 'DR' in values or 'Dramatic Regression' in values:
                failed_case_num += 1
        failed_case_rate = '{:.2%}'.format(failed_case_num / total_case_num)

        # save statistics
        self.statistics['test_result'] = test_result
        self.statistics['primary_metric'] = ','.join(self.primary_metrics)
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

        _show('self.primary_metrics', self.primary_metrics)
        _show('self.output', self.output)
        _show('self.df_benchmark', self.df_benchmark)
        _show('self.statistics', self.statistics)


if __name__ == '__main__':
    gen = benchmark_statistics_generator(ARGS)
    gen.dump_to_file()

exit(0)
