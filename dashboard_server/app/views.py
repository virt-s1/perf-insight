#!/usr/bin/env python3
"""
File:  views.py @flask-appbuilder
Owner: Frank Liang <xiliang@redhat.com>
"""

from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.api import ModelRestApi
from flask_appbuilder.models.sqla.filters import FilterEqualFunction, FilterContains
from flask_appbuilder.views import (ModelView, CompactCRUDMixin,
                                    MasterDetailView, SimpleFormView, expose)
from flask_appbuilder.widgets import ListBlock, ShowBlockWidget, ListWidget, ShowWidget, FormWidget
from flask_appbuilder import MultipleView
from flask_appbuilder.actions import action
from flask import redirect, render_template, flash, url_for, Markup, request, session
from flask_babel import lazy_gettext as _

from . import appbuilder, db
import subprocess
from .forms import YamlForm, NewTestrunForm
import tempfile
import datetime

from .models import (StorageRun, StorageResult, Bugs, FailureType,
                     FailureStatus, ComparedResult, NetworkRun, NetworkResult)

# Below import is for charts
import calendar
from flask_appbuilder.charts.views import (DirectByChartView, DirectChartView,
                                           GroupByChartView)
from flask_appbuilder.models.group import (aggregate_sum, aggregate_count,
                                           aggregate, aggregate_avg)

import shutil
import os
import yaml


# Load perf-insight configure
with open(os.path.expanduser('~/.perf-insight.yaml'), 'r') as f:
    user_config = yaml.safe_load(f)


config = user_config.get('global', {})
config.update(user_config.get('dashboard', {}))

PERF_INSIGHT_ROOT = config.get('perf_insight_root', '/nfs/perf-insight')
PERF_INSIGHT_REPO = config.get('perf_insight_repo', '/opt/perf-insight')
FILE_SERVER = config.get('file_server', 'localhost')
REPORT_PATH = os.path.join(PERF_INSIGHT_ROOT, 'reports')


TWO_WAY_BENCHMARK_YAML = '/opt/perf-insight/templates/generate_2way_benchmark.yaml'
TWO_WAY_METADATA_YAML = '/opt/perf-insight/templates/generate_2way_metadata.yaml'
TESTRUN_RESULTS_YAML = '/opt/perf-insight/templates/generate_testrun_results.yaml'


def jupiter_prepare(baserun, testrun, target_dir):
    baserun_dir = PERF_INSIGHT_ROOT + '/testruns/' + baserun
    testrun_dir = PERF_INSIGHT_ROOT + '/testruns/' + testrun
    shutil.copy(baserun_dir + '/datastore.json',
                target_dir + '/base.datastore.json')
    shutil.copy(baserun_dir + '/metadata.json',
                target_dir + '/base.metadata.json')
    shutil.copy(testrun_dir + '/datastore.json',
                target_dir + '/test.datastore.json')
    shutil.copy(testrun_dir + '/metadata.json',
                target_dir + '/test.metadata.json')


def generate_dirname():
    num_list = []
    current_dir = os.listdir(REPORT_PATH)
    old_found = False
    for dir in current_dir:
        if 'benchmark_' in dir:
            old_found = True
            num_list.append(int(dir[-6:]))
    if not old_found:
        new_name = 'benchmark_000000'
    else:
        new_num = str(max(num_list) + 1).zfill(6)
        new_name = 'benchmark_{}'.format(new_num)
    return new_name


class YamlFormWidget(FormWidget):
    template = 'widgets/yaml_show.html'


