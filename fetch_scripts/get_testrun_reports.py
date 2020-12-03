#!/usr/bin/env python
"""
Get TestRun Reports for pbench-fio test.
"""

import argparse
import logging
import json
import os
import pandas as pd

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(message)s')

ARG_PARSER = argparse.ArgumentParser(description="Generate benchmark CSV")
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


class testrun_reporter():
    """Generate TestRun Reports from specified directory with raw data."""
    def __init__(self, ARGS):
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

        self.dataframe = None
        self._build_dataframe()

    def _build_dataframe(self):
        table = []
        for iterdata in self.datastore:
            data = {}

            # get keys
            data['RW'] = iterdata['iteration_data']['parameters']['benchmark'][
                0]['rw']
            data['BS'] = iterdata['iteration_data']['parameters']['benchmark'][
                0]['bs']
            data['IODepth'] = iterdata['iteration_data']['parameters'][
                'benchmark'][0]['iodepth']
            data['Numjobs'] = iterdata['iteration_data']['parameters'][
                'benchmark'][0]['numjobs']

            # get kpis
            for client in iterdata['iteration_data']['throughput']['iops_sec']:
                if client['client_hostname'] == 'all':
                    iops = [x['value'] for x in client['samples']]
            for client in iterdata['iteration_data']['latency']['lat']:
                if client['client_hostname'] == 'all':
                    lat = [x['value'] / 1000000 for x in client['samples']]
            for client in iterdata['iteration_data']['latency']['clat']:
                if client['client_hostname'] == 'all':
                    clat = [x['value'] / 1000000 for x in client['samples']]

            # split into per sample
            data['Sample'] = 0
            for data['IOPS'], data['LAT(ms)'], data['CLAT(ms)'] in zip(
                    iops, lat, clat):
                data['Sample'] += 1
                data['Path'] = os.path.join(iterdata['path_lv_1'],
                                            iterdata['path_lv_2'],
                                            'sample%d' % data['Sample'])

                # save this item
                table.append(data.copy())

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
    report = testrun_reporter(ARGS)
    report.show_vars()
    report.dump_to_csv()

exit(0)
