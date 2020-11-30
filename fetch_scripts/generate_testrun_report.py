#!/usr/bin/env python
"""
Generate TestRun Reports from specified directory with raw data.
This script will generate the following reports:
1. $TestRunId_report.csv
"""

import argparse
import logging
import json
import re
import os
import pandas as pd

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(message)s')

ARG_PARSER = argparse.ArgumentParser(description="Generate benchmark CSV")
ARG_PARSER.add_argument('--dir',
                        dest='dir',
                        action='store',
                        help='The raw ouput directory of the test samples.',
                        default=None,
                        required=True)
ARG_PARSER.add_argument('--testrun',
                        dest='runid',
                        action='store',
                        help='The ID for the specified TestRun.',
                        default=None,
                        required=False)
ARG_PARSER.add_argument('--report_csv',
                        dest='report_csv',
                        action='store',
                        help='The name of the report csv file.',
                        default=None,
                        required=False)

ARGS = ARG_PARSER.parse_args()


class testrun_reporter():
    """Generate TestRun Reports from specified directory with raw data."""
    def __init__(self, ARGS):
        self.dir = ARGS.dir
        self.runid = ARGS.runid or os.path.basename(self.dir)
        self.report_csv = ARGS.report_csv or '%s_report.csv' % self.runid

        # self.datastore: [{'params': {...}, 'kpis': {...}, 'metadata': {...}}]
        self.datastore = []
        self.df_report = None

        self._load_raw_data()

    def _load_raw_data(self):
        # find all raw data files
        data_files = []
        for root, dirs, files in os.walk(self.dir):
            for name in files:
                if name == 'result.json' and '/sample' in root:
                    data_files.append(os.path.join(root, name))
        data_files.sort()

        # load and append data
        for f in data_files:
            data = self._parse_data(f)
            self.datastore.append(data)

    def _parse_data(self, json_file):

        data = {
            'metadata': {},
            'params': {},
            'kpis': {},
        }

        with open(json_file, 'r') as f:
            raw_data = json.load(f)

        # Get metadata
        data['metadata']['path'] = os.path.dirname(json_file)
        data['metadata']['sample'] = re.search(r'/sample(\d)/',
                                               json_file).group(1)

        # Get params
        data['params'] = raw_data['parameters']['benchmark'][0]

        # Get KPIs: iops / latency / complete latency
        items = raw_data['throughput']['iops_sec']
        for item in items:
            if item['client_hostname'] == 'all':
                data['kpis']['iops'] = item['value']

        items = raw_data['latency']['lat']
        for item in items:
            if item['client_hostname'] == 'all':
                data['kpis']['lat'] = item['value']

        items = raw_data['latency']['clat']
        for item in items:
            if item['client_hostname'] == 'all':
                data['kpis']['clat'] = item['value']

        return (data)

    def dump_vars(self):
        print(self.dir)
        print(self.runid)
        print(self.report_csv)
        print(self.datastore)
        pass


if __name__ == '__main__':
    report = testrun_reporter(ARGS)
    report.dump_vars()

exit(0)
