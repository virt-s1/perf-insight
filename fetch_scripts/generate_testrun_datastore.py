#!/usr/bin/env python
"""
Generate TestRun DataStore from pbench-fio raw data.
"""

import argparse
import logging
import json
import os

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(message)s')

ARG_PARSER = argparse.ArgumentParser(description="Generate TestRun DataStore.")
ARG_PARSER.add_argument('--logdir',
                        dest='logdir',
                        action='store',
                        help='Specify a log dir with TestRun raw data.',
                        default=None,
                        required=False)
ARG_PARSER.add_argument('--testrun',
                        dest='testrun',
                        action='store',
                        help='Specify a TestRun ID.',
                        default=None,
                        required=False)
ARG_PARSER.add_argument('--output',
                        dest='output',
                        action='store',
                        help='Specify a filename.',
                        default=None,
                        required=False)

ARGS = ARG_PARSER.parse_args()

if __name__ == '__main__':

    # parse parameters
    logdir = os.path.realpath(
        ARGS.logdir) if ARGS.logdir is not None else os.getcwd()
    testrun = ARGS.testrun or os.path.basename(logdir)
    output = ARGS.testrun or os.path.join(logdir, 'datastore.json')

    # collect data for datastore
    datastore = []
    for d in os.listdir(logdir):
        if d.startswith(testrun + '_'):
            fname = os.path.join(logdir, d, 'result.json')
            with open(fname, 'r') as f:
                data = json.load(f)

            for idata in data:
                idata['path_lv_1'] = d
                idata['path_lv_2'] = idata['iteration_name_format'] % (
                    idata['iteration_number'], idata['iteration_name'])
            datastore += data

    # dump datastore to file
    with open(output, 'w') as f:
        json.dump(datastore, f, indent=3)
