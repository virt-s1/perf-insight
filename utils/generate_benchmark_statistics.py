#!/usr/bin/env python3
"""
Generate the benchmark statistics.

Notice:
    The 'case_conclusion' function must be enabled while generating the
    benchmark results.
"""

import argparse
from collections import defaultdict
import logging
import json
import pandas as pd
import numpy as np

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(message)s')

ARG_PARSER = argparse.ArgumentParser(
    description='Generate the benchmark statistics.')
ARG_PARSER.add_argument('--benchmark-csv',
                        dest='benchmark_csv',
                        action='store',
                        help='The benchmark results.',
                        default='benchmark_results.csv',
                        required=False)
ARG_PARSER.add_argument('--base-csv',
                        dest='base_csv',
                        action='store',
                        help='The results CSV file for BASE testrun.',
                        default=None,
                        required=False)
ARG_PARSER.add_argument('--test-csv',
                        dest='test_csv',
                        action='store',
                        help='The results CSV file for TEST testrun.',
                        default=None,
                        required=False)
ARG_PARSER.add_argument('--output',
                        dest='output',
                        action='store',
                        help='The json file to store benchmark statistics.',
                        default='benchmark_statistics.json',
                        required=False)

ARGS = ARG_PARSER.parse_args()


class BenchmarkStatisticsGenerator():
    """Generate benchmark statistics."""

    def __init__(self, ARGS):
        # Parse parameters
        self.output = ARGS.output

        # Load the benchmark results
        benchmark_dataframe = pd.read_csv(ARGS.benchmark_csv, index_col=0)
        self.benchmark_json = json.loads(
            benchmark_dataframe.to_json(orient="records"))

        # Load BASE and TEST results
        self.base_json = self.test_json = None

        if ARGS.base_csv:
            base_dataframe = pd.read_csv(ARGS.base_csv, index_col=0)
            self.base_json = json.loads(
                base_dataframe.to_json(orient="records"))

        if ARGS.test_csv:
            test_dataframe = pd.read_csv(ARGS.test_csv, index_col=0)
            self.test_json = json.loads(
                test_dataframe.to_json(orient="records"))

        # Init
        self.statistics = {
            'benchmark': self.benchmark_json,
            'base': self.base_json,
            'test': self.test_json
        }

        # Calculate
        self._parse_data()

    def _parse_data(self):
        """Parse the statistic data from the results.

        Input:
            - self.benchmark_json: the benchmark results.
            - self.base_json: the test results for BASE.
            - self.test_json: the test results for TEST.
        Update:
            - self.statistics: the benchmark statistics.
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
        de_abbrs = {v: k for k, v in abbrs.items()}

        def _get_case_conclusion(row, use_abbr=False):
            """Get the case result by anaylse each kpi's conclusion.

            Input:
                - row: the case data with conclusions in dictionary

            Returns:
                - conclusion: the conclusion of this case
            """
            prioritized_conclusions = [
                'Dramatic Regression',
                'Moderate Regression',
                'High Variance',
                'Invalid Data',
                'Moderate Improvement',
                'Dramatic Improvement',
                'Negligible Changes',
                'No Significance'
            ]

            conclusion = None

            # collect conclusion for kpis
            kpi_conclusions = [row[x]
                               for x in row.keys() if x.endswith('-CON')]
            for c in prioritized_conclusions:
                if c in kpi_conclusions or abbrs[c] in kpi_conclusions:
                    conclusion = c
                    break

            # return conclusion or its abbreviation if asked
            return conclusion if not use_abbr else abbrs.get(
                conclusion, conclusion)

        # Get case number statistics
        self.statistics['case_num_base'] = len(
            self.base_json) if self.base_json else None
        self.statistics['case_num_test'] = len(
            self.test_json) if self.test_json else None
        self.statistics['case_num_benchmark'] = len(self.benchmark_json)

        case_num_spread = defaultdict(int)

        for case in self.benchmark_json:
            if 'Conclusion' in case:
                conclusion = case.get('Conclusion')
                conclusion = de_abbrs.get(conclusion, conclusion)
            else:
                conclusion = _get_case_conclusion(case, use_abbr=False)

            case_num_spread[conclusion] += 1

            # Keep conclusion explicit in statistics
            case['Conclusion'] = conclusion

        self.statistics['case_num_invalid_data'] = case_num_spread.get(
            'Invalid Data', 0)
        self.statistics['case_num_high_variance'] = case_num_spread.get(
            'High Variance', 0)
        self.statistics['case_num_no_significance'] = case_num_spread.get(
            'No Significance', 0)
        self.statistics['case_num_negligible_changes'] = case_num_spread.get(
            'Negligible Changes', 0)
        self.statistics['case_num_moderate_improvement'] = case_num_spread.get(
            'Moderate Improvement', 0)
        self.statistics['case_num_moderate_regression'] = case_num_spread.get(
            'Moderate Regression', 0)
        self.statistics['case_num_dramatic_improvement'] = case_num_spread.get(
            'Dramatic Improvement', 0)
        self.statistics['case_num_dramatic_regression'] = case_num_spread.get(
            'Dramatic Regression', 0)

        # Get overall performance statistics

        # # get primary metric(s) if not specified
        # if not self.primary_metrics:
        #     columns = records[0].keys()
        #     if 'IOPS-%DF' in columns:
        #         self.primary_metrics = ['IOPS']
        #     if 'Throughput-%DF' in columns:
        #         self.primary_metrics = ['Throughput', 'Trans']

        # # calculate overall performance
        # values = []
        # for record in records:
        #     for metric in self.primary_metrics:
        #         conclusion = record.get(metric + '-CON')
        #         # only put meaningful results into statistics
        #         if conclusion in ('NC', 'Negligible Changes', 'MI',
        #                           'Moderate Improvement', 'MR',
        #                           'Moderate Regression', 'DI',
        #                           'Dramatic Improvement', 'DR',
        #                           'Dramatic Regression'):
        #             value = record.get(metric + '-%DF')
        #             if value is not None:
        #                 values.append(value)

        # mean = np.mean(values) if values else 0
        # sign = '+' if mean > 0 else ''
        # overall_performance = '{}{:.2f}%'.format(sign, mean)

        # Get benchmark result
        if self.statistics['case_num_dramatic_regression'] > 0:
            self.statistics['benchmark_result'] = 'FAIL'
        else:
            self.statistics['benchmark_result'] = 'PASS'

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
        _show('self.benchmark_dataframe', self.benchmark_dataframe)
        _show('self.statistics', self.statistics)


if __name__ == '__main__':
    gen = BenchmarkStatisticsGenerator(ARGS)
    gen.dump_to_file()

exit(0)
