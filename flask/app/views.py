from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.api import ModelRestApi
from flask_appbuilder.models.sqla.filters import FilterEqualFunction, FilterContains
from flask_appbuilder.views import (ModelView, CompactCRUDMixin,
                                    MasterDetailView, SimpleFormView, expose)
from flask_appbuilder.widgets import ListBlock, ShowBlockWidget, ListWidget, ShowWidget, FormWidget
from flask_appbuilder import MultipleView
from flask_appbuilder.actions import action
from flask import redirect, render_template, flash, url_for, Markup,request,session
from flask_babel import lazy_gettext as _

from . import appbuilder, db
import subprocess
from .forms import YamlForm
import tempfile

from .models import (StorageRun, StorageResult, Bugs, FailureType,
                     FailureStatus)

# Below import is for charts
import calendar
from flask_appbuilder.charts.views import (DirectByChartView, DirectChartView,
                                           GroupByChartView)
from flask_appbuilder.models.group import (aggregate_sum, aggregate_count,
                                           aggregate, aggregate_avg)

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
            self.result = form.baserun.data + '_' + form.testrun.data
        except Exception as err:
            flash("Please specify baserun and testrun", 'danger')
            self.update_redirect()
            return redirect(self.get_redirect())
        if session.get('yaml2') is not None:
            form.yaml2.data = session['yaml2']
        elif session.get('yaml2') is None or len(session['yaml2']) < 10:
            form.yaml2.data = '''
benchmark_comparison_generator:
  defaults:
    dataframe_round: 2
    dataframe_fillna: "NaN"
  kpi_defaults:
    higher_is_better: yes
    max_percent_dev: 10
    regression_threshold: 0.05
    confidence_threshold: 0.95
  keys:
    - name: RW
    - name: BS
    - name: IOdepth
    - name: Numjobs
  kpis:
    - name: IOPS
    - name: LAT
      unit: ms
      from: LAT(ms)
      higher_is_better: no
    - name: CLAT
      unit: ms
      from: CLAT(ms)
      higher_is_better: no        
        '''
        if session.get('yaml1') is not None:
            form.yaml1.data = session['yaml1']
        elif session.get('yaml1') is None or len(session['yaml1']) < 10:
            form.yaml1.data = '''
testrun_results_generator:
  defaults:
    split: yes
  columns:
    - name: Backend
      source: metadata
      key: disk.backend
    - name: Driver
      source: metadata
      key: disk.driver
    - name: Format
      source: metadata
      key: disk.format
    - name: RW
      source: datastore
      jqexpr: ".iteration_data.parameters.benchmark[].rw"
    - name: BS
      source: datastore
      jqexpr: ".iteration_data.parameters.benchmark[].bs"
    - name: IOdepth
      source: datastore
      jqexpr: ".iteration_data.parameters.benchmark[].iodepth"
    - name: Numjobs
      source: datastore
      jqexpr: ".iteration_data.parameters.benchmark[].numjobs"
    - name: Sample
      source: auto
    - name: IOPS
      source: datastore
      jqexpr: '.iteration_data.throughput.iops_sec[] | select(.client_hostname=="all") | .samples[].value'
      multiple: true
    - name: LAT
      source: datastore
      jqexpr: '.iteration_data.latency.lat[] | select(.client_hostname=="all") | .samples[].value'
      unit: ms
      factor: 0.000001
    - name: CLAT
      source: datastore
      jqexpr: '.iteration_data.latency.clat[] | select(.client_hostname=="all") | .samples[].value'
      unit: ms
      factor: 0.000001
    - name: Path
      source: auto
        '''

    def form_post(self, form):
        # post process form
        tmpdir = tempfile.mkdtemp(suffix=None, prefix='jupiter', dir='/tmp/benchmark_reports/')
        print('save to {}'.format(tmpdir))
        tmp = tmpdir + '/' + 'generate_testrun_results.yaml'
        with open(tmp,'w') as fh:
            fh.write(form.yaml1.data)
        tmp = tmpdir + '/' + 'generate_2way_benchmark.yaml'
        with open(tmp,'w') as fh:
            fh.write(form.yaml2.data)
        self.message = Markup(' Please wait for 2 minutes, the compare result will be available at <a href="/static/workspace/benchmark_reports/{}/default.html" class="alert-link">compared {}</a> '.format(tmpdir, self.result))
        # to do: prepare data for jupiter here.
        flash(self.message, 'success')
        cmd = 'podman xxxxxxx xxxx &'
        subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120, encoding='utf-8')
        #session['yaml1'] = form.yaml1.data
        #session['yaml2'] = form.yaml2.data
        return redirect(request.url)

class MyListWidget(ListWidget):
     template = 'widgets/my_list.html'

class MyShowWidget(ShowWidget):
     template = 'widgets/my_show.html'