class YamlFormView(SimpleFormView):
    edit_widget = YamlFormWidget
    form = YamlForm
    form_title = 'Generat report'
    result = ''

    def form_get(self, form):
        try:
            form.baserun.data = request.args['baserun']
            form.testrun.data = request.args['testrun']
            self.result = form.baserun.data + ' vs ' + form.testrun.data
        except Exception as err:
            flash("Please specify baserun and testrun", 'danger')
            self.update_redirect()
            return redirect(self.get_redirect())

        # get testrun type
        if form.baserun.data.startswith('fio_'):
            testrun_type = 'fio'
        elif form.baserun.data.startswith('uperf_'):
            testrun_type = 'uperf'
        else:
            flash('Unsupported TestRun Type!', 'danger')
            self.update_redirect()
            return redirect(self.get_redirect())

        if session.get('yaml1') is None:
            TESTRUN_RESULTS_YAML = '/opt/perf-insight/\
templates/generate_testrun_results-{}.yaml'.format(testrun_type)
            with open(TESTRUN_RESULTS_YAML, 'r') as fh:
                form.yaml1.data = fh.read()
        else:
            form.yaml1.data = session['yaml1']

        if session.get('yaml2') is None:
            TWO_WAY_BENCHMARK_YAML = '/opt/perf-insight/\
templates/generate_2way_benchmark-{}.yaml'.format(testrun_type)
            with open(TWO_WAY_BENCHMARK_YAML, 'r') as fh:
                form.yaml2.data = fh.read()
        else:
            form.yaml2.data = session['yaml2']

        if session.get('yaml3') is None:
            TWO_WAY_METADATA_YAML = '/opt/perf-insight/\
templates/generate_2way_metadata-{}.yaml'.format(testrun_type)
            with open(TWO_WAY_METADATA_YAML, 'r') as fh:
                form.yaml3.data = fh.read()
        else:
            form.yaml3.data = session['yaml3']

    def form_post(self, form):
        # post process form
        # workspace = tempfile.mkdtemp(suffix=None, prefix='jupiter', dir=REPORT_PATH)

        # Prepare the workspace
        new_dir = generate_dirname()
        workspace = '{}/{}'.format(REPORT_PATH, new_dir)
        os.mkdir(workspace)

        # Save the yaml files
        print('save to {}'.format(workspace))
        with open(workspace + '/' + 'base.generate_testrun_results.yaml',
                  'w') as fh:
            fh.write(form.yaml1.data)
        with open(workspace + '/' + 'test.generate_testrun_results.yaml',
                  'w') as fh:
            fh.write(form.yaml1.data)
        with open(workspace + '/' + 'generate_2way_benchmark.yaml', 'w') as fh:
            fh.write(form.yaml2.data)
        with open(workspace + '/' + 'generate_2way_metadata.yaml', 'w') as fh:
            fh.write(form.yaml3.data)

        # Save the yaml files - backward support (all-in-one yaml)
        tmp_config = workspace + '/' + 'benchmark_config.yaml'
        if os.path.exists(tmp_config):
            os.unlink(tmp_config)
        with open(tmp_config, 'w+') as fh:
            fh.write(form.yaml1.data)
            fh.write('\n')
            fh.write(form.yaml2.data)
            fh.write('\n')
            fh.write(form.yaml3.data)

        # Show user message
        baserun = form.baserun.data
        testrun = form.testrun.data
        self.result = baserun + ' vs ' + testrun
        self.message = Markup('Benchmark report is available at \
<a href="http://{}/perf-insight/reports/{}/report.html" \
class="alert-link">compared {}</a>'.format(FILE_SERVER, new_dir,
                                           self.result))
        jupiter_prepare(baserun, testrun, workspace)
        cmd = 'podman run --rm \
--volume {}/.perf-insight.yaml:/root/.perf-insight.yaml:ro \
--volume {}:/workspace:rw jupyter_reporting '.format(os.getenv('HOME'),
                                                     workspace)

        # Generate report
        ret = subprocess.run(cmd,
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,
                             timeout=120,
                             encoding='utf-8')
        ret_code = ret.returncode

        # Update user message
        if ret_code > 0:
            flash('Error! {}'.format(ret.stdout), 'danger')
        else:
            # Write to database
            flash(self.message, 'success')
            result_record = ComparedResult()
            result_record.baseid = baserun
            result_record.testid = testrun
            result_record.reportlink = new_dir
            result_record.createtime = datetime.datetime.now()
            result_record.testrun_results_yaml = form.yaml1.data
            result_record.two_way_benchmark_yaml = form.yaml2.data
            result_record.two_way_metadata_yaml = form.yaml2.data
            result_record.comments = ''
            db.session.add(result_record)
            db.session.commit()

        # Redirect the page
        return redirect(
            url_for('YamlFormView.this_form_get',
                    baserun=baserun,
                    testrun=testrun))


