#!/usr/bin/env python3
"""
Gather TestRun DataStore from pbench-agent raw data.

Currently supports:
1. pbench-fio
"""

import argparse
import logging
import json
import os

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

ARG_PARSER = argparse.ArgumentParser(description="Gather TestRun DataStore \
from the pbench-agent logs.")
ARG_PARSER.add_argument('--logdir',
                        dest='logdir',
                        action='store',
                        help='Directory with collection of pbench-agent logs, \
the current directory will be used if not specified.',
                        default=None,
                        required=False)
ARG_PARSER.add_argument('--testrun',
                        dest='testrun',
                        action='store',
                        help='TestRun ID, the basename of the logdir will be \
used if not specified. (deprecated)',
                        default=None,
                        required=False)
ARG_PARSER.add_argument('--prefix',
                        dest='prefix',
                        action='store',
                        help='The prefix of the subfolder to be collected. \
"fio_" and "uperf_" will be used if not specified.',
                        default=None,
                        required=False)
ARG_PARSER.add_argument('--drop-failures',
                        dest='drop_failures',
                        action='store',
                        choices=('enforcing', 'restricted', 'permissive'),
                        help='Drop the records which marked as failed runs by \
the pbench-agent. Choose "enforcing" to drop all of ones, choose "restricted" \
to reserve the first one if the case failed all the time, choose "permissive" \
to disable this feature. Default is "restricted".',
                        default='restricted',
                        required=False)
ARG_PARSER.add_argument('--output',
                        dest='output',
                        action='store',
                        help='The name of the json output file.',
                        default='datastore.json',
                        required=False)

if __name__ == '__main__':

    # Parse parameters
    ARGS = ARG_PARSER.parse_args()
    logdir = ARGS.logdir or os.getcwd()
    #testrun = ARGS.testrun or os.path.basename(os.path.abspath(logdir))
    prefix = ARGS.prefix if ARGS.prefix else ('fio_', 'uperf_')
    drop_failures = ARGS.drop_failures
    output = ARGS.output

    # Gather data for the datastore
    logging.info('Gathering datastore.')
    datastore = []

    for d in os.listdir(logdir):
        dname = os.path.join(logdir, d)
        if os.path.isdir(dname) and d.startswith(prefix):
            logging.info('Collecting data from "{}".'.format(d))
            fname = os.path.join(logdir, d, 'result.json')
            with open(fname, 'r') as f:
                data = json.load(f)

            for idata in data:
                idata['path_lv_1'] = d
                idata['path_lv_2'] = idata['iteration_name_format'] % (
                    idata['iteration_number'], idata['iteration_name'])
            datastore += data

    # Drop failures
    if drop_failures in ('enforcing', 'restricted'):
        logging.info('Analyzing and dropping failures.')
        records = datastore.copy()
        datastore.clear()

        for record in records:
            drop_this_record = False

            path_lv_1 = record.get('path_lv_1')
            path_lv_2 = record.get('path_lv_2')

            # drop any failed records in enforcing mode
            if drop_failures == 'enforcing' and '-fail' in path_lv_2:
                drop_this_record = True

            # drop selected failed records in restricted mode
            if drop_failures == 'restricted' and '-fail' in path_lv_2:
                if not path_lv_2.endswith('-fail1'):
                    # drop the second and above failed records
                    drop_this_record = True
                else:
                    # drop the first failed record only when passed one exists
                    for x in records:
                        if x.get('path_lv_1') == path_lv_1 and x.get(
                                'path_lv_2') + '-fail1' == path_lv_2:
                            # found the passed record
                            drop_this_record = True
                            break

            # drop or save this record
            if drop_this_record:
                logging.info('{}/{} has been droped.'.format(
                    path_lv_1, path_lv_2))
            else:
                datastore.append(record)

    # Dump the datastore to a json file
    with open(output, 'w') as f:
        json.dump(datastore, f, indent=3)

    exit(0)
