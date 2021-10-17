from flask import Flask, request, jsonify
from jupyter_server.auth import passwd
from jupyter_server.auth.security import passwd_check
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
            - list of the dict, or
            - None if something goes wrong.
        """
        studies = []
        search_path = JUPYTER_WORKSPACE

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
            - list of the dict, or
            - None if something goes wrong.
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
                    token = m[3][7:] if m[3].startswith('?token=') else None
                    path = m[4]
                    user = path.split('/')[-1]
                    host = JUPYTER_LAB_HOST
                    port = m[2]
                    url = 'http://{}:{}/lab'.format(host, port)

                    try:
                        with open(os.path.join(path, '.passwd'), 'r') as f:
                            hash = f.readline()
                    except Exception as err:
                        LOG.warning('Unable to get hashed passwd for user "{}". error: {}'.format(
                            user, err))
                        hash = None

                    labs.append({'line': m[0], 'host': host, 'port': port,
                                 'token': token, 'path': path, 'user': user,
                                 'hash': hash, 'url': url})
        except Exception as err:
            msg = 'Failed to read jupyter server list. error: {}'.format(err)
            LOG.error(msg)
            return None

        return labs

    def _get_lab_by_user(self, username):
        """Get information of the running lab by username.

        Restriction: When the user has multiple labs, only the first one will
        be returned. This may cause problems. But the logic of create-lab will
        check the running list, so it will not happen. Only care should be
        taken to prevent users from manually creating labs.

        Input:
            username - Username associated with the lab
        Return:
            - list of the dict, or
            - None if something goes wrong.
        """
        labs = self._get_labs()

        if isinstance(labs, list):
            for lab in labs:
                if lab['user'] == username:
                    return lab

        return None

    def _check_password(self, username, password):
        """Check password for specified user.

        Input:
            username - Username associated with the lab
            password - Password to be checked
        Return:
            - True   - Valid password
            - False  - Something wrong or invalid password
        """
        try:
            with open(os.path.join(
                    JUPYTER_WORKSPACE, username, '.passwd'), 'r') as f:
                hashed_password = f.readline()
        except:
            hashed_password = None

        if hashed_password is None:
            LOG.error('Cannot get hashed password for user "{}".'.format(
                username))
            return False

        if passwd_check(hashed_password, password):
            LOG.info('Password for user "{}" is valid.'.format(username))
            return True
        else:
            LOG.error('Password for user "{}" is invalid.'.format(username))
            return False

    def _create_lab(self, username, password):
        """Start a JupyterLab server for the specified user.

        Restriction: A user can only have one lab, please check it before
        calling this function.

        Input:
            username - Username associated with the lab
            password - Password to be set
        Return:
            - (True, json-block), or
            - (False, message) if something goes wrong.
        """
        # Prepare environment
        workspace = os.path.join(JUPYTER_WORKSPACE, username)
        os.makedirs(workspace, exist_ok=True)

        hashed_passwd = passwd(password)
        with open(os.path.join(workspace, '.passwd'), 'w') as f:
            f.write(hashed_passwd)

        # Determine port
        try:
            min_port = int(JUPYTER_LAB_PORTS.split('-')[0])
            max_port = int(JUPYTER_LAB_PORTS.split('-')[1])
        except Exception as err:
            LOG.warning('Failed to get port range for Jupyter labs.', err)
            min_port = max_port = 8888

        labs = self._get_labs()
        if labs:
            port = max([int(x['port']) for x in labs]) + 1
            if port > max_port:
                msg = 'No more labs can be started. (port range: {}~{})'.format(
                    min_port, max_port)
                LOG.error(msg)
                return False, msg
        else:
            port = min_port

        # Create a Jupyter lab
        cmd = 'jupyter-lab -y --allow-root --no-browser --collaborative \
            --ip 0.0.0.0 --port {} --notebook-dir={} \
            --ServerApp.password_required=True \
            --ServerApp.password=\'{}\' \
            &>>{}/.jupyter.log &'.format(
            port, workspace, hashed_passwd, workspace
        )
        res = os.system(cmd)
        if res > 0:
            msg = 'Failed to create Jupyter lab for user "{}".'.format(
                username)
            LOG.error(msg)
            return False, msg
        else:
            time.sleep(1)
            lab = self._get_lab_by_user(username)
            return True, lab

    def _delete_lab(self, username, password):
        """Stop the JupyterLab server for the specified user.

        Input:
            username - Username associated with the lab
            password - Password to be checked
        Return:
            - (True, json-block), or
            - (False, message) if something goes wrong.
        """
        # Get lab info
        lab = self._get_lab_by_user(username)
        if lab is None:
            msg = 'No lab is associated with user "{}".'.format(username)
            LOG.error(msg)
            return False, msg

        # Verify password
        if not self._check_password(username, password):
            msg = 'Authentication failed with user "{}", operation denied.'.format(
                username)
            LOG.error(msg)
            return False, msg

        # Delete the Jupyter lab
        cmd = 'jupyter server stop {}'.format(lab.get('port'))
        res = os.system(cmd)

        if res > 0:
            msg = 'Failed to delete lab "{}" for user "{}".'.format(
                lab.get('port'), username)
            LOG.error(msg)
            return False, msg
        else:
            lab_safe = {
                'user': lab.get('user'),
                'host': lab.get('host'),
                'port': lab.get('port'),
                'url': lab.get('url')
            }
            return True, lab_safe

    # Report Functions
    def create_report(self, report_id):
        """Create the benchmark report in staging area.

        Input:
            report_id - the benchmark report ID
        Return:
            - (True, json-block), or
            - (False, message) if something goes wrong.
        """
        # Criteria check
        source = os.path.join(PERF_INSIGHT_ROOT, 'reports', report_id)
        if os.path.isdir(source):
            msg = 'Report ID "{}" already exists.'.format(id)
            LOG.error(msg)
            return False, msg

        workspace = os.path.join(PERF_INSIGHT_STAG, report_id)
        if not os.path.isdir(workspace):
            msg = 'Folder "{}" can not be found in staging area.'.format(id)
            LOG.error(msg)
            return False, msg

        # Create the report html
        cmd = '{}/data_process/generate_report.sh {} &>{}/generate_report.log'.format(
            PERF_INSIGHT_REPO, workspace, workspace)
        res = os.system(cmd)

        if res > 0:
            msg = 'Failed to generate report html, see generate_report.log for more details.'
            LOG.error(msg)
            return False, msg

        return True, {}

    # Lab Functions
    def query_labs(self):
        """Query information of the running labs.

        Input:
            None
        Return:
            - (True, json-block), or
            - (False, message) if something goes wrong.
        """
        labs = self._get_labs()

        if labs is None:
            msg = 'Failed to query information of the running labs.'
            LOG.error(msg)
            return False, msg

        # Remove sensitive information
        labs_safe = []
        for lab in labs:
            labs_safe.append({
                'user': lab.get('user'),
                'host': lab.get('host'),
                'port': lab.get('port'),
                'url': lab.get('url')
            })

        return True, {'labs': labs_safe}

    def create_lab(self, username, password):
        """Create a Jupyter lab for the specified user.

        Input:
            username - Username associated with the lab
            password - Password to be set
        Return:
            - (True, json-block), or
            - (False, message) if something goes wrong.
        """
        if self._get_lab_by_user(username):
            msg = 'Only one lab can be created for user "{}".'.format(username)
            LOG.error(msg)
            return False, msg

        res, con = self._create_lab(username, password)

        if res:
            # Remove sensitive information from lab info
            lab_safe = {
                'user': con.get('user'),
                'host': con.get('host'),
                'port': con.get('port'),
                'url': con.get('url')
            }
            return True, lab_safe
        else:
            return res, con

    def delete_lab(self, username, password):
        """Delete a Jupyter lab for the specified user.

        Input:
            username - Username associated with the lab
            password - Password to be checked
        Return:
            - (True, json-block), or
            - (False, message) if something goes wrong.
        """
        res, con = self._delete_lab(username, password)

        if res:
            # Remove sensitive information from lab info
            lab_safe = {
                'user': con.get('user'),
                'host': con.get('host'),
                'port': con.get('port'),
                'url': con.get('url')
            }
            return True, lab_safe
        else:
            return res, con

    # Study Functions

    def query_studies(self):
        """Query information of the current studies.

        Input:
            None
        Return:
            - (True, json-block), or
            - (False, message) if something goes wrong.
        """
        studies = self._get_studies()
        if studies is not None:
            return True, {'studies': studies}
        else:
            msg = 'Failed to query the current studies.'
            LOG.error(msg)
            return False, msg

    def start_study(self, report_id, username, password):
        """Start a study for a specified user.

        Input:
            report_id - Report ID to be studied
            username  - Username associated with the lab
            password  - Password to be set/checked
        Return:
            - (True, json-block), or
            - (False, message) if something goes wrong.
        """
        # Check if the report exists
        source = os.path.join(PERF_INSIGHT_ROOT, 'reports', report_id)
        if not os.path.isdir(source):
            msg = 'Report "{}" does not exist.'.format(id)
            LOG.error(msg)
            return False, msg

        # Check if the report is available for checking out
        studies = self._get_studies()
        if studies is None:
            msg = 'Failed to query the current studies.'
            LOG.error(msg)
            return False, msg

        users = [x['user'] for x in studies if x['id'] == report_id]
        if users:
            # Report has been checked out
            msg = 'Report "{}" is being studied by user "{}".'.format(
                report_id, ', '.join(users))
            LOG.error(msg)
            return False, msg

        # Check if the user already have a Jupyter lab
        if self._get_lab_by_user(username):
            # Verify password
            if not self._check_password(username, password):
                msg = 'Authentication failed with user "{}", operation denied.'.format(
                    username)
                LOG.error(msg)
                return False, msg
        else:
            # Create a Jupyter lab for the user
            res, con = self._create_lab(username, password)
            if res is False:
                return False, con

        # Check out the report
        try:
            lab = self._get_lab_by_user(username)
            os.symlink(source, os.path.join(lab['path'], report_id))
        except Exception as err:
            msg = 'Failed to check out report "{}" for user "{}". error: {}'.format(
                report_id, username, err)
            LOG.error(msg)
            return False, msg

        # Compile return data
        data = {
            'id': report_id,
            'user': username,
            'lab_info': {
                'host': lab.get('host'),
                'port': lab.get('port'),
                'url': lab.get('url')}
        }

        return True, data

    def stop_study(self, report_id, username, password):
        """Stop the study for a specified user.

        Input:
            report_id - Report ID to be studied
            username  - Username associated with the lab
            password  - Password to be checked
        Return:
            - (True, json-block), or
            - (False, message) if something goes wrong.
        """
        # Check if the report is checked out by the user
        studies = self._get_studies()
        if studies is None:
            msg = 'Failed to query the current studies.'
            LOG.error(msg)
            return False, msg

        users = [x['user'] for x in studies if x['id'] == report_id]
        if not users:
            # Report has not been checked out
            msg = 'Report "{}" is not being studied by anyone.'.format(
                report_id)
            LOG.error(msg)
            return False, msg

        if username not in users:
            # Report has been checked out by other users
            msg = 'Report "{}" is being studied by someone other than "{}".'.format(
                report_id, username)
            LOG.error(msg)
            return False, msg

        # Verify password
        if not self._check_password(username, password):
            msg = 'Authentication failed with user "{}", operation denied.'.format(
                username)
            LOG.error(msg)
            return False, msg

        # Check in the report
        try:
            os.unlink(os.path.join(JUPYTER_WORKSPACE, username, report_id))
        except Exception as err:
            msg = 'Failed to check in report "{}" for user "{}". error: {}'.format(
                report_id, username, err)
            LOG.error(msg)
            return False, msg

        return True, {'id': report_id, 'user': username}


# Flask
app = Flask(__name__)


@app.post('/reports/<id>')
def create_report(id):
    LOG.info('Received request to create report for "{}".'.format(id))
    res, con = helper.create_report(id)
    if res:
        return jsonify(con), 200
    else:
        return jsonify({'error': con}), 500


@app.get('/labs')
def query_labs():
    LOG.info('Received request to query all Jupyter labs.')
    res, con = helper.query_labs()
    if res:
        return jsonify(con), 200
    else:
        return jsonify({'error': con}), 500


@app.post('/labs')
def create_lab():
    LOG.info('Received request to create a Jupyter lab.')

    if request.is_json:
        req = request.get_json()
    else:
        return jsonify({'error': 'Request must be JSON.'}), 415

    # Parse args
    username = req.get('username')
    if username is None:
        return jsonify({'error': '"username" is missing in request.'}), 415

    password = req.get('password')
    if password is None:
        return jsonify({'error': '"password" is missing in request.'}), 415

    # Execute action
    res, con = helper.create_lab(username, password)
    if res:
        return jsonify(con), 200
    else:
        return jsonify({'error': con}), 500


@app.delete('/labs')
def delete_lab():
    LOG.info('Received request to delete a Jupyter lab.')

    if request.is_json:
        req = request.get_json()
    else:
        return jsonify({'error': 'Request must be JSON.'}), 415

    # Parse args
    username = req.get('username')
    if username is None:
        return jsonify({'error': '"username" is missing in request.'}), 415

    password = req.get('password')
    if password is None:
        return jsonify({'error': '"password" is missing in request.'}), 415

    # Execute action
    res, con = helper.delete_lab(username, password)
    if res:
        return jsonify(con), 200    # use 200 since 204 returns no json
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

    # Parse args
    report_id = req.get('report_id')
    if report_id is None:
        return jsonify({'error': '"report_id" is missing in request.'}), 415

    username = req.get('username')
    if username is None:
        return jsonify({'error': '"username" is missing in request.'}), 415

    password = req.get('password')
    if password is None:
        return jsonify({'error': '"password" is missing in request.'}), 415

    # Execute action
    res, con = helper.start_study(report_id, username, password)

    if res:
        return jsonify(con), 200
    else:
        return jsonify({'error': con}), 500


@app.delete('/studies')
def stop_study():
    LOG.info('Received request to stop a study.')

    if request.is_json:
        req = request.get_json()
    else:
        return jsonify({'error': 'Request must be JSON.'}), 415

    # Parse args
    report_id = req.get('report_id')
    if report_id is None:
        return jsonify({'error': '"report_id" is missing in request.'}), 415

    username = req.get('username')
    if username is None:
        return jsonify({'error': '"username" is missing in request.'}), 415

    password = req.get('password')
    if password is None:
        return jsonify({'error': '"password" is missing in request.'}), 415

    res, con = helper.stop_study(report_id, username, password)
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
JUPYTER_WORKSPACE = config.get('jupyter_workspace', '/app/workspace')
JUPYTER_LAB_HOST = config.get('jupyter_lab_host', 'localhost')
JUPYTER_LAB_PORTS = config.get('jupyter_lab_ports', '8890-8899')

helper = JupyterHelper()
