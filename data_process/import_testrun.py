#!/usr/bin/env python
"""Import externel data from pbench-server as a TestRun."""

import argparse
import logging
import json

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

ARG_PARSER = argparse.ArgumentParser(
    description="Import externel data from pbench-server as a TestRun.")
ARG_PARSER.add_argument('--url',
                        dest='url',
                        action='append',
                        help='The URL to the externel data source.',
                        default=None,
                        required=True)
ARG_PARSER.add_argument('--metadata',
                        dest='metadata',
                        action='store',
                        help='The metadata file of the TestRun.',
                        default=None,
                        required=True)

ARGS = ARG_PARSER.parse_args()

if __name__ == '__main__':
    # Parse params
    externel_urls = ARGS.url

    with open(ARGS.metadata, 'r') as f:
        metadata = json.load(f)

    # Get TestRun ID
    testrun_id = metadata.get('testrun-id')

exit(0)
