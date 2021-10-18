#!/usr/bin/env python3
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
import numpy as np

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
        try:
            with open(ARGS.metadata, 'r') as f:
                self.metadata = json.load(f)
        except (Exception):
            self.metadata = {}

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
        self._parse_datastore()
        self._create_dataframe()
        self._format_dataframe()

    def _parse_datastore(self):
        """Parse data from the datastore into datatable.

        Input:
        - self.datastore: datastore.
        - self.config: customized configuration.
        Output:
        - self.datatable: datatable to be generated.
        """

        def _query_datastore(jqexpr, iterdata):
            """Query datastore and return a list."""
            try:
                res = jq(jqexpr).transform(iterdata, multiple_output=True)
                # jq().transform() returns a list of string(s)
            except Exception as e:
                if 'Cannot iterate over null' in str(e):
                    res = [np.nan]
                else:
                    LOG.debug('jqexpr: {}; data: {}'.format(jqexpr, iterdata))
                    LOG.error('Query datastore failed: {}'.format(e))
                    exit(1)

            return res

        # Build the datatable
        self.datatable = []

        for iterdata in self.datastore:
            # Build the row
            row = {}
            split_info = {}

            # Fill elements into the row
            for cfg in self.config.get('columns'):
                name = cfg.get('name')
                method = cfg.get('method')

                if method == 'query_metadata':
                    # Query metadata
                    row[name] = self.metadata.get(cfg['key'])

                elif method == 'query_datastore':
                    # Query datastore
                    res = _query_datastore(cfg['jqexpr'], iterdata)

                    # Process data
                    if 'factor' in cfg:
                        # Multiply the factor if available
                        res = [x * cfg['factor'] for x in res]

                    # Get the object itself if there is only one in the list
                    if len(res) > 1:
                        row[name] = res
                        split_info.setdefault('iter', [])
                        split_info.get('iter').append(
                            {'name': name, 'len': len(res)})
                    else:
                        row[name] = res[0]

                elif method == 'batch_query_datastore':
                    # Batch query datastore
                    array = []
                    for jqexpr in cfg['jqexpr']:
                        res = _query_datastore(jqexpr, iterdata)
                        data = res if len(res) > 1 else res[0]
                        array.append(data)

                    try:
                        row[name] = cfg['format'] % tuple(array)
                    except Exception as e:
                        LOG.error('format: "{}"; data: {}'.format(
                            cfg['format'], array))
                        LOG.error('Failed to format string: {}'.format(e))
                        exit(1)

                elif method == 'get_sample':
                    # Get value for "Sample"
                    row[name] = 'all'
                    split_info.update({'name': {'sample': name}})

                elif method == 'get_source_url':
                    # Get value for "SourceURL"
                    external_url = iterdata.get('external_url')

                    if external_url:
                        row[name] = '{}/{}'.format(external_url,
                                                   iterdata['path_lv_2'])
                    else:
                        row[name] = '{}/{}'.format(iterdata['path_lv_1'],
                                                   iterdata['path_lv_2'])
                    split_info.update({'name': {'source_url': name}})

                else:
                    LOG.error('Unsupported method in config: {}'.format(cfg))
                    exit(1)

            # Check if this row need to be splitted
            if not self.config.get('defaults', {}).get('split'):
                # No need to split, append directly
                self.datatable.append(row.copy())
                continue

            if not split_info.get('iter'):
                # Nothing to be splitted, append directly
                self.datatable.append(row.copy())
                continue

            # Split this row
            split_names = [x['name'] for x in split_info.get('iter', [])]
            split_nblen = [x['len'] for x in split_info.get('iter', [])]
            max_sample = max(split_nblen)

            # Criteria check
            if max_sample != min(split_nblen):
                LOG.warning('The row cannot be splitted gracefully. '
                            'Row: {}'.format(row))
                # Cannot be splitted gracefully, append directly
                self.datatable.append(row.copy())
                continue

            # Split into subrows
            for index in range(1, max_sample + 1):
                subrow = {}
                # Deal with each element
                for name, value in row.items():
                    if name in split_names:
                        subrow[name] = value[index-1]
                    else:
                        subrow[name] = value

                # Update special elements
                sample_name = split_info.get('name', {}).get('sample')
                if sample_name:
                    subrow[sample_name] = index

                source_url_name = split_info.get('name', {}).get('sample')
                if source_url_name:
                    subrow[source_url_name] = '{}/sample{}'.format(
                        row[source_url_name], index)

                # Append the subrow
                self.datatable.append(subrow.copy())

    def _create_dataframe(self):
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
