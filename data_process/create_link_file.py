#!/usr/bin/env python
"""Create an html file for redirecting to the externel data source."""

import argparse
import logging

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(message)s')

ARG_PARSER = argparse.ArgumentParser(
    description="Create an html file for redirecting to the externel data \
source.")
ARG_PARSER.add_argument('--url',
                        dest='url',
                        action='store',
                        help='The URL to the externel data source.',
                        default=None,
                        required=True)
ARG_PARSER.add_argument('--file',
                        dest='file',
                        action='store',
                        help='Write to the specified file.',
                        default=None,
                        required=False)
ARG_PARSER.add_argument('--wait_sec',
                        dest='wait_sec',
                        action='store',
                        help='Seconds to wait before redirecting (default=1).',
                        type=int,
                        default=1,
                        required=False)

ARGS = ARG_PARSER.parse_args()

# parse params
externel_url = str(ARGS.url)

if ARGS.file:
    filename = ARGS.file
else:
    entities = [x for x in externel_url.split('/') if x]
    filename = entities[-1] if entities else 'externel_datasource'
    filename = filename + '_link.html'

wait_sec = ARGS.wait_sec


def write():
    """Create an html file for redirecting."""
    html_content = '''
<head><meta http-equiv="refresh" content="{0};url={1}"></head>
<body>Redirecting to <a href="{1}">{1}</a></body>
'''.format(wait_sec, externel_url)

    with open(filename, 'w') as f:
        f.write(html_content)


if __name__ == '__main__':
    write()

exit(0)
