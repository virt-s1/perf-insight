#!/usr/bin/env python3
"""
Generate the benchmark report summary.
"""

import argparse
import logging
import json
import pandas as pd

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(message)s')

ARG_PARSER = argparse.ArgumentParser(
    description='Generate the benchmark report summary.')
ARG_PARSER.add_argument('--statistics-json',
                        dest='statistics_json',
                        action='store',
                        help='The benchmark statistics.',
                        default='benchmark_statistics.json',
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
                        help='The file to store benchmark summary.',
                        default='benchmark_summary.csv',
                        required=False)

ARGS = ARG_PARSER.parse_args()


class BenchmarkSummaryGenerator():
    """Generate benchmark report summary."""
    def __init__(self, ARGS):
        # load the benchmark statistics
        with open(ARGS.statistics_json, 'r') as f:
            self.statistics = json.load(f)

        # parse parameters
        self.output = ARGS.output
        self.output_format = ARGS.output_format

        if self.output is None:
            self.output = 'benchmark_summary.{0}'.format(self.output_format)

        # init
        self.datatable = []
        self.dataframe = None
        self._parse_data()

    def _parse_data(self):
        """Parse data from the benchmark statistics.

        Input:
            - self.statistics: the benchmark statistics.
        Update:
            - self.datatable: the benchmark summary.
        """
        # build the table from statistics

        self.datatable.append(
            ('Test Result', self.statistics.get('test_result')))
        self.datatable.append(
            ['Total Cases',
             self.statistics.get('total_case_num')])
        self.datatable.append(
            ['Failed Cases',
             self.statistics.get('failed_case_num')])

        self.datatable = [
            ('Test Result', self.statistics.get('test_result')),
            ('Total Case', self.statistics.get('total_case_num')),
            ('Failed Case', self.statistics.get('failed_case_num')),
            ('Failed Rate', self.statistics.get('failed_case_rate')),
            ('Primary Metric', self.statistics.get('primary_metric')),
            ('Overall Performance',
             self.statistics.get('overall_performance')),
        ]

        self.dataframe = pd.DataFrame(data=self.datatable,
                                      index=None,
                                      columns=('NAME', 'VALUE'))

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

        _show('self.statistics', self.statistics)
        _show('self.datatable', self.datatable)
        _show('self.dataframe', self.dataframe)


if __name__ == '__main__':
    gen = BenchmarkSummaryGenerator(ARGS)
    gen.dump_to_file()

exit(0)
