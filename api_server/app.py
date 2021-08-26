from flask import Flask, request, jsonify
import logging
import os
import yaml
import json
import shutil


class TestRunManager():
    def query_testruns(self):
        """Query all the TestRunIDs from PERF_INSIGHT_ROOT.

        Input:
            None
        Return:
            A list of TestRunIDs.
        """

        testruns = []
        valid_prefix = ('fio_', 'uperf_')
        search_path = os.path.join(PERF_INSIGHT_ROOT, 'testruns')

        if not os.path.isdir(search_path):
            return testruns

        for entry in os.listdir(search_path):
            if not os.path.isdir(os.path.join(search_path, entry)):
                continue
            if entry.startswith(valid_prefix):
                LOG.debug('Found TestRunID "{}".'.format(entry))
                testruns.append({'id': entry})

        return testruns

    def inspect_testrun(self, id):
        """Inspect a specified TestRunID from PERF_INSIGHT_ROOT.

        Input:
            id = TestRunID
        Return:
            A dict of TestRun information.
        """

        search_path = os.path.join(PERF_INSIGHT_ROOT, 'testruns', id)
        if not os.path.isdir(search_path):
            return None

        # Get TestRunID
        testrun = {'id': id}

        # # Get datastore
        # try:
        #     datastore_file = os.path.join(search_path, 'datastore.json')
        #     with open(datastore_file, 'r') as f:
        #         datastore = json.load(f)
        # except Exception as err:
        #     LOG.info('Fail to get datastore from {}. error: {}'.format(
        #         datastore_file, err))
        #     datastore = None
        # testrun.update({'datastore': datastore})

        # Get metadata
        try:
            metadata_file = os.path.join(search_path, 'metadata.json')
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        except Exception as err:
            LOG.info('Fail to get metadata from {}. error: {}'.format(
                metadata_file, err))
            metadata = None
        testrun.update({'metadata': metadata})

        return testrun

    def load_testrun(self, id, generate_plots, create_datastore, update_dashboard):
        """Load TestRun from staged eara.

        Input:
            request - the request json.
        Return:
            True or False if something goes wrong.
        """

        # Criteria check
        target = os.path.join(PERF_INSIGHT_ROOT, 'testruns', id)
        if os.path.isdir(target):
            LOG.error('TestRunID "{}" already exists.'.format(id))
            return False

        workspace = os.path.join(PERF_INSIGHT_ROOT, '.staged', id)
        if not os.path.isdir(workspace):
            LOG.error('Folder "{}" can not be found in staged eara.'.format(id))
            return False

        # Get TestRunID and metadata
        testrun = {'id': id}

        try:
            metadata_file = os.path.join(workspace, 'metadata.json')
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        except Exception as err:
            LOG.error('Fail to get metadata from {}. error: {}'.format(
                metadata_file, err))
            return False

        testrun.update({'metadata': metadata})

        # Perform data process
        if generate_plots:
            res = self._generate_plots(workspace)
            if res is False:
                return False

        if create_datastore:
            res = self._create_datastore(workspace)
            if res is False:
                return False

        if update_dashboard:
            res = self._update_dashboard(workspace)
            if res is False:
                return False

        # Deal with the files
        try:
            shutil.copytree(workspace, target)
            staged_eara = os.path.join(PERF_INSIGHT_ROOT, '.staged')
            shutil.move(os.path.join(staged_eara, id), os.path.join(
                staged_eara, '.deleted_after_loading__{}'.format(id)))
        except Exception as err:
            LOG.error('Fail to deal with the files. error: {}'.format(err))
            return False

        return True

    def import_testrun(self, request):
        """Import TestRun from external pbench server.

        Input:
            request - the request json.
        Return:
            True or False if something goes wrong.
        """
        # TODO: need to implement 'import_testrun()'.
        pass

    def _generate_plots(self, workspace):
        """Generate plots for pbench-fio results.
        Input:
            workspace - the path of the workspace.
        Return:
            True or False if something goes wrong.
        """
        LOG.info('Generate plots for pbench-fio results.')

        cmd = '{}/data_process/generate_pbench_fio_plots.sh -d {}'.format(
            PERF_INSIGHT_REPO, workspace)
        res = os.system(cmd)

        return True if res == 0 else False

    def _create_datastore(self, workspace):
        """Create datastore for the TestRun.
        Input:
            workspace - the path of the workspace.
        Return:
            True or False if something goes wrong.
        """
        LOG.info('Create datastore for the TestRun.')

        cmd = '{}/data_process/gather_testrun_datastore.py --logdir {} \
--output {}/datastore.json'.format(PERF_INSIGHT_REPO, workspace, workspace)
        res = os.system(cmd)

        return True if res == 0 else False

    def _update_dashboard(self, workspace):
        """Update the testrun into dashboard.
        Input:
            workspace - the path of the workspace.
        Return:
            True or False if something goes wrong.
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
            LOG.error('Fail to get metadata from {}. error: {}'.format(f, err))
            return False

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
            LOG.error('Can not find file {} or {} in {}.'.format(
                file_a, file_b, PERF_INSIGHT_TEMP))
            return False

        # Create DB loader CSV
        datastore = os.path.join(workspace, 'datastore.json')
        metadata = os.path.join(workspace, 'metadata.json')
        dbloader = os.path.join(workspace, '.testrun_results_dbloader.csv')

        cmd = '{}/data_process/generate_testrun_results.py --config {} --datastore {} \
--metadata {} --output-format csv --output {}'.format(
            PERF_INSIGHT_REPO, config, datastore, metadata, dbloader)
        res = os.system(cmd)
        if res > 0:
            LOG.error('Failed to create DB loader CSV.')
            return False

        # Update database
        if os.path.exists(DASHBOARD_DB_FILE):
            db_file = DASHBOARD_DB_FILE
        else:
            LOG.error('Can not find the dashboard DB file {}'.format(
                DASHBOARD_DB_FILE))
            return False

        if testrun_type == 'fio':
            flag = '--storage'
        elif testrun_type == 'uperf':
            flag = '--network'
        else:
            LOG.error('Unsupported TestRun Type "{}".'.format(testrun_type))
            return False

        cmd = '{}/data_process/flask_load_db.py {} --db_file {} --delete {}'.format(
            PERF_INSIGHT_REPO, flag, db_file, testrun_id)
        res = os.system(cmd)
        if res > 0:
            return False

        cmd = '{}/data_process/flask_load_db.py {} --db_file {} --csv_file {}'.format(
            PERF_INSIGHT_REPO, flag, db_file, dbloader)
        res = os.system(cmd)
        if res > 0:
            return False

        return True


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
DASHBOARD_DB_FILE = user_config.get('flask', {}).get('db_file')

testrun_manager = TestRunManager()


@app.get('/testruns')
def query_testruns():
    result = testrun_manager.query_testruns()
    return jsonify({'testruns': {'testrun': result}}), 200


@app.get('/testruns/<id>')
def inspect_testrun(id):
    result = testrun_manager.inspect_testrun(id)
    if result is None:
        return jsonify({'error': 'The requested resource was not found.'}), 404
    else:
        return jsonify({'testrun': result}), 200


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

    generate_plots = req.get('generate_plots')
    if generate_plots is None:
        return jsonify({'error': '"generate_plots" is missing in request.'}), 415
    elif not isinstance(generate_plots, bool):
        return jsonify({'error': '"generate_plots" in request must be a bool value.'}), 415

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

    # Execute action
    if action == 'load':
        res = testrun_manager.load_testrun(
            id=id,
            generate_plots=generate_plots,
            create_datastore=create_datastore,
            update_dashboard=update_dashboard)
    elif action == 'import':
        res = testrun_manager.import_testrun(req)

    if res is False:
        return jsonify({'error': 'Internal error.'}), 500

    return jsonify(req), 201