class NewTestrunFormWidget(FormWidget):
    template = 'widgets/testrun_new.html'


class NewTestrunFormView(SimpleFormView):
    edit_widget = NewTestrunFormWidget
    form = NewTestrunForm
    form_title = 'New Testrun'

    def form_get(self, form):
        form.testrun.data = ''

    def form_post(self, form):
        # post process form
        testrun = form.testrun.data.strip(' ')

        cmd = "{}/utils/process_testrun.sh -t {} -s -d -P".format(
            PERF_INSIGHT_REPO, testrun)
        print('cmd {}'.format(cmd))
        ret = subprocess.run(cmd,
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,
                             timeout=120,
                             encoding='utf-8')
        ret_code = ret.returncode

        if ret_code > 0:
            flash('Error! {}'.format(ret.stdout), 'danger')
            redirect_url = request.url
        else:
            flash('Uploaded!', 'success')
            if testrun.startswith('fio_'):
                redirect_url = url_for('StorageRunPubView.list',
                                       _flt_0_testrun=str(testrun))
            elif testrun.startswith('uperf_'):
                redirect_url = url_for('NetworkRunPubView.list',
                                       _flt_0_testrun=str(testrun))
            else:
                redirect_url = request.url

        return redirect(redirect_url)


class MyListWidget(ListWidget):
    template = 'widgets/my_list.html'


class MyShowWidget(ShowWidget):
    template = 'widgets/my_show.html'


class NetworkRunPubView(ModelView):
    datamodel = SQLAInterface(NetworkRun)
    base_permissions = ["can_list", "can_show", "menu_access"]

    @action("compareruns",
            "Compare2runs",
            "[Deprecated]Compare 2 test runs?",
            "fa-rocket",
            single=False)
    def compareruns(self, items):
        testruns = ''

        if len(items) != 2:
            flash("Please choose 2 testruns to compare!", 'danger')
            self.update_redirect()
            return redirect(self.get_redirect())
        else:
            for item in items:
                testruns += item.testrun + '_'
            testruns = testruns.rstrip('_')
        #form = YamlForm
        baserun, testrun = items[0].testrun, items[1].testrun
        # return self.render_template(self.yaml_template, form=form, appbuilder=self.appbuilder)
        return redirect("/yamlformview/form?baserun={}&testrun={}".format(
            testrun, baserun))

    label_columns = {
        "result_url": "Result",
        "rawdata_url": "RawData",
    }

    list_columns = [
        "id", "testrun", "platform", "flavor", "branch", "compose", "kernel",
        "casenum", "result_url", "rawdata_url"
    ]
    search_columns = [
        "id", "testrun", "platform", "flavor", "branch", "compose", "kernel",
        "casenum", "result", "rawdata"
    ]

    show_fieldsets = [
        ("Summary", {
            "fields": [
                "id", "testrun", "platform", "flavor", "branch", "compose",
                "kernel", "casenum", "result_url", "rawdata_url"
            ]
        }),
        ("Description", {
            "fields": ["description"],
            "expanded": True
        }),
    ]
    base_order = ("id", "desc")


class EC2NetworkRunPubView(NetworkRunPubView):
    base_filters = [["platform", FilterContains, 'ec2']]


class AzureNetworkRunPubView(NetworkRunPubView):
    base_filters = [["platform", FilterContains, 'azure']]


class EsxiNetworkRunPubView(NetworkRunPubView):
    base_filters = [["platform", FilterContains, 'esxi']]


class HypervNetworkRunPubView(NetworkRunPubView):
    base_filters = [["platform", FilterContains, 'hyperv']]


class NetworkRunEditView(NetworkRunPubView):
    base_permissions = [
        "can_list", "can_show", "menu_access", "can_add", "can_edit",
        "can_delete"
    ]


