#!/usr/bin/env python
"""Import externel data from pbench-server as a TestRun."""

import argparse
import logging
import json
import yaml
import os
import shutil
import urllib.request

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


def download_file(from_url, to_file):
    """Download file from specified URL."""

    try:
        logging.debug('Downloading from URL "{}" to "{}".'.format(
            from_url, to_file))
        urllib.request.urlretrieve(from_url, filename=to_file)
        return 0
    except Exception as e:
        logging.warning('Failed to download the file: {}'.format(e))
        return 1


def create_redirect_html(externel_url,
                         output_path='.',
                         filename=None,
                         wait_sec=1):
    """Create an html file for redirecting to a specified URL."""
    logging.debug('Creating redirect html for "{}".'.format(externel_url))

    if filename is None:
        # Determine the filename from externel_url
        filename = os.path.basename(externel_url.strip('/')) + '.html'
    output_file = os.path.join(output_path, filename)

    html_content = '''
<head><meta http-equiv="refresh" content="{0};url={1}"></head>
<body>Redirecting to <a href="{1}">{1}</a></body>
'''.format(wait_sec, externel_url)

    with open(output_file, 'w') as f:
        f.write(html_content)


if __name__ == '__main__':

    # Get user config
    with open(os.path.expanduser('~/.perf-insight.yaml'), 'r') as f:
        user_config = yaml.safe_load(f)

    PERF_INSIGHT_ROOT = user_config.get(
        'global', {}).get('perf_insight_root') or '/nfs/perf-insight'
    PERF_INSIGHT_REPO = user_config.get(
        'global', {}).get('perf_insight_repo') or '/opt/perf-insight'

    # Parse params
    ARGS = ARG_PARSER.parse_args()
    externel_urls = ARGS.url

    with open(ARGS.metadata, 'r') as f:
        metadata = json.load(f)

    # Get TestRun ID and path
    testrun_id = metadata.get('testrun-id')
    testrun_path = os.path.join(PERF_INSIGHT_ROOT, 'testruns', testrun_id)

    # Verify TestRun ID and path
    if not testrun_id.startswith(('fio_', 'uperf_')):
        logging.error('Invalid TestRun ID "{}".'.formart(testrun_id))
        exit(1)

    if os.path.exists(testrun_path):
        logging.error('"{}" already exists, exit!'.format(testrun_path))
        exit(1)

    # Create workspace
    workspace = testrun_path + '.tmp'
    if os.path.exists(workspace):
        shutil.rmtree(workspace, ignore_errors=True)
    os.makedirs(workspace)
    logging.debug('Created workspace "{}".'.format(workspace))

    # Collect external data
    logging.info('Collecting external data.')
    for externel_url in externel_urls:
        # Download result.json to workspace
        entities = [x for x in externel_url.split('/') if x]
        folder_name = entities[-1] if entities else 'unknown_foldername'
        folder_path = os.path.join(workspace, folder_name)
        os.makedirs(folder_path)

        file_url = externel_url + '/result.json'
        file_path = folder_path + '/result.json'
        download_file(file_url, file_path)

        # Create redirect html
        create_redirect_html(externel_url, output_path=workspace)

    # Gather datastore
    logging.info('Gathering datastore.')
    cmd = '{}/data_process/gather_testrun_datastore.py \
        --logdir {} --output {}'.format(PERF_INSIGHT_REPO, workspace,
                                        workspace + '/datastore.json')
    logging.debug('Run command: {}'.format(cmd))
    res = os.system(cmd)
    if res > 0:
        logging.error('Command failed.')
        exit(1)

    # Remove subfolders
    logging.info('Removing subfolders.')
    for d in os.listdir(workspace):
        dname = os.path.join(workspace, d)
        if os.path.isdir(dname) and d.startswith(('fio_', 'uperf_')):
            shutil.rmtree(dname, ignore_errors=True)

    # Save TestRun
    os.rename(workspace, testrun_path)

exit(0)
