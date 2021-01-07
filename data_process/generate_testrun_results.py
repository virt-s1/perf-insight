#!/usr/bin/env python
"""
Generate TestRun Results for pbench-fio test.
"""

import argparse
import logging
import json
import yaml
import os
import pandas as pd
from jq import jq

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(message)s')

ARG_PARSER = argparse.ArgumentParser(description="Generate TestRun Results.")
ARG_PARSER.add_argument('--config',
                        dest='config',
                        action='store',
                        help='The yaml config file for generating results.',
                        default='generate_testrun_results.yaml',
                        required=False)
ARG_PARSER.add_argument('--datastore',
                        dest='datastore',
                        action='store',
                        help='The json file which contains the datastore.',
                        default='datastore.json',
                        required=False)
ARG_PARSER.add_argument('--metadata',
                        dest='metadata',
                        action='store',
                        help='The json file which contains the metadata.',
                        default='metadata.json',
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
                        help='The file to store TestRun results.',
                        default=None,
                        required=False)
ARGS = ARG_PARSER.parse_args()


class testrun_results_generator():
    """Generate TestRun Results according to the customized configuration."""
    def __init__(self, ARGS):
        # load config
        with open(ARGS.config, 'r') as f:
            c = yaml.safe_load(f)
            self.config = c[__class__.__name__]

        # load datastore
        with open(ARGS.datastore, 'r') as f:
            self.datastore = json.load(f)

        # load metadata
        with open(ARGS.metadata, 'r') as f:
            self.metadata = json.load(f)

        # parse parameters
        self.output = ARGS.output
        self.output_format = ARGS.output_format

        if self.output is None:
            self.output = 'testrun_results.{0}'.format(self.output_format)

        # init
        self.datatable = []
        self.dataframe = None
        self._parse_data()

    def _parse_data(self):
        self._build_datatable()
        self._build_dataframe()
        self._format_dataframe()

    def _build_datatable(self):
        """Parse data from the datastore into datatable.

        Input:
        - self.datastore: datastore.
        - self.config: customized configuration.
        Output:
        - self.datatable: datatable to be generated.
        """
        def _get_value_metadata(cfg, data=None):
            """Get value from metadata."""
            if cfg.get('key'):
                return self.metadata.get(cfg.get('key'))

        def _get_value_datastore(cfg, data=None):
            """Get value(s) from datastore."""
            # jq().transform() returns a list of string(s)
            res = jq(cfg['jqexpr']).transform(data, multiple_output=True)

            # multiply the factor if available
            if 'factor' in cfg:
                res = [x * cfg['factor'] for x in res]

            # return the whole list or the only value
            return res if len(res) > 1 else res[0]

        def _get_value_auto(cfg, data=None):
            """Get value by calculating."""
            if cfg['name'] == 'Sample':
                return 0
            if cfg['name'] == 'Path':
                value = os.path.join(data['path_lv_1'], data['path_lv_2'])
                return value

        def _get_value_unknown(cfg, data=None):
            print('ERROR: Unknown type in "source", config = "%s".' % cfg)
            exit(1)

        switch = {
            'metadata': _get_value_metadata,
            'datastore': _get_value_datastore,
            'auto': _get_value_auto,
        }

        self.config
        self.datastore
        self.datatable = []

        # generate rows for the datatable
        for iterdata in self.datastore:
            # generate one row
            data = {}
            for cfg in self.config.get('columns'):
                # get and set value(s)
                name = cfg.get('name')
                data[name] = switch.get(cfg['source'],
                                        _get_value_unknown)(cfg, iterdata)

            # deal with split if needed
            need_split = False
            if self.config.get('defaults', {}).get('split'):
                # get max number of samples
                max_sample = 1
                for value in data.values():
                    if isinstance(value, list) and len(value) > max_sample:
                        max_sample = len(value)
                need_split = True if max_sample > 1 else False

            if need_split:
                # split into samples
                for index in range(1, max_sample + 1):
                    sample_data = {}
                    # deal with each column
                    for name, value in data.items():
                        if isinstance(value, list):
                            # get the first value and save the rest
                            sample_data[name] = value[0]
                            data[name] = value[1:]
                            # Set "WRONG" flags for user check
                            if len(data[name]) == 0:
                                data[name] = 'WRONG'
                        else:
                            sample_data[name] = value

                    # update related columns
                    sample_data['Sample'] = index
                    sample_data['Path'] = os.path.join(data['Path'],
                                                       'sample%s' % index)

                    # save this row (sample) to datatable
                    self.datatable.append(sample_data.copy())
            else:
                # no need to split, save directly
                self.datatable.append(data.copy())

    def _build_dataframe(self):
        # create the dataframe
        self.dataframe = pd.DataFrame(self.datatable)

    def _format_dataframe(self):
        # get defaults
        defaults = self.config.get('defaults', {})
        default_round = defaults.get('round')
        default_fillna = defaults.get('fillna', '')

        # apply rounds
        decimals_mapper = {}
        for column in self.config.get('columns'):
            name = column['name']
            decimal = column.get('round', default_round)
            if decimal is not None:
                decimals_mapper.update({name: decimal})
        self.dataframe = self.dataframe.round(decimals=decimals_mapper)

        # fill non-values
        self.dataframe = self.dataframe.fillna(default_fillna)

        # add units to the column names
        columns_mapper = {}
        for column in self.config.get('columns'):
            if column.get('unit'):
                old_name = column['name']
                new_name = '{0}({1})'.format(column['name'], column['unit'])
                columns_mapper.update({old_name: new_name})
        self.dataframe.rename(columns=columns_mapper, inplace=True)

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
        _show('self.datastore', self.datastore)
        _show('self.metadata', self.metadata)
        _show('self.output', self.output)
        _show('self.output_format', self.output_format)
        _show('self.datatable', self.datatable)
        _show('self.dataframe', self.dataframe)


if __name__ == '__main__':
    gen = testrun_results_generator(ARGS)
    gen.dump_to_file()

exit(0)
