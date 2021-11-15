from flask import Flask, request, redirect, jsonify
import logging
import os
import yaml
import json
import shutil
import time
import urllib
import requests


class PerfInsightManager():
    # Shared functions
    def _select_file(self, search_path, candidates):
        """Select the first available file from candidates.

        Input:
            search_path - Where to search the candidate
            candidates  - A list of filenames (priority decreases)
        Return:
            - The selected filename, or
            - '' if not found
        """
        LOG.debug('Searching from path "{}"...'.format(search_path))

        for name in candidates:
            if os.path.isfile(os.path.join(search_path, name)):
                LOG.debug('"{}" -> YES'.format(name))
                return name
            else:
                LOG.debug('"{}" -> NO'.format(name))

        LOG.debug('No candidate can be found.')
        return ''

    # TestRun Functions
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

        # Get TestRunID and RawData URL
        url = 'http://{}/perf-insight/testruns/{}/'.format(FILE_SERVER, id)
        testrun = {'id': id, 'url': url}

        # Get metadata
        try:
            metadata_file = os.path.join(search_path, 'metadata.json')
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        except Exception as err:
            msg = 'Failed to get metadata from {}. error: {}'.format(
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
        #     msg = 'Failed to get datastore from {}. error: {}'.format(
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
            msg = 'Folder "{}" can not be found in the staging area.'.format(
                id)
            LOG.error(msg)
            return False, msg

        # Get TestRunID and metadata
        testrun = {'id': id}

        try:
            metadata_file = os.path.join(workspace, 'metadata.json')
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        except Exception as err:
            msg = 'Failed to get metadata from {}. error: {}'.format(
                metadata_file, err)
            LOG.error(msg)
            return False, msg

        testrun.update({'metadata': metadata})

        # Perform data process
        if generate_plots:
            res, msg = self._generate_plots(workspace)
            if res is False:
                return False, msg

        # Create datastore as requested
        if create_datastore:
            res, msg = self._create_datastore(workspace)
            if res is False:
                return False, msg

        # Update dashboard as requested
        if update_dashboard:
            res, msg = self._update_dashboard(workspace)
            if res is False:
                return False, msg

        # Deal with the files
        try:
            if SAFE_MODE:
                shutil.copytree(workspace, target)
                shutil.move(workspace, os.path.join(
                    PERF_INSIGHT_RBIN,
                    '.deleted_after_loading_{}__{}'.format(
                        time.strftime('%y%m%d%H%M%S',
                                      time.localtime()),
                        os.path.basename(workspace))))
            else:
                shutil.move(workspace, target)
        except Exception as err:
            msg = 'Failed to deal with the files. error: {}'.format(err)
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
                msg = 'Failed to download {}: {}'.format(from_file, e)
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

        # Create datastore as requested
        if create_datastore:
            res, msg = self._create_datastore(workspace)
            if res is False:
                return False, msg

        # Update dashboard as requested
        if update_dashboard:
            res, msg = self._update_dashboard(workspace)
            if res is False:
                return False, msg

        # Deal with the files
        try:
            if SAFE_MODE:
                shutil.copytree(workspace, target)
                shutil.move(workspace, os.path.join(
                    PERF_INSIGHT_RBIN,
                    '.deleted_after_importing_{}__{}'.format(
                        time.strftime('%y%m%d%H%M%S',
                                      time.localtime()),
                        os.path.basename(workspace))))
            else:
                shutil.move(workspace, target)
        except Exception as err:
            msg = 'Failed to deal with the files. error: {}'.format(err)
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

        cmd = '{}/utils/generate_pbench_fio_plots.sh -d {}'.format(
            PERF_INSIGHT_REPO, workspace)
        res = os.system(cmd)

        if res == 0:
            return True, None
        else:
            msg = 'Failed to generate plots for pbench-fio results.'
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

        cmd = '{}/utils/gather_testrun_datastore.py --logdir {} \
            --output {}/datastore.json'.format(PERF_INSIGHT_REPO, workspace, workspace)
        res = os.system(cmd)

        if res == 0:
            return True, None
        else:
            msg = 'Failed to create datastore for the TestRun.'
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
            msg = 'Failed to get metadata from "{}". error: {}'.format(f, err)
            LOG.error(msg)
            return False, msg

        # Get template
        config = os.path.join(workspace, '.testrun_results_dbloader.yaml')
        candidates = [
            'generate_testrun_results-{}-{}-dbloader.yaml'.format(
                testrun_type, str(testrun_platform).lower()),
            'generate_testrun_results-{}-dbloader.yaml'.format(
                testrun_type)
        ]
        filename = self._select_file(PERF_INSIGHT_TEMP, candidates)
        if filename:
            shutil.copyfile(os.path.join(PERF_INSIGHT_TEMP, filename),
                            config)
        else:
            return False, 'Cannot find template "{}".'.format(candidates)

        # Create DB loader CSV
        datastore = os.path.join(workspace, 'datastore.json')
        metadata = os.path.join(workspace, 'metadata.json')
        dbloader = os.path.join(workspace, '.testrun_results_dbloader.csv')

        cmd = '{}/utils/generate_testrun_results.py --config {} --datastore {} \
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

        cmd = '{}/utils/flask_load_db.py {} --db_file {} --delete {}'.format(
            PERF_INSIGHT_REPO, flag, db_file, testrun_id)
        res = os.system(cmd)
        if res > 0:
            msg = 'Failed to clean up specified TestRunID from database.'
            LOG.error(msg)
            return False, msg

        cmd = '{}/utils/flask_load_db.py {} --db_file {} --csv_file {}'.format(
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
        source = os.path.join(PERF_INSIGHT_ROOT, 'testruns', id)
        if not os.path.isdir(source):
            msg = 'TestRunID "{}" does not exist.'.format(id)
            LOG.error(msg)
            return False, msg

        target = os.path.join(PERF_INSIGHT_STAG, id)
        if os.path.isdir(target):
            msg = 'Folder "{}" already exists in the staging area.'.format(id)
            LOG.error(msg)
            return False, msg

        # Deal with the files
        try:
            shutil.copytree(source, target)
        except Exception as err:
            msg = 'Failed to deal with the files. error: {}'.format(err)
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

        cmd = '{}/utils/flask_load_db.py {} --db_file {} --delete {}'.format(
            PERF_INSIGHT_REPO, flag, db_file, id)
        res = os.system(cmd)
        if res > 0:
            msg = 'Failed to clean up specified TestRunID from database.'
            LOG.error(msg)
            return False, msg

        # Deal with the files
        try:
            shutil.move(target, os.path.join(PERF_INSIGHT_RBIN, '.deleted_by_user_{}__{}'.format(
                time.strftime('%y%m%d%H%M%S', time.localtime()), id)))
        except Exception as err:
            msg = 'Failed to deal with the files. error: {}'.format(err)
            LOG.error(msg)
            return False, msg

        return True, {'id': id}

    # Benchmark Functions
    def query_benchmarks(self):
        """Query all Benchmark reports from PERF_INSIGHT_ROOT.

        Input:
            None
        Return:
            - (True, json-block), or
            - (False, message) if something goes wrong.
        """

        benchmarks = []
        search_path = os.path.join(PERF_INSIGHT_ROOT, 'reports')

        if not os.path.isdir(search_path):
            msg = 'Path "{}" does not exist.'.format(search_path)
            LOG.error(msg)
            return False, msg

        for entry in os.listdir(search_path):
            if not os.path.isdir(os.path.join(search_path, entry)):
                continue
            if entry.startswith('benchmark_'):
                LOG.debug('Found benchmark "{}".'.format(entry))
                benchmarks.append({'id': entry})

        return True, {'benchmarks': benchmarks}

    def inspect_benchmark(self, id):
        """Inspect a specified benchmark from PERF_INSIGHT_ROOT.

        Input:
            id - Benchmark ID
        Return:
            - (True, json-block), or
            - (False, message) if something goes wrong.
        """

        # Criteria check
        search_path = os.path.join(PERF_INSIGHT_ROOT, 'reports', id)
        if not os.path.isdir(search_path):
            msg = 'Benchmark "{}" does not exist.'.format(id)
            LOG.error(msg)
            return False, msg

        # Get Benchmark ID and Report URL
        url = 'http://{}/perf-insight/reports/{}/report.html'.format(
            FILE_SERVER, id)
        benchmark = {'id': id, 'url': url}

        # Get metadata
        try:
            metadata_file = os.path.join(search_path, 'metadata.json')
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        except Exception as err:
            msg = 'Failed to get metadata from {}. error: {}'.format(
                metadata_file, err)
            LOG.warning(msg)
            metadata = None

        benchmark.update({'metadata': metadata})

        return True, benchmark

    def create_benchmark(self, test_id, base_id, test_yaml=None,
                         base_yaml=None, benchmark_yaml=None,
                         metadata_yaml=None, introduction_md=None,
                         comments=None, update_dashboard=True,
                         allow_overwrite=True):
        """Create benchmark report for the specified TestRuns.

        Input:
            test_id          - TestRun to be checked/compared
            base_id          - TestRun to be used as baseline
            test_yaml        - Configure file to parse the TEST samples
            base_yaml        - Configure file to parse the BASE samples
            benchmark_yaml   - Configure file for the benchmark comparison
            metadata_yaml    - Configure file for the metadata comparison
            introduction_md  - Template for TestRun introduction
            comments         - User comments to the report
            update_dashboard - Update the dashboard or not
            allow_overwrite  - Allow overwrite content in the staging area
        Return:
            - (True, json-block), or
            - (False, message) if something goes wrong.
        """

        # Criteria check
        benchmark = 'benchmark_{}_over_{}'.format(test_id, base_id)
        target = os.path.join(PERF_INSIGHT_ROOT, 'reports', benchmark)
        if os.path.isdir(target):
            msg = 'Benchmark report "{}" already exists.'.format(benchmark)
            LOG.error(msg)
            return False, msg

        for id in (test_id, base_id):
            path = os.path.join(PERF_INSIGHT_ROOT, 'testruns', id)
            if not os.path.isdir(path):
                msg = 'TestRunID "{}" does not exist.'.format(id)
                LOG.error(msg)
                return False, msg
            for file in ('datastore.json', 'metadata.json'):
                path = os.path.join(PERF_INSIGHT_ROOT, 'testruns', id, file)
                if not os.path.exists(path):
                    msg = 'File "{}" does not exist.'.format(path)
                    LOG.error(msg)
                    return False, msg

        test_datastore_file = os.path.join(
            PERF_INSIGHT_ROOT, 'testruns', test_id, 'datastore.json')
        base_datastore_file = os.path.join(
            PERF_INSIGHT_ROOT, 'testruns', base_id, 'datastore.json')
        test_metadata_file = os.path.join(
            PERF_INSIGHT_ROOT, 'testruns', test_id, 'metadata.json')
        base_metadata_file = os.path.join(
            PERF_INSIGHT_ROOT, 'testruns', base_id, 'metadata.json')

        workspace = os.path.join(PERF_INSIGHT_STAG, benchmark)
        if os.path.isdir(workspace):
            if allow_overwrite:
                LOG.warning(
                    'Folder "{}" already exists in the staging area and will be overwritten.'.format(benchmark))
                shutil.rmtree(workspace, ignore_errors=True)
            else:
                msg = 'Folder "{}" already exists in the staging area.'.format(
                    benchmark)
                LOG.error(msg)
                return False, msg

        # Get details from metadata for checking
        try:
            with open(test_metadata_file, 'r') as f:
                test_metadata = json.load(f)
            with open(base_metadata_file, 'r') as f:
                base_metadata = json.load(f)
        except Exception as err:
            msg = 'Failed to get metadata from "{}". error: {}'.format(f, err)
            LOG.error(msg)
            return False, msg

        test_type = test_metadata.get('testrun-type')
        test_platform = test_metadata.get('testrun-platform')
        base_type = base_metadata.get('testrun-type')
        base_platform = base_metadata.get('testrun-platform')

        # Check TestRun types
        if test_type != base_type:
            msg = 'Different tests "{}:{}" cannot be benchmarked.'.format(
                test_type, base_type)

        # Prepare benchmark workspace
        os.makedirs(workspace)

        # Deliver data files
        shutil.copyfile(test_datastore_file,
                        os.path.join(workspace, 'test.datastore.json'))
        shutil.copyfile(base_datastore_file,
                        os.path.join(workspace, 'base.datastore.json'))
        shutil.copyfile(test_metadata_file,
                        os.path.join(workspace, 'test.metadata.json'))
        shutil.copyfile(base_metadata_file,
                        os.path.join(workspace, 'base.metadata.json'))

        # Deploy config files
        candidates = [test_yaml] if test_yaml else [
            'generate_testrun_results-{}-{}.yaml'.format(
                test_type, str(test_platform).lower()),
            'generate_testrun_results-{}.yaml'.format(test_type)
        ]
        filename = self._select_file(PERF_INSIGHT_TEMP, candidates)
        if filename:
            shutil.copyfile(os.path.join(PERF_INSIGHT_TEMP, filename),
                            os.path.join(workspace, 'test.generate_testrun_results.yaml'))
        else:
            return False, 'Cannot find template "{}".'.format(candidates)

        candidates = [base_yaml] if base_yaml else [
            'generate_testrun_results-{}-{}.yaml'.format(
                base_type, str(base_platform).lower()),
            'generate_testrun_results-{}.yaml'.format(base_type)
        ]
        filename = self._select_file(PERF_INSIGHT_TEMP, candidates)
        if filename:
            shutil.copyfile(os.path.join(PERF_INSIGHT_TEMP, filename),
                            os.path.join(workspace, 'base.generate_testrun_results.yaml'))
        else:
            return False, 'Cannot find template "{}".'.format(candidates)

        candidates = [benchmark_yaml] if benchmark_yaml else [
            'generate_benchmark_results-{}-{}.yaml'.format(
                test_type, str(test_platform).lower()),
            'generate_benchmark_results-{}.yaml'.format(test_type)
        ]
        filename = self._select_file(PERF_INSIGHT_TEMP, candidates)
        if filename:
            shutil.copyfile(os.path.join(PERF_INSIGHT_TEMP, filename),
                            os.path.join(workspace, 'generate_benchmark_results.yaml'))
        else:
            return False, 'Cannot find template "{}".'.format(candidates)

        candidates = [metadata_yaml] if metadata_yaml else [
            'generate_benchmark_metadata-{}-{}.yaml'.format(
                test_type, str(test_platform).lower()),
            'generate_benchmark_metadata-{}.yaml'.format(test_type)
        ]
        filename = self._select_file(PERF_INSIGHT_TEMP, candidates)
        if filename:
            shutil.copyfile(os.path.join(PERF_INSIGHT_TEMP, filename),
                            os.path.join(workspace, 'generate_benchmark_metadata.yaml'))
        else:
            return False, 'Cannot find template "{}".'.format(candidates)

        # Deliver templates
        shutil.copyfile(os.path.join(PERF_INSIGHT_TEMP, 'benchmark_description.md'),
                        os.path.join(workspace, 'benchmark_description.md'))

        candidates = [introduction_md] if introduction_md else [
            'introduction_{}_{}.md'.format(
                str(test_platform).lower(), test_type),
            'introduction_default.md'
        ]
        filename = self._select_file(PERF_INSIGHT_TEMP, candidates)
        if filename:
            shutil.copyfile(os.path.join(PERF_INSIGHT_TEMP, filename),
                            os.path.join(workspace, 'testrun_introduction.md'))
        else:
            return False, 'Cannot find template "{}".'.format(candidates)

        # Deliver scripts
        os.makedirs(os.path.join(workspace, 'utils'))

        script_list = ['generate_testrun_results.py',
                       'generate_benchmark_results.py',
                       'generate_benchmark_metadata.py',
                       'generate_benchmark_parameters.py',
                       'generate_benchmark_statistics.py',
                       'generate_benchmark_summary.py']
        for filename in script_list:
            shutil.copyfile(
                os.path.join(PERF_INSIGHT_REPO, 'utils', filename),
                os.path.join(workspace, 'utils', filename))

        shutil.copyfile(
            os.path.join(PERF_INSIGHT_REPO, 'jupyter_server',
                         'utils', 'html_report.sh'),
            os.path.join(workspace, 'utils', 'html_report.sh'))

        shutil.copyfile(
            os.path.join(PERF_INSIGHT_REPO, 'jupyter_server',
                         'utils', 'report_portal.ipynb'),
            os.path.join(workspace, 'report_portal.ipynb'))

        # Connect to Jupyter server and generate the report
        request_url = 'http://{}/reports/{}'.format(
            JUPYTER_API_SERVER, benchmark)

        try:
            LOG.debug('Send request: {}'.format(request_url))
            response = requests.post(url=request_url)

            response.raise_for_status()
            result = response.json()

            # Successful request
            LOG.info('Benchmark report generated.')

        except requests.exceptions.RequestException as ex:
            LOG.error('Failed to generate benchmark report with Jupyter server.')

            # Use json reply if available
            try:
                details = response.json()['error']
            except:
                details = str(ex)

            # Failed request
            LOG.error(details)
            return False, details

        # Update metadata and dump to metadata.json
        create_time = time.strftime(
            '%Y-%m-%d %H:%M:%S', time.localtime())

        metadata = {'id': benchmark,
                    'create_time': create_time,
                    'test_id': test_id,
                    'base_id': base_id,
                    'comments': comments,
                    'test_metadata': test_metadata,
                    'base_metadata': base_metadata}

        with open(os.path.join(workspace, 'metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=3)

        # Get the Report URL
        report_url = 'http://{}/perf-insight/reports/{}/report.html'.format(
            FILE_SERVER, benchmark)

        # Update dashboard as requested
        if update_dashboard:
            if os.path.exists(DASHBOARD_DB_FILE):
                db_file = DASHBOARD_DB_FILE
            else:
                msg = 'Can not find the dashboard DB file "{}".'.format(
                    DASHBOARD_DB_FILE)
                LOG.error(msg)
                return False, msg

            dbloader = os.path.join('/tmp/benchmark_info.json')
            benchmark_info = {
                'id': benchmark,
                'create_time': create_time,
                'test_id': test_id,
                'base_id': base_id,
                'report_url': report_url,
                'comments': comments,
                'metadata': metadata
            }
            with open(dbloader, 'w') as f:
                json.dump(benchmark_info, f, indent=3)

            cmd = '{}/utils/flask_load_db.py --benchmark --db_file {} --delete {}'.format(
                PERF_INSIGHT_REPO, db_file, benchmark)
            res = os.system(cmd)
            if res > 0:
                msg = 'Failed to clean up specified benchmark report from database.'
                LOG.error(msg)
                return False, msg

            cmd = '{}/utils/flask_load_db.py --benchmark --db_file {} --json_file {}'.format(
                PERF_INSIGHT_REPO,  db_file, dbloader)
            res = os.system(cmd)
            if res > 0:
                msg = 'Failed to load specified benchmark report into database.'
                LOG.error(msg)
                return False, msg

        # Deal with the files
        try:
            if SAFE_MODE:
                shutil.copytree(workspace, target)
                shutil.move(workspace, os.path.join(
                    PERF_INSIGHT_RBIN,
                    '.deleted_after_creating_{}__{}'.format(
                        time.strftime('%y%m%d%H%M%S', time.localtime()),
                        os.path.basename(workspace))))
            else:
                shutil.move(workspace, target)
        except Exception as err:
            msg = 'Failed to deal with the files. error: {}'.format(err)
            LOG.error(msg)
            return False, msg

        return True, {'id': benchmark, 'url': report_url, 'metadata': metadata}

    def delete_benchmark(self, id, update_dashboard=True):
        """Delete a specified benchmark from PERF_INSIGHT_ROOT.

        Input:
            id               - Benchmark ID
            update_dashboard - Update the dashboard or not

        Return:
            - (True, json-block), or
            - (False, message) if something goes wrong.
        """

        # Criteria check
        target = os.path.join(PERF_INSIGHT_ROOT, 'reports', id)
        if not os.path.isdir(target):
            msg = 'Benchmark "{}" does not exist.'.format(id)
            LOG.error(msg)
            return False, msg

        # Update dashboard as requested
        if update_dashboard:
            if os.path.exists(DASHBOARD_DB_FILE):
                db_file = DASHBOARD_DB_FILE
            else:
                msg = 'Can not find the dashboard DB file "{}".'.format(
                    DASHBOARD_DB_FILE)
                LOG.error(msg)
                return False, msg

            cmd = '{}/utils/flask_load_db.py --benchmark --db_file {} --delete {}'.format(
                PERF_INSIGHT_REPO, db_file, id)
            res = os.system(cmd)
            if res > 0:
                msg = 'Failed to clean up specified benchmark report from database.'
                LOG.error(msg)
                return False, msg

        # Deal with the files
        try:
            shutil.move(target, os.path.join(PERF_INSIGHT_RBIN, '.deleted_by_user_{}__{}'.format(
                time.strftime('%y%m%d%H%M%S', time.localtime()), id)))
        except Exception as err:
            msg = 'Failed to deal with the files. error: {}'.format(err)
            LOG.error(msg)
            return False, msg

        return True, {'id': id}


# Flask
app = Flask(__name__)


# TestRun entrypoints


@app.get('/testruns')
def query_testruns():
    LOG.info('Received request to query all TestRuns.')
    res, con = manager.query_testruns()
    if res:
        return jsonify(con), 200
    else:
        return jsonify({'error': con}), 500


@app.get('/testruns/<id>')
def inspect_testrun(id):
    LOG.info('Received request to inspect TestRun "{}".'.format(id))
    res, con = manager.inspect_testrun(id)
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
        res, con = manager.load_testrun(
            id=id,
            generate_plots=generate_plots,
            create_datastore=create_datastore,
            update_dashboard=update_dashboard)
    elif action == 'import':
        res, con = manager.import_testrun(
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
    res, con = manager.fetch_testrun(id)
    if res:
        return jsonify(con), 200
    else:
        return jsonify({'error': con}), 500


@app.delete('/testruns/<id>')
def delete_testrun(id):
    LOG.info('Received request to delete TestRun "{}".'.format(id))
    res, con = manager.delete_testrun(id)
    if res:
        return jsonify(con), 200    # use 200 since 204 returns no json
    else:
        return jsonify({'error': con}), 500


# Benchmark entrypoints


@app.get('/benchmarks')
def query_benchmarks():
    LOG.info('Received request to query all benchmarks.')
    res, con = manager.query_benchmarks()
    if res:
        return jsonify(con), 200
    else:
        return jsonify({'error': con}), 500


@app.get('/benchmarks/<id>')
def inspect_benchmark(id):
    LOG.info('Received request to inspect benchmark "{}".'.format(id))
    res, con = manager.inspect_benchmark(id)
    if res:
        return jsonify(con), 200
    else:
        return jsonify({'error': con}), 500


@app.post('/benchmarks')
def create_benchmark():
    LOG.info('Received request to create benchmark report.')

    if request.is_json:
        req = request.get_json()
    else:
        return jsonify({'error': 'Request must be JSON.'}), 415

    # Parse args
    test_id = req.get('test_id')
    if test_id is None:
        return jsonify({'error': '"test_id" is missing in request.'}), 415

    base_id = req.get('base_id')
    if base_id is None:
        return jsonify({'error': '"base_id" is missing in request.'}), 415

    test_yaml = req.get('test_yaml')
    base_yaml = req.get('base_yaml')
    benchmark_yaml = req.get('benchmark_yaml')
    metadata_yaml = req.get('metadata_yaml')
    introduction_md = req.get('introduction_md')
    comments = req.get('comments')
    update_dashboard = req.get('update_dashboard', True)
    allow_overwrite = req.get('allow_overwrite', True)

    res, con = manager.create_benchmark(
        test_id, base_id, test_yaml, base_yaml,
        benchmark_yaml, metadata_yaml, introduction_md, comments,
        update_dashboard, allow_overwrite)

    if res:
        return jsonify(con), 201
    else:
        return jsonify({'error': con}), 500


@app.delete('/benchmarks')
def delete_benchmark():
    LOG.info('Received request to delete benchmark.')

    if request.is_json:
        req = request.get_json()
    else:
        return jsonify({'error': 'Request must be JSON.'}), 415

    # Parse args
    report_id = req.get('report_id')
    if report_id is None:
        return jsonify({'error': '"report_id" is missing in request.'}), 415

    update_dashboard = req.get('update_dashboard', True)

    res, con = manager.delete_benchmark(report_id, update_dashboard)
    if res:
        return jsonify(con), 200    # use 200 since 204 returns no json
    else:
        return jsonify({'error': con}), 500


# Jupyter server's entrypoints (labs, studies)

@app.route('/labs', methods=['GET', 'POST', 'DELETE', 'PUT'])
@app.route('/studies', methods=['GET', 'POST', 'DELETE', 'PUT'])
def jupyter_server_proxy():
    LOG.debug(request)
    LOG.info('Redirect request to the Jupyter API Server.')

    jupyter_server = 'http://{}/'.format(JUPYTER_API_SERVER)
    response = requests.request(
        method=request.method,
        url=request.url.replace(request.host_url, jupyter_server),
        data=request.get_data(),
        headers=request.headers)

    return jsonify(response.json()), response.status_code


# Main
LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')


# Load perf-insight configure
with open(os.path.expanduser('~/.perf-insight.yaml'), 'r') as f:
    user_config = yaml.safe_load(f)

config = user_config.get('global', {})
config.update(user_config.get('api', {}))

PERF_INSIGHT_ROOT = config.get('perf_insight_root', '/nfs/perf-insight')
PERF_INSIGHT_REPO = config.get('perf_insight_repo', '/opt/perf-insight')
PERF_INSIGHT_TEMP = config.get(
    'perf_insight_temp', os.path.join(PERF_INSIGHT_REPO, 'templates'))
PERF_INSIGHT_STAG = config.get(
    'perf_insight_stag', os.path.join(PERF_INSIGHT_ROOT, '.staging'))
PERF_INSIGHT_RBIN = config.get(
    'perf_insight_rbin', os.path.join(PERF_INSIGHT_ROOT, '.deleted'))
DASHBOARD_DB_FILE = config.get('dashboard_db_file', '/data/app.db')
JUPYTER_API_SERVER = config.get('jupyter_api_server', 'localhost:8880')
FILE_SERVER = config.get('file_server', 'localhost:8081')
SAFE_MODE = config.get('safe_mode', False)

manager = PerfInsightManager()
