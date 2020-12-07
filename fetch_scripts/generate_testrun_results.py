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
ARG_PARSER.add_argument('--datastore',
                        dest='datastore',
                        action='store',
                        help='Specify the location of datastore file.',
                        default='datastore.json',
                        required=False)
ARG_PARSER.add_argument('--testrun',
                        dest='testrun',
                        action='store',
                        help='Specify a TestRun ID.',
                        default=None,
                        required=False)
ARG_PARSER.add_argument('--config',
                        dest='config',
                        action='store',
                        help='Specify the yaml config file.',
                        default='generate_testrun_results.yaml',
                        required=False)
ARG_PARSER.add_argument('--output-format',
                        dest='output_format',
                        action='store',
                        help='Specify a output format in [csv, ].',
                        default='csv',
                        required=False)
ARG_PARSER.add_argument('--output',
                        dest='output',
                        action='store',
                        help='Specify a name for the output file.',
                        default=None,
                        required=False)

ARGS = ARG_PARSER.parse_args()


class testrun_report_generator():
    """Generate TestRun Results according to customized configuration."""
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

        # parse parameters
        self.output = ARGS.output
        self.output_format = ARGS.output_format

        if self.output is None and self.output_format == 'csv':
            fpath = os.path.dirname(ARGS.datastore)
            fname = 'testrun_report.csv'
            self.output = os.path.join(fpath, fname)

        # init
        self.datatable = []
        self.dataframe = None
        self._parse_data()
        exit(0)
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
            pass

        def _get_value_datastore(cfg, data=None):
            """Get value(s) from datastore."""
            # jq().transform() returns a list of string(s)
            res = jq(cfg['jqexpr']).transform(data, multiple_output=True)

            # multiply the factor if available
            if 'factor' in cfg:
                res = [x * cfg['factor'] for x in res]

            # return the value or the whole list
            if len(res) == 1:
                return res[0]
            else:
                return res

        def _get_value_auto(cfg, data=None):
            """Caluclate value."""
            pass

        def _get_value_unknown(cfg, data=None):
            """Unknown error."""
            print('ERROR: Unknown type in "source", config = "%s".' % cfg)
            exit(1)

        self.config
        self.datastore
        self.datatable = []

        splits = []
        data = {}

        switch = {
            'metadata': _get_value_metadata,
            'datastore': _get_value_datastore,
            'auto': _get_value_auto,
        }

        # generate rows of the datatable
        for iterdata in self.datastore:
            # generate one row
            for cfg in self.config['columns']:
                name = cfg['name']
                value = switch.get(cfg['source'], _get_value_unknown)(cfg,
                                                                      iterdata)
                print(name, ' = ', value)

                continue

            # # get keys
            # data['RW'] = iterdata['iteration_data']['parameters']['benchmark'][
            #     0]['rw']
            # data['BS'] = iterdata['iteration_data']['parameters']['benchmark'][
            #     0]['bs']
            # data['IODepth'] = iterdata['iteration_data']['parameters'][
            #     'benchmark'][0]['iodepth']
            # data['Numjobs'] = iterdata['iteration_data']['parameters'][
            #     'benchmark'][0]['numjobs']

            # # get kpis
            # for client in iterdata['iteration_data']['throughput']['iops_sec']:
            #     if client['client_hostname'] == 'all':
            #         iops = [x['value'] for x in client['samples']]
            # for client in iterdata['iteration_data']['latency']['lat']:
            #     if client['client_hostname'] == 'all':
            #         lat = [x['value'] / 1000000 for x in client['samples']]
            # for client in iterdata['iteration_data']['latency']['clat']:
            #     if client['client_hostname'] == 'all':
            #         clat = [x['value'] / 1000000 for x in client['samples']]

            # # split into per sample
            # data['Sample'] = 0
            # for data['IOPS'], data['LAT(ms)'], data['CLAT(ms)'] in zip(
            #         iops, lat, clat):
            #     data['Sample'] += 1
            #     data['Path'] = os.path.join(iterdata['path_lv_1'],
            #                                 iterdata['path_lv_2'],
            #                                 'sample%d' % data['Sample'])

            #     # save this item
            #     table.append(data.copy())

    def _build_dataframe(self):

        self.dataframe = pd.DataFrame(table)

    def dump_to_csv(self):
        with open(self.output, 'w') as f:
            f.write(self.dataframe.to_csv())

    def show_vars(self):
        #print(self.output)
        #print(self.output_format)
        #print(self.datastore)
        print(self.dataframe)
        pass


if __name__ == '__main__':
    report = testrun_report_generator(ARGS)
    report.show_vars()
    report.dump_to_csv()

exit(0)
