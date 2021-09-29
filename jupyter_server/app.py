from flask import Flask, request, jsonify
import logging
import os
import yaml
import re
import json
import shutil
import time
import urllib


class JupyterHelper():
    # Shared functions
    def _get_studies(self):
        """Get information of current studies.

        Input:
            None
        Return:
            - list or None
        """
        studies = []
        search_path = JUPYTERLAB_WORKSPACE

        if not os.path.isdir(search_path):
            msg = 'Path "{}" does not exist.'.format(search_path)
            LOG.error(msg)
            return None

        for user in os.listdir(search_path):
            if not os.path.isdir(os.path.join(search_path, user)):
                continue
            for id in os.listdir(os.path.join(search_path, user)):
                if not id.startswith('benchmark_'):
                    continue
                if os.path.islink(os.path.join(search_path, user, id)):
                    LOG.debug(
                        'Found study "{}" for user "{}".'.format(id, user))
                    studies.append({'id': id, 'user': user})

        return studies

    def _get_labs(self):
        """Get information of the running labs.

        Input:
            None
        Return:
            - list or None
        """
        labs = []

        with os.popen('jupyter server list') as p:
            output = p.readlines()

        # Ex1: 'http://hostname:8888/ :: /app/workspace/cheshi'
        # Ex2: 'http://hostname:8888/?token=b298...d8 :: /app/workspace/cheshi'
        re_labinfo = re.compile(r'^http://(\S+):(\d+)/(\S*) :: (\S+)$')

        try:
            for line in output:
                m = re_labinfo.match(line.strip())
                if m:
                    token = m[3][7:] if m[3].startswith('?token=') else ''
                    user = m[4].split('/')[-1]

                    labs.append({'line': m[0], 'host': m[1], 'port': m[2],
                                 'token': token, 'dir': m[4], 'user': user})
        except Exception as err:
            msg = 'Fail to parse output from "{}". error: {}'.format(
                cmd, err)
            LOG.error(msg)
            return None

        return labs

    def _start_lab(self):
        """Start a JupyterLab server for a specified user.

        Input:
            user - Username associated with the lab
        Return:
            - (True, json-block), or
            - (False, message) if something goes wrong.
        """
        pass

    def _stop_lab(self):
        """Stop the JupyterLab server for a specified user.

        Input:
            user - Username associated with the lab
        Return:
            - (True, json-block), or
            - (False, message) if something goes wrong.
        """
        pass

    # Report Functions
    def create_report(self, id):
        """Create the benchmark report in staging area.

        Input:
            id - Benchmark ID
        Return:
            - (True, json-block), or
            - (False, message) if something goes wrong.
        """
        pass

    # Study Functions
    def query_studies(self):
        """Query information of the current studies.

        Input:
            user - Owner of the study
        Return:
            - (True, json-block), or
            - (False, message) if something goes wrong.
        """
        studies = self._get_studies()
        if studies is not None:
            return True, studies
        else:
            msg = 'Failed to query information of the current studies.'
            LOG.error(msg)
            return False, msg

    def start_study(self):
        """Start a study for a specified user.

        Input:
            user - Owner of the study
        Return:
            - (True, json-block), or
            - (False, message) if something goes wrong.
        """
        labs = self._get_labs()
        if labs is not None:
            return True, labs
        else:
            msg = 'Failed to query information of the running labs.'
            LOG.error(msg)
            return False, msg

    def stop_study(self):
        """Stop the study for a specified user.

        Input:
            user - Owner of the study
        Return:
            - (True, json-block), or
            - (False, message) if something goes wrong.
        """
        pass


# Flask
app = Flask(__name__)


@app.put('/reports/<id>')
def create_report(id):
    LOG.info('Received request to create report for "{}".'.format(id))
    res, con = helper.create_report(id)
    if res:
        return jsonify(con), 200
    else:
        return jsonify({'error': con}), 500


@app.get('/studies')
def query_studies():
    LOG.info('Received request to query all studies.')
    res, con = helper.query_studies()
    if res:
        return jsonify(con), 200
    else:
        return jsonify({'error': con}), 500


@app.post('/studies')
def start_study():
    LOG.info('Received request to start a study.')
    if request.is_json:
        req = request.get_json()
    else:
        return jsonify({'error': 'Request must be JSON.'}), 415

    res, con = helper.start_study()

    if res:
        return jsonify(con), 201
    else:
        return jsonify({'error': con}), 500


@app.delete('/studies/<id>')
def stop_study(id):
    LOG.info('Received request to stop a study.')
    res, con = helper.stop_study(id)
    if res:
        return jsonify(con), 200    # use 200 since 204 returns no json
    else:
        return jsonify({'error': con}), 500


# Main
LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')


# Load perf-insight configure
with open(os.path.expanduser('~/.perf-insight.yaml'), 'r') as f:
    user_config = yaml.safe_load(f)

config = user_config.get('global', {})
config.update(user_config.get('jupyter', {}))

PERF_INSIGHT_ROOT = config.get('perf_insight_root', '/mnt/perf-insight')
PERF_INSIGHT_REPO = config.get('perf_insight_repo', '/opt/perf-insight')
PERF_INSIGHT_STAG = os.path.join(PERF_INSIGHT_ROOT, '.staging')
JUPYTERLAB_WORKSPACE = config.get('jupyterlab_workspace', '/app/workspace')

helper = JupyterHelper()
