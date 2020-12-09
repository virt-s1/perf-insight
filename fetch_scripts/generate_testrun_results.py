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
                        help='The json file where stores the datastore.',
                        default='datastore.json',
                        required=False)
ARG_PARSER.add_argument('--metadata',
                        dest='metadata',
                        action='store',
                        help='The json file where stores the metadata.',
                        default='testrun_metadata.json',
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
                        help='The file to store TestRun results.',
                        default=None,
                        required=False)

ARGS = ARG_PARSER.parse_args()


class testrun_results_generator():
    """Generate TestRun Results according to the customized configuration."""
    def __init__(self, ARGS):
        # load config
        codepath = os.path.split(os.path.abspath(__file__))[0]
        filename = os.path.join(codepath, ARGS.config)
        with open(filename, 'r') as f:
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

        if self.output is None and self.output_format == 'csv':
            fpath = os.path.dirname(ARGS.datastore)
            fname = 'testrun_results.csv'
            self.output = os.path.join(fpath, fname)

        # init
        self.datatable = []
        self.dataframe = None
        self._parse_data()
        self._build_dataframe()

    def _parse_data(self):
        """Parse data from the datastore.

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
                # get name and unit
                name = cfg.get('name')
                unit = cfg.get('unit')
                if unit:
                    name = '%s(%s)' % (name, unit)

                # get and set value(s)
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
        self.dataframe = pd.DataFrame(self.datatable)

    def dump_to_csv(self):
        with open(self.output, 'w') as f:
            f.write(self.dataframe.to_csv())

    def show_vars(self):
        print(self.output)
        print(self.output_format)
        print(self.datastore)
        print(self.dataframe)
        pass


if __name__ == '__main__':
    gen = testrun_results_generator(ARGS)
    gen.dump_to_csv()

exit(0)
