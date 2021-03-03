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

import shutil, os
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

with open(os.getenv('HOME') + '/.perf-insight.yaml', 'r') as fh:
    keys_data = load(fh, Loader=Loader)
APACHE_SERVER = keys_data['flask']['apache_server']
DATA_PATH = keys_data['flask']['data_path']
REPORT_PATH = '{}/reports/'.format(DATA_PATH)
PERF_INSIGHT_REPO = keys_data['flask']['perf_insight_repo']

TWO_WAY_BENCHMARK_YAML = '/opt/perf-insight/data_process/generate_2way_benchmark.yaml'
TWO_WAY_METADATA_YAML = '/opt/perf-insight/data_process/generate_2way_metadata.yaml'
TESTRUN_RESULTS_YAML = '/opt/perf-insight/data_process/generate_testrun_results.yaml'


def jupiter_prepare(baserun, testrun, target_dir):
    baserun_dir = DATA_PATH + '/testruns/' + baserun
    testrun_dir = DATA_PATH + '/testruns/' + testrun
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
            TESTRUN_RESULTS_YAML = '/opt/perf-insight/data_process/\
templates/generate_testrun_results-{}.yaml'.format(testrun_type)
            with open(TESTRUN_RESULTS_YAML, 'r') as fh:
                form.yaml1.data = fh.read()
        else:
            form.yaml1.data = session['yaml1']

        if session.get('yaml2') is None:
            TWO_WAY_BENCHMARK_YAML = '/opt/perf-insight/data_process/\
templates/generate_2way_benchmark-{}.yaml'.format(testrun_type)
            with open(TWO_WAY_BENCHMARK_YAML, 'r') as fh:
                form.yaml2.data = fh.read()
        else:
            form.yaml2.data = session['yaml2']

        if session.get('yaml3') is None:
            TWO_WAY_METADATA_YAML = '/opt/perf-insight/data_process/\
templates/generate_2way_metadata-{}.yaml'.format(testrun_type)
            with open(TWO_WAY_METADATA_YAML, 'r') as fh:
                form.yaml3.data = fh.read()
        else:
            form.yaml3.data = session['yaml3']

    def form_post(self, form):
        # post process form
        # tmpdir = tempfile.mkdtemp(suffix=None, prefix='jupiter', dir=REPORT_PATH)
        new_dir = generate_dirname()
        tmpdir = '{}/{}'.format(REPORT_PATH, new_dir)
        os.mkdir(tmpdir)
        print('save to {}'.format(tmpdir))
        tmp_config = tmpdir + '/' + 'benchmark_config.yaml'
        if os.path.exists(tmp_config):
            os.unlink(tmp_config)
        with open(tmp_config, 'w+') as fh:
            fh.write(form.yaml1.data)
            fh.write(form.yaml2.data)
            fh.write(form.yaml3.data)
        # to do: prepare data for jupiter here.
        baserun = form.baserun.data
        testrun = form.testrun.data
        self.result = baserun + ' vs ' + testrun
        self.message = Markup(
            'Benchmark report is available at <a href="http://{}/perf-insight/reports/{}/report.html" class="alert-link">compared {}</a> '
            .format(APACHE_SERVER, new_dir, self.result))
        jupiter_prepare(baserun, testrun, tmpdir)
        cmd = 'podman run -v {}/.perf-insight.yaml:/root/.perf-insight.yaml:ro --volume {}:/workspace:rw jupyter_reporting '.format(
            os.getenv('HOME'), tmpdir)
        ret = subprocess.run(cmd,
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,
                             timeout=120,
                             encoding='utf-8')
        ret_code = ret.returncode
        if ret_code > 0:
            flash('Error! {}'.format(ret.stdout), 'danger')
        else:
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
        #session['yaml1'] = form.yaml1.data
        #session['yaml2'] = form.yaml2.data
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
        cmd = "{}/data_process/process_testrun.sh -t {} -s -d -P".format(
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
            return redirect(request.url)
        else:
            flash('Uploaded!', 'success')
            return redirect(
                url_for('StorageRunPubView.list', _flt_0_testrun=str(testrun)))


class MyListWidget(ListWidget):
    template = 'widgets/my_list.html'


class MyShowWidget(ShowWidget):
    template = 'widgets/my_show.html'


class NetworkRunPubView(ModelView):
    datamodel = SQLAInterface(NetworkRun)
    base_permissions = ["can_list", "can_show", "menu_access"]
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
        #return self.render_template(self.yaml_template, form=form, appbuilder=self.appbuilder)
        return redirect("/yamlformview/form?baserun={}&testrun={}".format(
            testrun, baserun))

    label_columns = {"result_url": "Result", "rawdata_url": "RawData"}

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
        "": "Type",
        "cpu": "CPU",
        "cpu_model": "CPU_Model",
        "net_driver": "Net-Driver",
        "net_duplex": "Net-Duplex",
        "net_speed": "Net-Speed",
        "throughput": "Throughput(Mb/s)",
        "trans": "Trans(t/s)",
        "latency": "Latency(us)"
    }

    list_columns = [
        "testrun", "compose", "vcpu", "memory", "net_driver", "net_speed",
        "protocol", "testtype", "msize", "instance", "sample", "throughput",
        "trans", "latency", "rawdata_url"
    ]
    search_columns = [
        "id", "testrun", "run_type", "platform", "flavor", "cpu_model", "cpu",
        "hypervisor", "branch", "compose", "kernel", "vcpu", "memory",
        "net_driver", "net_duplex", "net_speed", "protocol", "testtype",
        "msize", "instance", "sample", "throughput", "trans", "latency",
        "tool_version", "date", "rawdata", "comments"
    ]

    show_fieldsets = [
        ("Summary", {
            "fields": [
                "testrun", "run_type", "platform", "flavor", "cpu_model",
                "cpu", "hypervisor", "branch", "compose", "kernel", "vcpu",
                "memory", "net_driver", "net_duplex", "net_speed", "protocol",
                "testtype", "msize", "instance", "sample", "throughput",
                "trans", "latency", "tool_version", "date", "rawdata",
                "comments"
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
        #return self.render_template(self.yaml_template, form=form, appbuilder=self.appbuilder)
        return redirect("/yamlformview/form?baserun={}&testrun={}".format(
            testrun, baserun))

    label_columns = {"debug_url": "Result", "rawdata_url": "RawData"}

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
        'iops': 'IOPS',
        'rw': 'RW',
        'bs': 'BS',
        'iodepth': 'IOdepth',
        'cpu': 'CPU',
        'cpu_model': 'CPU Model'
    }

    list_columns = [
        "testrun", "flavor", "backend", "driver", "format", "rw", "bs",
        "iodepth", "numjobs", "sample", "iops", "latency", "clat"
    ]
    search_columns = [
        'id', 'testrun', 'kernel', 'branch', 'backend', 'driver', 'format',
        'rw', 'bs', 'iodepth', 'numjobs', 'iops', 'latency', 'clat',
        'tool_version', 'compose', 'cpu', 'cpu_model', 'memory', 'platform',
        'flavor', 'date', 'comments', 'sample', 'testrun'
    ]

    show_fieldsets = [
        ("Summary", {
            "fields": [
                'testrun', 'platform', 'flavor', 'branch', 'compose', 'kernel',
                'cpu', 'cpu_model', 'memory', 'backend', 'driver', 'format',
                'rw', 'bs', 'iodepth', 'numjobs', 'sample', 'iops', 'latency',
                'clat', 'tool_version', 'date', 'rawdata_url', 'comments'
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
        "testid": "TestID",
        "createtime": "Create Time",
        "report_url": "Report Link"
    }

    list_columns = [
        "id", "baseid", "testid", "createtime", "report_url", "comments"
    ]
    search_columns = [
        "id", "baseid", "testid", "createtime", "reportlink", "comments",
        "testrun_results_yaml", "two_way_benchmark_yaml",
        "two_way_metadata_yaml"
    ]

    show_fieldsets = [
        ("Summary", {
            "fields": [
                "id", "baseid", "testid", "createtime", "report_url",
                "comments", "testrun_results_yaml", "two_way_benchmark_yaml",
                "two_way_metadata_yaml"
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
                    "All Test Runs",
                    icon="fa-angle-double-right",
                    category="StorageRuns")
appbuilder.add_view(EC2StorageRunPubView,
                    "EC2 Test Runs",
                    icon="fa-angle-double-right",
                    category="StorageRuns")
appbuilder.add_view(AzureStorageRunPubView,
                    "Azure Test Runs",
                    icon="fa-angle-double-right",
                    category="StorageRuns")
appbuilder.add_view(EsxiStorageRunPubView,
                    "ESXi Test Runs",
                    icon="fa-angle-double-right",
                    category="StorageRuns")
appbuilder.add_view(HypervStorageRunPubView,
                    "Hyperv Test Runs",
                    icon="fa-angle-double-right",
                    category="StorageRuns")
appbuilder.add_view(StorageResultPubView,
                    "All Test Results",
                    icon="fa-angle-double-right",
                    category="StorageResults")
appbuilder.add_view(EC2StorageResultPubView,
                    "EC2 Test Results",
                    icon="fa-angle-double-right",
                    category="StorageResults")
appbuilder.add_view(AzureStorageResultPubView,
                    "Azure Test Results",
                    icon="fa-angle-double-right",
                    category="StorageResults")
appbuilder.add_view(EsxiStorageResultPubView,
                    "ESXi Test Results",
                    icon="fa-angle-double-right",
                    category="StorageResults")
appbuilder.add_view(HypervStorageResultPubView,
                    "Hyperv Test Results",
                    icon="fa-angle-double-right",
                    category="StorageResults")
appbuilder.add_view(NetworkRunPubView,
                    "All Network Test Runs",
                    icon="fa-angle-double-right",
                    category="NetRuns")
appbuilder.add_view(EC2NetworkRunPubView,
                    "EC2 Network Test Runs",
                    icon="fa-angle-double-right",
                    category="NetRuns")
appbuilder.add_view(AzureNetworkRunPubView,
                    "Azure Network Test Runs",
                    icon="fa-angle-double-right",
                    category="NetRuns")
appbuilder.add_view(EsxiNetworkRunPubView,
                    "ESXi Network Test Runs",
                    icon="fa-angle-double-right",
                    category="NetRuns")
appbuilder.add_view(HypervNetworkRunPubView,
                    "Hyperv Network Test Runs",
                    icon="fa-angle-double-right",
                    category="NetRuns")
appbuilder.add_view(NetworkResultPubView,
                    "All Network Test Results",
                    icon="fa-angle-double-right",
                    category="NetResults")
appbuilder.add_view(EC2NetworkResultPubView,
                    "EC2 Network Test Results",
                    icon="fa-angle-double-right",
                    category="NetResults")
appbuilder.add_view(AzureNetworkResultPubView,
                    "Azure Network Test Results",
                    icon="fa-angle-double-right",
                    category="NetResults")
appbuilder.add_view(EsxiNetworkResultPubView,
                    "ESXi Network Test Results",
                    icon="fa-angle-double-right",
                    category="NetResults")
appbuilder.add_view(HypervNetworkResultPubView,
                    "Hyperv Network Test Results",
                    icon="fa-angle-double-right",
                    category="NetResults")
appbuilder.add_view(ComparedResultPubView,
                    "ComparedResult",
                    icon="fa-angle-double-right",
                    category="ComparedResult")
appbuilder.add_view(StorageRunEditView,
                    "Edit All Storage Test Runs",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(EC2StorageRunEditView,
                    "Edit EC2 Storage Test Runs",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(AzureStorageRunEditView,
                    "Edit Azure Storage Test Runs",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(EsxiStorageRunEditView,
                    "Edit ESXi Storage Test Runs",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(HypervStorageRunEditView,
                    "Edit Hyperv Storage Test Runs",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(StorageResultEditView,
                    "Edit All Storage Test Results",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(EC2StorageResultEditView,
                    "Edit EC2 Storage Test Results",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(AzureStorageResultEditView,
                    "Edit Azure Storage Test Results",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(EsxiStorageResultEditView,
                    "Edit ESXi Storage Test Results",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(HypervStorageResultEditView,
                    "Edit Hyperv Storage Test Results",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(ComparedResultEditView,
                    "Edit Compared Result List",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(NetworkRunEditView,
                    "Edit All Network Test Runs",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(EC2NetworkRunEditView,
                    "Edit EC2 Network Test Runs",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(AzureNetworkRunEditView,
                    "Edit Azure Network Test Runs",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(EsxiNetworkRunEditView,
                    "Edit ESXi Network Test Runs",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(HypervNetworkRunEditView,
                    "Edit Hyperv Network Test Runs",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(NetworkResultEditView,
                    "Edit All Network Test Results",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(EC2NetworkResultEditView,
                    "Edit EC2 Network Test Results",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(AzureNetworkResultEditView,
                    "Edit Azure Network Test Results",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(EsxiNetworkResultEditView,
                    "Edit ESXi Network Test Results",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(HypervNetworkResultEditView,
                    "Edit Hyperv Network Test Results",
                    icon="fa-pencil-square-o",
                    category="Management")
appbuilder.add_view(BugsPubView,
                    "List Know Failures",
                    icon="fa-angle-double-right",
                    category="TestBugs")
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
appbuilder.add_view(NewTestrunFormView,
                    "New Testrun",
                    icon="fa-upload",
                    category="Management")
appbuilder.add_separator("Management")

#appbuilder.add_view(YamlFormView, "My form View", icon="fa-group", label=_('My form View'),
#                     category="My Forms", category_icon="fa-cogs")
appbuilder.add_view_no_menu(YamlFormView)
appbuilder.add_api(StorageResultModelApi)

# appbuilder.add_separator("TestReports")
# appbuilder.add_separator("Management")
