#!/usr/bin/env python
"""
Generate user parameter report for the 2-way benchmark comparison.
"""

import argparse
import logging
import yaml
import os
import pandas as pd

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(message)s')

ARG_PARSER = argparse.ArgumentParser(
    description="Generate user parameter report for the 2-way benchmark \
comparison.")
ARG_PARSER.add_argument('--benchmark_config',
                        dest='config',
                        action='store',
                        help='The yaml config file for generating comparison.',
                        default='generate_2way_benchmark.yaml',
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


class benchmark_parameters_generator():
    """Generate user parameter report for the 2-way benchmark comparison.."""
    def __init__(self, ARGS):
        # load and expend config
        codepath = os.path.split(os.path.abspath(__file__))[0]
        filename = os.path.join(codepath, ARGS.config)
        with open(filename, 'r') as f:
            c = yaml.safe_load(f)
            self.config = c.get('benchmark_comparison_generator', {})

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

        # parse parameters
        self.output = ARGS.output
        self.output_format = ARGS.output_format

        if self.output is None:
            fpath = os.path.dirname(codepath)
            fname = '2way_benchmark_configuration.{0}'.format(
                self.output_format)
            self.output = os.path.join(fpath, fname)

        # init
        self._parse_data()

    def _parse_data(self):
        """Parse data and build the dataframe.

        Input:
            - self.config: customized configuration.
        Updates:
            - self.dataframe: report dataframe to be updated.
        """
        # build the dataframe
        self.dataframe = pd.DataFrame(self.kpis_cfg,
                                      columns=[
                                          'name', 'unit', 'higher_is_better',
                                          'max_pctdev_threshold',
                                          'confidence_threshold',
                                          'negligible_threshold',
                                          'regression_threshold'
                                      ])
        # format the dataframe
        # self.dataframe = self.dataframe.round(2)

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

        _show('self.config', self.config)
        _show('self.kpis_cfg', self.kpis_cfg)
        _show('self.output', self.output)
        _show('self.output_format', self.output_format)
        _show('self.dataframe', self.dataframe)


if __name__ == '__main__':
    gen = benchmark_parameters_generator(ARGS)
    # gen.show_vars()
    gen.dump_to_file()

exit(0)
