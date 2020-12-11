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
        # load config
        codepath = os.path.split(os.path.abspath(__file__))[0]
        filename = os.path.join(codepath, ARGS.config)
        with open(filename, 'r') as f:
            c = yaml.safe_load(f)
            self.config = c[__class__.__name__]

        # load testrun results for test and base samples
        self.df_test = pd.read_csv(ARGS.test)
        self.df_base = pd.read_csv(ARGS.base)

        # parse parameters
        self.output = ARGS.output
        self.output_format = ARGS.output_format

        if self.output is None and self.output_format == 'csv':
            fpath = os.path.dirname(ARGS.test)
            fname = '2way_benchmark.csv'
            self.output = os.path.join(fpath, fname)

        # init
        self.datatable = []
        self.dataframe = None
        self._parse_data()
        self._build_dataframe()

    def _parse_data(self):
        """Parse data from the testrun results.

        Input:
        - self.df_test: results for TEST testrun.
        - self.df_base: results for BASE testrun.
        - self.config: customized configuration.
        Output:
        - self.datatable: datatable to be generated.
        """
        pass

    def _build_dataframe(self):
        self.dataframe = pd.DataFrame(self.datatable)

    def dump_to_csv(self):
        with open(self.output, 'w') as f:
            f.write(self.dataframe.to_csv())

    def show_vars(self):
        print(self.config)
        print(self.df_test)
        print(self.df_base)
        print(self.output)
        print(self.output_format)
        print(self.datatable)
        print(self.dataframe)
        pass


if __name__ == '__main__':
    gen = benchmark_comparison_generator(ARGS)
    gen.show_vars()
    gen.dump_to_csv()

exit(0)