class EC2NetworkRunEditView(EC2NetworkRunPubView):
    base_permissions = [
        "can_list", "can_show", "menu_access", "can_add", "can_edit",
        "can_delete"
    ]


class AzureNetworkRunEditView(AzureNetworkRunPubView):
    base_permissions = [
        "can_list", "can_show", "menu_access", "can_add", "can_edit",
        "can_delete"
    ]


class EsxiNetworkRunEditView(EsxiNetworkRunPubView):
    base_permissions = [
        "can_list", "can_show", "menu_access", "can_add", "can_edit",
        "can_delete"
    ]


class HypervNetworkRunEditView(HypervNetworkRunPubView):
    base_permissions = [
        "can_list", "can_show", "menu_access", "can_add", "can_edit",
        "can_delete"
    ]


class NetworkResultPubView(ModelView):
    datamodel = SQLAInterface(NetworkResult)
    base_permissions = ["can_list", "can_show", "menu_access"]

    label_columns = {
        "debug_url": "Result",
        "rawdata_url": "RawData",
        "testtype": "TestType",
        "cpu": "CPU",
        "cpu_model": "CPU_Model",
        "vcpu": "vCPU",
        "case_id": "Case ID",
        "net_driver": "Net-Driver",
        "net_duplex": "Net-Duplex",
        "net_speed": "Net-Speed",
        "msize": "MSize",
        "throughput": "Throughput(Mb/s)",
        "trans": "Trans(t/s)",
        "latency": "Latency(us)"
    }

    list_columns = [
        "testrun", "flavor", "protocol", "testtype", "msize", "instance",
        "case_id", "sample", "throughput", "trans", "latency", "rawdata_url"
    ]
    search_columns = [
        "id", "testrun", "run_type", "platform", "flavor", "cpu_model", "cpu",
        "hypervisor", "branch", "compose", "kernel", "vcpu", "memory",
        "net_driver", "net_duplex", "net_speed", "protocol", "testtype", "case_id",
        "msize", "instance", "sample", "throughput", "trans", "latency",
        "tool_version", "date", "rawdata", "comments"
    ]

    show_fieldsets = [
        ("Summary", {
            "fields": [
                "testrun", "run_type", "platform", "flavor", "cpu_model",
                "cpu", "hypervisor", "branch", "compose", "kernel", "vcpu",
                "memory", "net_driver", "net_duplex", "net_speed", "protocol",
                "testtype", "msize", "instance", "case_id", "sample",
                "throughput", "trans", "latency", "tool_version", "date",
                "rawdata_url", "comments"
            ]
        }),
        ("Description", {
            "fields": ["description"],
            "expanded": True
        }),
    ]
    # base_order = ("log_id", "asc")
    base_order = ("id", "desc")
    # base_filters = [["created_by", FilterEqualFunction, get_user]]


class EC2NetworkResultPubView(NetworkResultPubView):
    base_filters = [["platform", FilterContains, 'ec2']]


class AzureNetworkResultPubView(NetworkResultPubView):
    base_filters = [["platform", FilterContains, 'azure']]


class EsxiNetworkResultPubView(NetworkResultPubView):
    base_filters = [["platform", FilterContains, 'esxi']]


class HypervNetworkResultPubView(NetworkResultPubView):
    base_filters = [["platform", FilterContains, 'hyperv']]


class NetworkResultEditView(NetworkResultPubView):
    base_permissions = [
        "can_list", "can_show", "menu_access", "can_add", "can_edit",
        "can_delete"
    ]


class EC2NetworkResultEditView(EC2NetworkResultPubView):
    base_permissions = [
        "can_list", "can_show", "menu_access", "can_add", "can_edit",
        "can_delete"
    ]


class AzureNetworkResultEditView(AzureNetworkResultPubView):
    base_permissions = [
        "can_list", "can_show", "menu_access", "can_add", "can_edit",
        "can_delete"
    ]


class EsxiNetworkResultEditView(EsxiNetworkResultPubView):
    base_permissions = [
        "can_list", "can_show", "menu_access", "can_add", "can_edit",
        "can_delete"
    ]