class StorageRunPubView(ModelView):
    datamodel = SQLAInterface(StorageRun)
    base_permissions = ["can_list", "can_show", "menu_access"]
    #show_widget = MyShowWidget
    #list_widget = MyListWidget
    @action("compareruns", "Compare2runs", "Compare 2 test runs?", "fa-rocket", single=False)
    def compareruns(self, items):
        testruns=''
        
        if len(items) != 2:
            flash("Please choose 2 testruns to compare!", 'danger')
            self.update_redirect()
            return redirect(self.get_redirect())
        else:
            for item in items:
                testruns+=item.testrun + '_'
            testruns = testruns.rstrip('_')
        #form = YamlForm
        baserun, testrun = items[0].testrun, items[1].testrun
        #return self.render_template(self.yaml_template, form=form, appbuilder=self.appbuilder)
        return redirect("/yamlformview/form?baserun={}&testrun={}".format(testrun,baserun))

    label_columns = {"debug_url": "Result","rawdata_url": "RawData"}

    list_columns = [
        "id","testrun","platform","flavor","branch","compose",
                "kernel","casenum","result_url","rawdata_url"
    ]
    search_columns = [
        "id","testrun","platform","flavor","branch","compose",
                "kernel","casenum","result","rawdata"
    ]

    show_fieldsets = [
        ("Summary", {
            "fields": [
                "id","testrun","platform","flavor","branch","compose",
                "kernel","casenum","result_url","rawdata_url"
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

    label_columns = {"latency": "LAT(ms)",'clat':'CLAT(ms)',"rawdata_url": "RawData",'iops':'IOPS',
                    'rw':'RW','bs':'BS','iodepth':'IOdepth','cpu':'CPU','cpu_model':'CPU Model'}

    list_columns = [
        "testrun","flavor","backend","driver","format","rw","bs","iodepth","numjobs",
                "sample","iops","latency","clat"
    ]
    search_columns = [
        'id', 'testrun', 'kernel', 'branch', 'backend', 'driver', 'format', 'rw', 'bs',
        'iodepth', 'numjobs', 'iops', 'latency', 'clat', 'tool_version', 'compose',
        'cpu', 'cpu_model', 'memory', 'platform', 'flavor', 'run_time', 'comments', 'sample',
        'testrun'
    ]

    show_fieldsets = [
        ("Summary", {
            "fields": [
                'testrun', 'platform', 'flavor', 'branch', 'compose', 'kernel', 'cpu', 'cpu_model', 'memory','backend', 'driver', 'format', 'rw', 'bs',
                'iodepth', 'numjobs', 'sample', 'iops', 'latency', 'clat', 'tool_version', 
                   'run_time',  'rawdata_url', 'comments'
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
                    icon="fa-folder-open-o",
                    category="StorageTestRun")
appbuilder.add_view(EC2StorageRunPubView,
                    "EC2 Test Runs",
                    icon="fa-folder-open-o",
                    category="StorageTestRun")
appbuilder.add_view(AzureStorageRunPubView,
                    "Azure Test Runs",
                    icon="fa-folder-open-o",
                    category="StorageTestRun")
appbuilder.add_view(EsxiStorageRunPubView,
                    "Esxi Test Runs",
                    icon="fa-folder-open-o",
                    category="StorageTestRun")
appbuilder.add_view(HypervStorageRunPubView,
                    "Hyperv Test Runs",
                    icon="fa-folder-open-o",
                    category="StorageTestRun")
appbuilder.add_view(StorageResultPubView,
                    "All Test Results",
                    icon="fa-folder-open-o",
                    category="StorageTestResult")
appbuilder.add_view(EC2StorageResultPubView,
                    "EC2 Test Results",
                    icon="fa-folder-open-o",
                    category="StorageTestResult")
appbuilder.add_view(AzureStorageResultPubView,
                    "Azure Test Results",
                    icon="fa-folder-open-o",
                    category="StorageTestResult")
appbuilder.add_view(EsxiStorageResultPubView,
                    "Esxi Test Results",
                    icon="fa-folder-open-o",
                    category="StorageTestResult")
appbuilder.add_view(HypervStorageResultPubView,
                    "Hyperv Test Results",
                    icon="fa-folder-open-o",
                    category="StorageTestResult")

appbuilder.add_view(StorageRunEditView,
                    "Edit All Test Runs",
                    icon="fa-folder-open-o",
                    category="Management")
appbuilder.add_view(EC2StorageRunEditView,
                    "Edit EC2 Test Runs",
                    icon="fa-folder-open-o",
                    category="Management")
appbuilder.add_view(AzureStorageRunEditView,
                    "Edit Azure Test Runs",
                    icon="fa-folder-open-o",
                    category="Management")
appbuilder.add_view(EsxiStorageRunEditView,
                    "Edit Esxi Test Runs",
                    icon="fa-folder-open-o",
                    category="Management")
appbuilder.add_view(HypervStorageRunEditView,
                    "Edit Hyperv Test Runs",
                    icon="fa-folder-open-o",
                    category="Management")
appbuilder.add_view(StorageResultEditView,
                    "Edit All Test Results",
                    icon="fa-folder-open-o",
                    category="Management")
appbuilder.add_view(EC2StorageResultEditView,
                    "Edit EC2 Test Results",
                    icon="fa-folder-open-o",
                    category="Management")
appbuilder.add_view(AzureStorageResultEditView,
                    "Edit Azure Test Results",
                    icon="fa-folder-open-o",
                    category="Management")
appbuilder.add_view(EsxiStorageResultEditView,
                    "Edit Esxi Test Results",
                    icon="fa-folder-open-o",
                    category="Management")
appbuilder.add_view(HypervStorageResultEditView,
                    "Edit Hyperv Test Results",
                    icon="fa-folder-open-o",
                    category="Management")
appbuilder.add_view(BugsPubView,
                    "List Know Failures",
                    icon="fa-folder-open-o",
                    category="TestBugs")
appbuilder.add_view(BugsView,
                    "Edit Know Failures",
                    icon="fa-envelope",
                    category="Management")
appbuilder.add_view(FailureTypeView,
                    "Edit Know Failures Types",
                    icon="fa-envelope",
                    category="Management")
appbuilder.add_view(FailureStatusView,
                    "Edit Failures Status List",
                    icon="fa-envelope",
                    category="Management")
appbuilder.add_separator("Management")

#appbuilder.add_view(YamlFormView, "My form View", icon="fa-group", label=_('My form View'),
#                     category="My Forms", category_icon="fa-cogs")
appbuilder.add_view_no_menu(YamlFormView)
appbuilder.add_api(StorageResultModelApi)

# appbuilder.add_separator("TestReports")
# appbuilder.add_separator("Management")
