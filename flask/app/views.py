from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.api import ModelRestApi
from flask_appbuilder.models.sqla.filters import FilterEqualFunction, FilterContains
from flask_appbuilder.views import (ModelView, CompactCRUDMixin,
                                    MasterDetailView, SimpleFormView)
from flask_appbuilder.widgets import ListBlock, ShowBlockWidget, ListWidget, ShowWidget
from flask_appbuilder import MultipleView
from flask_appbuilder.actions import action
from flask import redirect, render_template, flash, url_for, Markup

from . import appbuilder, db
import subprocess

from .models import (Storage_Run, Storage_Result, Bugs, FailureType,
                     FailureStatus)

# Below import is for charts
import calendar
from flask_appbuilder.charts.views import (DirectByChartView, DirectChartView,
                                           GroupByChartView)
from flask_appbuilder.models.group import (aggregate_sum, aggregate_count,
                                           aggregate, aggregate_avg)

class MyListWidget(ListWidget):
     template = 'widgets/my_list.html'

class MyShowWidget(ShowWidget):
     template = 'widgets/my_show.html'

class StorageRunPubView(ModelView):
    datamodel = SQLAInterface(Storage_Run)
    base_permissions = ["can_list", "can_show", "menu_access"]
    #show_widget = MyShowWidget
    #list_widget = MyListWidget
    @action("compareruns", "Compare2runs", "Compare 2 test runs?", "fa-rocket", single=False)
    def compareruns(self, items):
        testruns=''
        if len(items) != 2:
            flash("Please choose 2 testruns to compare!", 'danger')
        else:
            for item in items:
                testruns+=item.testrun + '&'
            testruns = testruns.rstrip('&')
            # to do: prepare data for jupiter here.
            flash(Markup('Access compare result, click <a href="/me" class="alert-link">compared {}</a> '.format(testruns)),'success')
        self.update_redirect()
        return redirect(self.get_redirect())

    label_columns = {"debug_url": "Result"}

    list_columns = [
        "id","testrun","platform","flavor","branch","compose",
                "kernel","casenum","result_url"
    ]
    search_columns = [
        "id","testrun","platform","flavor","branch","compose",
                "kernel","casenum","result","metadata_l"
    ]

    show_fieldsets = [
        ("Summary", {
            "fields": [
                "id","testrun","platform","flavor","branch","compose",
                "kernel","casenum","result_url","metadata_l"
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

class StorageRunModelApi(ModelRestApi):
    resource_name = 'storageruns'
    datamodel = SQLAInterface(Storage_Run)

class StorageResultPubView(ModelView):
    datamodel = SQLAInterface(Storage_Result)
    base_permissions = ["can_list", "can_show", "menu_access"]
    # list_widget = ListBlock
    # show_widget = ShowBlockWidget
    # show_template = 'my_show.html'

    label_columns = {"latency": "LAT(ms)",'clat':'CLAT(ms)',"details_url": "Details",'iops':'IOPS',
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
                'iodepth', 'numjobs', 'sample', 'iops', 'latency', 'clat', 'path', 'tool_version', 
                   'run_time',  'details_url', 'comments'
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
    datamodel = SQLAInterface(Storage_Result)

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
appbuilder.add_view(StorageResultPubView,
                    "Full Test Results",
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
appbuilder.add_view(StorageResultEditView,
                    "Edit Full Test Results",
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

appbuilder.add_api(StorageResultModelApi)

# appbuilder.add_separator("TestReports")
# appbuilder.add_separator("Management")