class HypervNetworkResultEditView(HypervNetworkResultPubView):
    base_permissions = [
        "can_list", "can_show", "menu_access", "can_add", "can_edit",
        "can_delete"
    ]


class StorageRunPubView(ModelView):
    datamodel = SQLAInterface(StorageRun)
    base_permissions = ["can_list", "can_show", "menu_access"]
    #show_widget = MyShowWidget
    #list_widget = MyListWidget

    @action("compareruns",
            "Compare2runs",
            "Compare 2 test runs?",
            "fa-rocket",
            single=False)
    def compareruns(self, items):
        testruns = ''

        if len(items) != 2:
            flash("Please choose 2 testruns to compare!", 'danger')
            self.update_redirect()
            return redirect(self.get_redirect())
        else:
            for item in items:
                testruns += item.testrun + '_'
            testruns = testruns.rstrip('_')
        #form = YamlForm
        baserun, testrun = items[0].testrun, items[1].testrun
        # return self.render_template(self.yaml_template, form=form, appbuilder=self.appbuilder)
        return redirect("/yamlformview/form?baserun={}&testrun={}".format(
            testrun, baserun))

    label_columns = {"rawdata_url": "RawData", "result_url": "Result"}

    list_columns = [
        "id", "testrun", "platform", "flavor", "branch", "compose", "kernel",
        "casenum", "result_url", "rawdata_url"
    ]
    search_columns = [
        "id", "testrun", "platform", "flavor", "branch", "compose", "kernel",
        "casenum", "result", "rawdata"
    ]

    show_fieldsets = [
        ("Summary", {
            "fields": [
                "id", "testrun", "platform", "flavor", "branch", "compose",
                "kernel", "casenum", "result_url", "rawdata_url"
            ]
        }),
        ("Description", {
            "fields": ["description"],
            "expanded": True
        }),
    ]
    # base_order = ("log_id", "asc")
    base_order = ("id", "desc")
    # base_filters = [["created_by", FilterEqualFunction, get_user]]


class StorageRunEditView(StorageRunPubView):
    base_permissions = [
        "can_list", "can_show", "menu_access", "can_add", "can_edit",
        "can_delete"
    ]


class EC2StorageRunPubView(StorageRunPubView):
    base_filters = [["platform", FilterContains, 'ec2']]


class AzureStorageRunPubView(StorageRunPubView):
    base_filters = [["platform", FilterContains, 'azure']]


class EsxiStorageRunPubView(StorageRunPubView):
    base_filters = [["platform", FilterContains, 'esxi']]


class HypervStorageRunPubView(StorageRunPubView):
    base_filters = [["platform", FilterContains, 'hyperv']]


class EC2StorageRunEditView(EC2StorageRunPubView):
    base_permissions = [
        "can_list", "can_show", "menu_access", "can_add", "can_edit",
        "can_delete"
    ]


class AzureStorageRunEditView(AzureStorageRunPubView):
    base_permissions = [
        "can_list", "can_show", "menu_access", "can_add", "can_edit",
        "can_delete"
    ]


class EsxiStorageRunEditView(EsxiStorageRunPubView):
    base_permissions = [
        "can_list", "can_show", "menu_access", "can_add", "can_edit",
        "can_delete"
    ]


class HypervStorageRunEditView(HypervStorageRunPubView):
    base_permissions = [
        "can_list", "can_show", "menu_access", "can_add", "can_edit",
        "can_delete"
    ]


class StorageRunModelApi(ModelRestApi):
    resource_name = 'storageruns'
    datamodel = SQLAInterface(StorageRun)


