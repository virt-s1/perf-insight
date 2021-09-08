from flask import Flask, request, jsonify
import logging
import os
import yaml
import json
import shutil
import time
import urllib


class TestRunManager():
    def query_testruns(self):
        """Query all the TestRunIDs from PERF_INSIGHT_ROOT.

        Input:
            None
        Return:
            - (True, json-block), or
            - (False, message) if something goes wrong.
        """

        testruns = []
        valid_prefix = ('fio_', 'uperf_')
        search_path = os.path.join(PERF_INSIGHT_ROOT, 'testruns')

        if not os.path.isdir(search_path):
            msg = 'Path "{}" does not exist.'.format(search_path)
            LOG.error(msg)
            return False, msg

        for entry in os.listdir(search_path):
            if not os.path.isdir(os.path.join(search_path, entry)):
                continue
            if entry.startswith(valid_prefix):
                LOG.debug('Found TestRunID "{}".'.format(entry))
                testruns.append({'id': entry})

        return True, {'testruns': testruns}

    def inspect_testrun(self, id):
        """Inspect a specified TestRunID from PERF_INSIGHT_ROOT.

        Input:
            id - TestRunID
        Return:
            - (True, json-block), or
            - (False, message) if something goes wrong.
        """

        # Criteria check
        search_path = os.path.join(PERF_INSIGHT_ROOT, 'testruns', id)
        if not os.path.isdir(search_path):
            msg = 'TestRunID "{}" does not exist.'.format(id)
            LOG.error(msg)
            return False, msg

        # Get TestRunID
        testrun = {'id': id}

        # Get metadata
        try:
            metadata_file = os.path.join(search_path, 'metadata.json')
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        except Exception as err:
            msg = 'Fail to get metadata from {}. error: {}'.format(
                metadata_file, err)
            LOG.warning(msg)
            metadata = None

        testrun.update({'metadata': metadata})

        # Get datastore
        # try:
        #     datastore_file = os.path.join(search_path, 'datastore.json')
        #     with open(datastore_file, 'r') as f:
        #         datastore = json.load(f)
        # except Exception as err:
        #     msg = 'Fail to get datastore from {}. error: {}'.format(
        #         datastore_file, err)
        #     LOG.warning(msg)
        #     datastore = None

        # testrun.update({'datastore': datastore})

        return True, testrun

    def load_testrun(self, id, generate_plots, create_datastore,
                     update_dashboard):
        """Load TestRun from staging area.

        Input:
            id               - TestRunID
            generate_plots   - [bool] generate plots
            create_datastore - [bool] create datastore
            update_dashboard - [bool] update dashboard
        Return:
            - (True, json-block), or
            - (False, message) if something goes wrong.
        """

        # Criteria check
        target = os.path.join(PERF_INSIGHT_ROOT, 'testruns', id)
        if os.path.isdir(target):
            msg = 'TestRunID "{}" already exists.'.format(id)
            LOG.error(msg)
            return False, msg

        workspace = os.path.join(PERF_INSIGHT_STAG, id)
        if not os.path.isdir(workspace):
            msg = 'Folder "{}" can not be found in staging area.'.format(id)
            LOG.error(msg)
            return False, msg

        # Get TestRunID and metadata
        testrun = {'id': id}

        try:
            metadata_file = os.path.join(workspace, 'metadata.json')
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        except Exception as err:
            msg = 'Fail to get metadata from {}. error: {}'.format(
                metadata_file, err)
            LOG.error(msg)
            return False, msg

        testrun.update({'metadata': metadata})

        # Perform data process
        if generate_plots:
            res, msg = self._generate_plots(workspace)
            if res is False:
                return False, msg

        if create_datastore:
            res, msg = self._create_datastore(workspace)
            if res is False:
                return False, msg

        if update_dashboard:
            res, msg = self._update_dashboard(workspace)
            if res is False:
                return False, msg

        # Deal with the files
        try:
            shutil.copytree(workspace, target)
            shutil.move(workspace, os.path.join(
                os.path.dirname(workspace),
                '.deleted_after_loading_{}__{}'.format(
                    time.strftime('%y%m%d%H%M%S',
                                  time.localtime()),
                    os.path.basename(workspace))))
        except Exception as err:
            msg = 'Fail to deal with the files. error: {}'.format(err)
            LOG.error(msg)
            return False, msg

        return True, testrun

    def import_testrun(self, id, create_datastore, update_dashboard,
                       metadata, external_urls):
        """Import TestRun from external pbench server.

        Input:
            id               - TestRunID
            create_datastore - [bool] create datastore
            update_dashboard - [bool] update dashboard
            metadata         - [dict] metadata
            external_urls    - [list] external URLs
        Return:
            - (True, json-block), or
            - (False, message) if something goes wrong.
        """

        # Criteria check
        target = os.path.join(PERF_INSIGHT_ROOT, 'testruns', id)
        if os.path.isdir(target):
            msg = 'TestRunID "{}" already exists.'.format(id)
            LOG.error(msg)
            return False, msg

        workspace = os.path.join(PERF_INSIGHT_STAG, id)
        if os.path.isdir(workspace):
            LOG.warning(
                'Folder "{}" already exists in the staging area and will be overwritten.'.format(id))
            shutil.rmtree(workspace, ignore_errors=True)

        testrun_type = metadata.get('testrun-type')
        if testrun_type is None:
            msg = '"testrun-type" must be provisioned in metadata.'
            LOG.error(msg)
            return False, msg
        if testrun_type not in ('fio', 'uperf'):
            msg = 'Unsupported testrun-type "{}" from metadata. Valid types: "fio", "uperf".'.format(
                testrun_type)
            LOG.error(msg)
            return False, msg

        for url in external_urls:
            url = url.strip('/')
            basename = os.path.basename(url)
            if not basename.startswith(testrun_type):
                msg = 'URL with "{}" cannot be handled as "{}" tests.'.format(
                    basename, testrun_type)
                LOG.error(msg)
                return False, msg

        # Create a workspace in the staging area
        os.makedirs(workspace)

        # Retrive data from the URLs
        for url in external_urls:
            url = url.strip('/')
            subfolder = os.path.join(workspace, os.path.basename(url))

            # Download the result.json file
            from_file = url + '/result.json'
            to_file = os.path.join(subfolder, 'result.json')

            LOG.debug('Downloading "{}" as "{}".'.format(from_file, to_file))
            try:
                os.makedirs(subfolder)
                urllib.request.urlretrieve(from_file, to_file)
            except Exception as e:
                msg = 'Failed to download result.json: {}'.format(e)
                LOG.error(msg)
                return False, msg

            # Write down external_url.txt
            with open(os.path.join(subfolder, 'external_url.txt'), 'w') as f:
                f.write(url)

            # Create an html file for redirecting
            LOG.debug('Creating an html file for redirecting "{}".'.format(url))
            filename = os.path.basename(url) + '.html'
            html_content = '''
                <head><meta http-equiv="refresh" content="{0};url={1}"></head>
                <body>Redirecting to <a href="{1}">{1}</a></body>
                '''.format(1, url)

            with open(os.path.join(workspace, filename), 'w') as f:
                f.write(html_content)

        # Update metadata and dump to metadata.json
        if metadata.get('testrun-id') is None:
            metadata['testrun-id'] = id
        elif metadata.get('testrun-id') != id:
            LOG.warning(
                'The "testrun-id" in metadata is mismatched, replace with "{}".'.format(id))
            metadata['testrun-id'] = id

        if metadata.get('external_urls') is None:
            metadata['external_urls'] = external_urls
        elif not isinstance(metadata.get('external_urls'), list) or set(metadata.get('external_urls')) != set(external_urls):
            LOG.warning(
                'The "external_urls" in metadata is mismatched, replace with "{}".'.format(external_urls))
            metadata['external_urls'] = external_urls

        with open(os.path.join(workspace, 'metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=3)

        # Create datastore if needed
        if create_datastore:
            res, msg = self._create_datastore(workspace)
            if res is False:
                return False, msg

        # Update dashboard if needed
        if update_dashboard:
            res, msg = self._update_dashboard(workspace)
            if res is False:
                return False, msg

        # Deal with the files
        try:
            shutil.copytree(workspace, target)
            shutil.move(workspace, os.path.join(
                os.path.dirname(workspace),
                '.deleted_after_importing_{}__{}'.format(
                    time.strftime('%y%m%d%H%M%S',
                                  time.localtime()),
                    os.path.basename(workspace))))
        except Exception as err:
            msg = 'Fail to deal with the files. error: {}'.format(err)
            LOG.error(msg)
            return False, msg

        return True, {'id': id, 'metadata': metadata}

    def _generate_plots(self, workspace):
        """Generate plots for pbench-fio results.
        Input:
            workspace - the path of the workspace.
        Return:
            - (True, None), or
            - (False, message) if something goes wrong.
        """

        LOG.info('Generate plots for pbench-fio results.')

        cmd = '{}/data_process/generate_pbench_fio_plots.sh -d {}'.format(
            PERF_INSIGHT_REPO, workspace)
        res = os.system(cmd)

        if res == 0:
            return True, None
        else:
            msg = 'Fail to generate plots for pbench-fio results.'
            LOG.error(msg)
            return False, msg

    def _create_datastore(self, workspace):
        """Create datastore for the TestRun.
        Input:
            workspace - the path of the workspace.
        Return:
            - (True, None), or
            - (False, message) if something goes wrong.
        """
        LOG.info('Create datastore for the TestRun.')

        cmd = '{}/data_process/gather_testrun_datastore.py --logdir {} \
            --output {}/datastore.json'.format(PERF_INSIGHT_REPO, workspace, workspace)
        res = os.system(cmd)

        if res == 0:
            return True, None
        else:
            msg = 'Create datastore for the TestRun.'
            LOG.error(msg)
            return False, msg

    def _update_dashboard(self, workspace):
        """Update the testrun into dashboard.
        Input:
            workspace - the path of the workspace.
        Return:
            - (True, None), or
            - (False, message) if something goes wrong.
        """
        LOG.info('Update the dashboard database.')

        # Get keywords from metadata
        try:
            f = os.path.join(workspace, 'metadata.json')
            with open(f, 'r') as f:
                m = json.load(f)
            testrun_id = m.get('testrun-id')
            testrun_type = m.get('testrun-type')
            testrun_platform = m.get('testrun-platform')
        except Exception as err:
            msg = 'Fail to get metadata from "{}". error: {}'.format(f, err)
            LOG.error(msg)
            return False, msg

        # Get best config file
        config = os.path.join(workspace, '.testrun_results_dbloader.yaml')
        file_a = 'generate_testrun_results-{}-dbloader-{}.yaml'.format(
            testrun_type, testrun_platform)
        file_b = 'generate_testrun_results-{}-dbloader.yaml'.format(
            testrun_type)
        if os.path.exists(os.path.join(PERF_INSIGHT_TEMP, file_a)):
            shutil.copy(os.path.join(PERF_INSIGHT_TEMP, file_a), config)
        elif os.path.exists(os.path.join(PERF_INSIGHT_TEMP, file_b)):
            shutil.copy(os.path.join(PERF_INSIGHT_TEMP, file_b), config)
        else:
            msg = 'Can not find file "{}" or "{}" in "{}".'.format(
                file_a, file_b, PERF_INSIGHT_TEMP)
            LOG.error(msg)
            return False, msg

        # Create DB loader CSV
        datastore = os.path.join(workspace, 'datastore.json')
        metadata = os.path.join(workspace, 'metadata.json')
        dbloader = os.path.join(workspace, '.testrun_results_dbloader.csv')

        cmd = '{}/data_process/generate_testrun_results.py --config {} --datastore {} \
            --metadata {} --output-format csv --output {}'.format(
            PERF_INSIGHT_REPO, config, datastore, metadata, dbloader)
        res = os.system(cmd)
        if res > 0:
            msg = 'Failed to create DB loader CSV.'
            LOG.error(msg)
            return False, msg

        # Update database
        if os.path.exists(DASHBOARD_DB_FILE):
            db_file = DASHBOARD_DB_FILE
        else:
            msg = 'Can not find the dashboard DB file "{}".'.format(
                DASHBOARD_DB_FILE)
            LOG.error(msg)
            return False, msg

        if testrun_type == 'fio':
            flag = '--storage'
        elif testrun_type == 'uperf':
            flag = '--network'
        else:
            msg = 'Unsupported TestRun Type "{}" for "flask_load_db.py".'.format(
                testrun_type)
            LOG.error(msg)
            return False, msg

        cmd = '{}/data_process/flask_load_db.py {} --db_file {} --delete {}'.format(
            PERF_INSIGHT_REPO, flag, db_file, testrun_id)
        res = os.system(cmd)
        if res > 0:
            msg = 'Failed to clean up specified TestRunID from database.'
            LOG.error(msg)
            return False, msg

        cmd = '{}/data_process/flask_load_db.py {} --db_file {} --csv_file {}'.format(
            PERF_INSIGHT_REPO, flag, db_file, dbloader)
        res = os.system(cmd)
        if res > 0:
            msg = 'Failed to load specified TestRunID into database.'
            LOG.error(msg)
            return False, msg

        return True, None

    def fetch_testrun(self, id):
        """Fetch a specified TestRunID to the staging area.

        Input:
            id - TestRunID
        Return:
            - (True, json-block), or
            - (False, message) if something goes wrong.
        """

        # Criteria check
        target = os.path.join(PERF_INSIGHT_ROOT, 'testruns', id)
        if not os.path.isdir(target):
            msg = 'TestRunID "{}" does not exist.'.format(id)
            LOG.error(msg)
            return False, msg

        # Deal with the files
        try:
            shutil.copytree(target, os.path.join(PERF_INSIGHT_STAG, id))
        except Exception as err:
            msg = 'Fail to deal with the files. error: {}'.format(err)
            LOG.error(msg)
            return False, msg

        return True, {'id': id}

    def delete_testrun(self, id):
        """Delete a specified TestRunID from PERF_INSIGHT_ROOT.

        Input:
            id - TestRunID
        Return:
            - (True, json-block), or
            - (False, message) if something goes wrong.
        """

        # Criteria check
        target = os.path.join(PERF_INSIGHT_ROOT, 'testruns', id)
        if not os.path.isdir(target):
            msg = 'TestRunID "{}" does not exist.'.format(id)
            LOG.error(msg)
            return False, msg

        # Remove from dashboard
        if os.path.exists(DASHBOARD_DB_FILE):
            db_file = DASHBOARD_DB_FILE
        else:
            msg = 'Can not find the dashboard DB file "{}".'.format(
                DASHBOARD_DB_FILE)
            LOG.error(msg)
            return False, msg

        testrun_type = id.split('_')[0]
        if testrun_type == 'fio':
            flag = '--storage'
        elif testrun_type == 'uperf':
            flag = '--network'
        else:
            msg = 'Unsupported TestRun Type "{}" for "flask_load_db.py".'.format(
                testrun_type)
            LOG.error(msg)
            return False, msg

        cmd = '{}/data_process/flask_load_db.py {} --db_file {} --delete {}'.format(
            PERF_INSIGHT_REPO, flag, db_file, id)
        res = os.system(cmd)
        if res > 0:
            msg = 'Failed to clean up specified TestRunID from database.'
            LOG.error(msg)
            return False, msg

        # Deal with the files
        try:
            shutil.move(target, os.path.join(PERF_INSIGHT_STAG, '.deleted_by_user_{}__{}'.format(
                time.strftime('%y%m%d%H%M%S', time.localtime()), id)))
        except Exception as err:
            msg = 'Fail to deal with the files. error: {}'.format(err)
            LOG.error(msg)
            return False, msg

        return True, {'id': id}


LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

app = Flask(__name__)

# Load perf-insight configure
with open(os.path.expanduser('~/.perf-insight.yaml'), 'r') as f:
    user_config = yaml.safe_load(f)

PERF_INSIGHT_ROOT = user_config.get(
    'global', {}).get('perf_insight_root') or '/nfs/perf-insight'
PERF_INSIGHT_REPO = user_config.get(
    'global', {}).get('perf_insight_repo') or '/opt/perf-insight'
PERF_INSIGHT_TEMP = os.path.join(
    PERF_INSIGHT_REPO,  'data_process', 'templates')
PERF_INSIGHT_STAG = os.path.join(PERF_INSIGHT_ROOT, '.staging')
DASHBOARD_DB_FILE = user_config.get('flask', {}).get('db_file')

testrun_manager = TestRunManager()


@app.get('/testruns')
def query_testruns():
    LOG.info('Received request to query all TestRuns.')
    res, con = testrun_manager.query_testruns()
    if res:
        return jsonify(con), 200
    else:
        return jsonify({'error': con}), 500


@app.get('/testruns/<id>')
def inspect_testrun(id):
    LOG.info('Received request to inspect TestRun "{}".'.format(id))
    res, con = testrun_manager.inspect_testrun(id)
    if res:
        return jsonify(con), 200
    else:
        return jsonify({'error': con}), 500


@app.post('/testruns')
def add_testrun():
    if request.is_json:
        req = request.get_json()
    else:
        return jsonify({'error': 'Request must be JSON.'}), 415

    # Parse args
    action = req.get('action')
    if action is None:
        return jsonify({'error': '"action" is missing in request.'}), 415
    elif not action in ('load', 'import'):
        return jsonify({'error': '"action" must be "load" or "import".'}), 415

    id = req.get('id')
    if id is None:
        return jsonify({'error': '"id" is missing in request.'}), 415

    if action == 'load':
        LOG.info('Received request to load TestRun "{}".'.format(id))
    elif action == 'import':
        LOG.info('Received request to import TestRun "{}".'.format(id))

    create_datastore = req.get('create_datastore')
    if create_datastore is None:
        return jsonify({'error': '"create_datastore" is missing in request.'}), 415
    elif not isinstance(create_datastore, bool):
        return jsonify({'error': '"create_datastore" in request must be a bool value.'}), 415

    update_dashboard = req.get('update_dashboard')
    if update_dashboard is None:
        return jsonify({'error': '"update_dashboard" is missing in request.'}), 415
    elif not isinstance(update_dashboard, bool):
        return jsonify({'error': '"update_dashboard" in request must be a bool value.'}), 415

    if action == 'load':
        generate_plots = req.get('generate_plots')
        if generate_plots is None:
            return jsonify({'error': '"generate_plots" is missing in request.'}), 415
        elif not isinstance(generate_plots, bool):
            return jsonify({'error': '"generate_plots" in request must be a bool value.'}), 415

    if action == 'import':
        metadata = req.get('metadata')
        if metadata is None:
            return jsonify({'error': '"metadata" is missing in request.'}), 415
        elif not isinstance(metadata, dict):
            return jsonify({'error': '"metadata" in request must be a json block.'}), 415

        external_urls = req.get('external_urls')
        if external_urls is None:
            return jsonify({'error': '"external_urls" is missing in request.'}), 415
        elif not isinstance(external_urls, list):
            return jsonify({'error': '"external_urls" in request must be a json block.'}), 415

    # Execute action
    if action == 'load':
        res, con = testrun_manager.load_testrun(
            id=id,
            generate_plots=generate_plots,
            create_datastore=create_datastore,
            update_dashboard=update_dashboard)
    elif action == 'import':
        res, con = testrun_manager.import_testrun(
            id=id,
            create_datastore=create_datastore,
            update_dashboard=update_dashboard,
            metadata=metadata,
            external_urls=external_urls)

    if res:
        return jsonify(con), 201
    else:
        return jsonify({'error': con}), 500


@app.put('/testruns/<id>')
def fetch_testrun(id):
    LOG.info('Received request to fetch TestRun "{}".'.format(id))
    res, con = testrun_manager.fetch_testrun(id)
    if res:
        return jsonify(con), 200
    else:
        return jsonify({'error': con}), 500


@app.delete('/testruns/<id>')
def delete_testrun(id):
    LOG.info('Received request to delete TestRun "{}".'.format(id))
    res, con = testrun_manager.delete_testrun(id)
    if res:
        return jsonify(con), 204    # 204 returns nothing in content
    else:
        return jsonify({'error': con}), 500
