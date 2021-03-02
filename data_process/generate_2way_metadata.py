#!/usr/bin/env python
"""
Generate the 2-way metadata comparison for the TEST and BASE testruns.
"""

import argparse
import logging
import json
import yaml
import pandas as pd

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(message)s')

ARG_PARSER = argparse.ArgumentParser(description="Generate the 2-way metadata \
comparison for the TEST and BASE testruns.")
ARG_PARSER.add_argument('--config',
                        dest='config',
                        action='store',
                        help='The yaml config file for generating comparison.',
                        default='generate_2way_metadata.yaml',
                        required=False)
ARG_PARSER.add_argument('--test',
                        dest='test',
                        action='store',
                        help='The metadata JSON file for TEST testrun.',
                        default='test.metadata.json',
                        required=False)
ARG_PARSER.add_argument('--base',
                        dest='base',
                        action='store',
                        help='The metadata JSON file for BASE testrun.',
                        default='base.metadata.json',
                        required=False)
ARG_PARSER.add_argument('--output-format',
                        dest='output_format',
                        action='store',
                        help='The output format, available in [csv, html].',
                        default='csv',
                        required=False)
ARG_PARSER.add_argument('--output',
                        dest='output',
                        action='store',
                        help='The file to store metadata comparison.',
                        default='2way_benchmark_metadata.csv',
                        required=False)

ARGS = ARG_PARSER.parse_args()


class metadata_comparison_generator():
    """Generate TestRun Results according to the customized configuration."""
    def __init__(self, ARGS):
        # load config
        with open(ARGS.config, 'r') as f:
            c = yaml.safe_load(f)
            self.config = c[__class__.__name__]

        # load metadata for test and base testruns
        with open(ARGS.test, 'r') as f:
            self.test = json.load(f)
        with open(ARGS.base, 'r') as f:
            self.base = json.load(f)

        # parse parameters
        self.output = ARGS.output
        self.output_format = ARGS.output_format

        # init
        self.datatable = []
        self.dataframe = None
        self._parse_data()

    def _parse_data(self):
        """Parse data from the metadata dicts.

        Input:
        - self.test: metadata for TEST testrun.
        - self.base: metadata for BASE testrun.
        - self.config: customized configuration. (TBD)
        Output:
        - self.datatable: datatable to be generated.
        """
        # get defaults
        defaults = self.config.get('defaults', {})
        show_keys = defaults.get('show_keys', True)
        show_undefined = defaults.get('show_undefined', True)

        data = {}
        defined_test_keys = []
        defined_base_keys = []

        for item in self.config.get('metadata', {}):
            # get display name
            data['NAME'] = item.get('name')

            # get keys
            test_key = item.get('test_key') or item.get('key')
            base_key = item.get('base_key') or item.get('key')

            if test_key == base_key:
                data['KEY'] = test_key
            else:
                data['KEY'] = '{0}/{1}'.format(test_key, base_key)

            # get values
            data['BASE'] = self.base.get(base_key)
            data['TEST'] = self.test.get(test_key)

            # save to the data table
            self.datatable.append(data.copy())

            # save defined keys
            defined_test_keys.append(test_key)
            defined_base_keys.append(base_key)

        # deal with undefined metadata
        if show_undefined:
            # get undefined keys
            undefined_test_keys = [
                x for x in self.test.keys() if x not in defined_test_keys
            ]
            undefined_base_keys = [
                x for x in self.base.keys() if x not in defined_base_keys
            ]
            undefined_keys = list(
                set(undefined_test_keys) | set(undefined_base_keys))
            undefined_keys.sort()

            for key in undefined_keys:
                data['NAME'] = data['KEY'] = key
                data['BASE'] = self.base.get(key)
                data['TEST'] = self.test.get(key)

                # save to the data table
                self.datatable.append(data.copy())

        # remove keys if asked
        if not show_keys:
            for item in self.datatable:
                item.pop('KEY', None)

        # build dataframe
        self._build_dataframe()

    def _build_dataframe(self):
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

        _show('self.config', self.config)
        _show('self.test', self.test)
        _show('self.base', self.base)
        _show('self.output', self.output)
        _show('self.output_format', self.output_format)
        _show('self.datatable', self.datatable)
        _show('self.dataframe', self.dataframe)


if __name__ == '__main__':
    gen = metadata_comparison_generator(ARGS)
    gen.dump_to_file()

exit(0)