class StorageResultPubView(ModelView):
    datamodel = SQLAInterface(StorageResult)
    base_permissions = ["can_list", "can_show", "menu_access"]
    # list_widget = ListBlock
    # show_widget = ShowBlockWidget
    # show_template = 'my_show.html'

    label_columns = {
        "latency": "LAT(ms)",
        'clat': 'CLAT(ms)',
        "rawdata_url": "RawData",
        "case_id": "Case ID",
        'iops': 'IOPS',
        'rw': 'RW',
        'bs': 'BS',
        'iodepth': 'IOdepth',
        'cpu': 'CPU',
        'cpu_model': 'CPU Model'
    }

    list_columns = [
        "testrun", "flavor", "backend", "driver", "format", "case_id",
        "rw", "bs", "iodepth", "numjobs", "sample", "iops", "latency", "clat",
        "rawdata_url"
    ]
    search_columns = [
        'id', 'testrun', 'kernel', 'branch', 'backend', 'driver', 'format',
        'rw', 'bs', 'iodepth', 'numjobs', 'iops', 'latency', 'clat',
        'tool_version', 'compose', 'cpu', 'cpu_model', 'memory', 'platform',
        'flavor', 'date', 'comments', 'sample', 'testrun', "case_id",
    ]

    show_fieldsets = [
        ("Summary", {
            "fields": [
                'testrun', 'platform', 'flavor', 'branch', 'compose', 'kernel',
                'cpu', 'cpu_model', 'memory', 'backend', 'driver', 'format',
                "case_id", 'rw', 'bs', 'iodepth', 'numjobs', 'sample', 'iops',
                'latency', 'clat', 'tool_version', 'date', 'rawdata_url', 'comments'
            ]
        }),
        ("Description", {
            "fields": ["description"],
            "expanded": True
        }),
    ]
    # base_order = ("log_id", "asc")
    base_order = ("id", "desc")
    # base_filters = [["created_by", FilterEqualFunction, get_user]]


class EC2StorageResultPubView(StorageResultPubView):
    base_filters = [["platform", FilterContains, 'ec2']]


class AzureStorageResultPubView(StorageResultPubView):
    base_filters = [["platform", FilterContains, 'azure']]


class EsxiStorageResultPubView(StorageResultPubView):
    base_filters = [["platform", FilterContains, 'esxi']]


class HypervStorageResultPubView(StorageResultPubView):
    base_filters = [["platform", FilterContains, 'hyperv']]


class StorageResultEditView(StorageResultPubView):
    base_permissions = [
        "can_list", "can_show", "menu_access", "can_add", "can_edit",
        "can_delete"
    ]


class StorageResultModelApi(ModelRestApi):
    resource_name = 'storageresults'
    datamodel = SQLAInterface(StorageResult)


class EC2StorageResultEditView(EC2StorageResultPubView):
    base_permissions = [
        "can_list", "can_show", "menu_access", "can_add", "can_edit",
        "can_delete"
    ]


class AzureStorageResultEditView(AzureStorageResultPubView):
    base_permissions = [
        "can_list", "can_show", "menu_access", "can_add", "can_edit",
        "can_delete"
    ]


class EsxiStorageResultEditView(EsxiStorageResultPubView):
    base_permissions = [
        "can_list", "can_show", "menu_access", "can_add", "can_edit",
        "can_delete"
    ]


class HypervStorageResultEditView(HypervStorageResultPubView):
    base_permissions = [
        "can_list", "can_show", "menu_access", "can_add", "can_edit",
        "can_delete"
    ]


class ComparedResultPubView(ModelView):
    datamodel = SQLAInterface(ComparedResult)
    base_permissions = ["can_list", "can_show", "menu_access"]
    #show_widget = MyShowWidget
    #list_widget = MyListWidget

    label_columns = {
        "baseid": "BaseID",
        "report_id": "ReportID",
        "testid": "TestID",
        "createtime": "Create Time",
        "report_url": "Report Link"
    }

    list_columns = [
        "id", "baseid", "testid", "createtime", "report_url", "comments"
    ]
    search_columns = [
        "id", "report_id", "baseid", "testid", "createtime", "reportlink",
        "comments", "benchmark_metadata"
    ]

    show_fieldsets = [
        ("Summary", {
            "fields": [
                "id", "report_id", "baseid", "testid", "createtime", "report_url",
                "comments", "benchmark_metadata"
            ]
        }),
        ("Description", {
            "fields": ["description"],
            "expanded": True
        }),
    ]
    base_order = ("id", "desc")


class ComparedResultEditView(ComparedResultPubView):
    base_permissions = [
        "can_list", "can_show", "menu_access", "can_add", "can_edit",
        "can_delete"
    ]


class BugsPubView(ModelView):
    datamodel = SQLAInterface(Bugs)
    base_permissions = ["can_list", "can_show", "menu_access"]

    # label_columns = {"bug_url": "BZ#"}

    list_columns = [
        "id", "test_suite", "case_name", "bug_url", "bug_title",
        "failure_status", "failure_type", "comments", "last_update",
        "create_date"
    ]
    search_columns = [
        "id", "test_suite", "case_name", "bug_id", "bug_title",
        "failure_status", "branch_name", "comments", "last_update",
        "create_date", 'failure_type', 'identify_keywords',
        'identify_debuglog', 'contactor'
    ]

    show_fieldsets = [
        ("Summary", {
            "fields": [
                "id", "test_suite", "case_name", "bug_id", "bug_title",
                "failure_status", "branch_name", "comments", "last_update",
                "create_date", 'failure_type', 'identify_keywords',
                'identify_debuglog', 'contactor'
            ]
        }),
        ("Description", {
            "fields": ["description"],
            "expanded": True
        }),
    ]
    # base_order = ("log_id", "asc")
    base_order = ("id", "desc")


class BugsView(BugsPubView):
    base_permissions = [
        "can_list", "can_show", "menu_access", "can_add", "can_edit",
        "can_delete"
    ]


class FailureTypeView(ModelView):
    datamodel = SQLAInterface(FailureType)
    related_views = [BugsView]


class FailureStatusView(ModelView):
    datamodel = SQLAInterface(FailureStatus)
    related_views = [BugsView]


def pretty_month_year(value):
    return calendar.month_name[value.month] + " " + str(value.year)


db.create_all()

appbuilder.add_view(StorageRunPubView,
                    "Storage Test Runs - All",
                    icon="fa-angle-double-right",
                    category="StorageTest")
appbuilder.add_view(EC2StorageRunPubView,
                    "Storage Test Runs - EC2",
                    icon="fa-angle-double-right",
                    category="StorageTest")
appbuilder.add_view(AzureStorageRunPubView,
                    "Storage Test Runs - Azure",
                    icon="fa-angle-double-right",
                    category="StorageTest")
appbuilder.add_view(EsxiStorageRunPubView,
                    "Storage Test Runs - ESXi",
                    icon="fa-angle-double-right",
                    category="StorageTest")
appbuilder.add_view(HypervStorageRunPubView,
                    "Storage Test Runs - HyperV",
                    icon="fa-angle-double-right",
                    category="StorageTest")
appbuilder.add_separator("StorageTest")
appbuilder.add_view(StorageResultPubView,
                    "Storage Test Results - All",
                    icon="fa-angle-double-right",
                    category="StorageTest")
appbuilder.add_view(EC2StorageResultPubView,
                    "Storage Test Results - EC2",
                    icon="fa-angle-double-right",
                    category="StorageTest")
appbuilder.add_view(AzureStorageResultPubView,
                    "Storage Test Results - Azure",
                    icon="fa-angle-double-right",
                    category="StorageTest")
appbuilder.add_view(EsxiStorageResultPubView,
                    "Storage Test Results - ESXi",
                    icon="fa-angle-double-right",
                    category="StorageTest")
appbuilder.add_view(HypervStorageResultPubView,
                    "Storage Test Results - HyperV",
                    icon="fa-angle-double-right",
                    category="StorageTest")

appbuilder.add_view(NetworkRunPubView,
                    "Network Test Runs - All",
                    icon="fa-angle-double-right",
                    category="NetworkTest")
appbuilder.add_view(EC2NetworkRunPubView,
                    "Network Test Runs - EC2",
                    icon="fa-angle-double-right",
                    category="NetworkTest")
appbuilder.add_view(AzureNetworkRunPubView,
                    "Network Test Runs - Azure",
                    icon="fa-angle-double-right",
                    category="NetworkTest")
appbuilder.add_view(EsxiNetworkRunPubView,
                    "Network Test Runs - ESXi",
                    icon="fa-angle-double-right",
                    category="NetworkTest")
appbuilder.add_view(HypervNetworkRunPubView,
                    "Network Test Runs - HyperV",
                    icon="fa-angle-double-right",
                    category="NetworkTest")
appbuilder.add_separator("NetworkTest")
appbuilder.add_view(NetworkResultPubView,
                    "Network Test Results - All",
                    icon="fa-angle-double-right",
                    category="NetworkTest")
appbuilder.add_view(EC2NetworkResultPubView,
                    "Network Test Results - EC2",
                    icon="fa-angle-double-right",
                    category="NetworkTest")
appbuilder.add_view(AzureNetworkResultPubView,
                    "Network Test Results - Azure",
                    icon="fa-angle-double-right",
                    category="NetworkTest")
appbuilder.add_view(EsxiNetworkResultPubView,
                    "Network Test Results - ESXi",
                    icon="fa-angle-double-right",
                    category="NetworkTest")
appbuilder.add_view(HypervNetworkResultPubView,
                    "Network Test Results - HyperV",
                    icon="fa-angle-double-right",
                    category="NetworkTest")

appbuilder.add_view(ComparedResultPubView,
                    "ComparedResult",
                    icon="fa-angle-double-right",
                    category="ComparedResult")

appbuilder.add_view(StorageRunEditView,
                    "Edit Storage Test Runs - All",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(EC2StorageRunEditView,
                    "Edit Storage Test Runs - EC2",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(AzureStorageRunEditView,
                    "Edit Storage Test Runs - Azure",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(EsxiStorageRunEditView,
                    "Edit Storage Test Runs - ESXi",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(HypervStorageRunEditView,
                    "Edit Storage Test Runs - HyperV",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(StorageResultEditView,
                    "Edit Storage Test Results - All",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(EC2StorageResultEditView,
                    "Edit Storage Test Results - EC2",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(AzureStorageResultEditView,
                    "Edit Storage Test Results - Azure",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(EsxiStorageResultEditView,
                    "Edit Storage Test Results - ESXi",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(HypervStorageResultEditView,
                    "Edit Storage Test Results - HyperV",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(NetworkRunEditView,
                    "Edit Network Test Runs - All",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(EC2NetworkRunEditView,
                    "Edit Network Test Runs - EC2",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(AzureNetworkRunEditView,
                    "Edit Network Test Runs - Azure",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(EsxiNetworkRunEditView,
                    "Edit Network Test Runs - ESXi",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(HypervNetworkRunEditView,
                    "Edit Network Test Runs - HyperV",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(NetworkResultEditView,
                    "Edit Network Test Results - All",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(EC2NetworkResultEditView,
                    "Edit Network Test Results - EC2",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(AzureNetworkResultEditView,
                    "Edit Network Test Results - Azure",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(EsxiNetworkResultEditView,
                    "Edit Network Test Results - ESXi",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(HypervNetworkResultEditView,
                    "Edit Network Test Results - HyperV",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(ComparedResultEditView,
                    "Edit Compared Result List",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(BugsView,
                    "Edit Know Failures",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(FailureTypeView,
                    "Edit Know Failures Types",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(FailureStatusView,
                    "Edit Failures Status List",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_separator("Management")
appbuilder.add_view(NewTestrunFormView,
                    "New Testrun",
                    icon="fa-upload",
                    category="Management")

appbuilder.add_view(BugsPubView,
                    "List Know Failures",
                    icon="fa-angle-double-right",
                    category="TestBugs")

# appbuilder.add_view(YamlFormView, "My form View", icon="fa-group", label=_('My form View'),
#                     category="My Forms", category_icon="fa-cogs")
appbuilder.add_view_no_menu(YamlFormView)
appbuilder.add_api(StorageResultModelApi)

# appbuilder.add_separator("TestReports")
# appbuilder.add_separator("Management")
