from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.api import ModelRestApi
from flask_appbuilder.models.sqla.filters import FilterEqualFunction, FilterContains
from flask_appbuilder.views import (ModelView, CompactCRUDMixin,
                                    MasterDetailView)
from flask_appbuilder.widgets import ListBlock, ShowBlockWidget
from flask_appbuilder import MultipleView

from . import appbuilder, db

from .models import (Storage_Report, Bugs, FailureType,
                     FailureStatus)

# Below import is for charts
import calendar
from flask_appbuilder.charts.views import (DirectByChartView, DirectChartView,
                                           GroupByChartView)
from flask_appbuilder.models.group import (aggregate_sum, aggregate_count,
                                           aggregate, aggregate_avg)

class StorageReportPubView(ModelView):
    datamodel = SQLAInterface(Storage_Report)
    base_permissions = ["can_list", "can_show", "menu_access"]
    # list_widget = ListBlock
    # show_widget = ShowBlockWidget

    label_columns = {"debug_url": "Result"}

    list_columns = [
        "id","kernel","testrun","backend","format","rw","bs",
                "rw","iodepth","numjobs","round","bw","iops","latency","test_date"
    ]
    search_columns = [
        "id","kernel","branch","compose","cpu","memory","platform","instance_type",
        "test_date","comments","testrun","debug","backend","driver","format","rw","bs",
        "rw","iodepth","numjobs","round","bw","iops","latency","tool_version"
    ]

    show_fieldsets = [
        ("Summary", {
            "fields": [
                "id","kernel","branch","compose","cpu","memory","platform","instance_type",
                "test_date","comments","testrun","debug_url","backend","driver","format","rw","bs",
                "rw","iodepth","numjobs","round","bw","iops","latency","tool_version"
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

class EC2StorageReportPubView(StorageReportPubView):
    base_filters = [["platform", FilterContains, 'ec2']]

class AzureStorageReportPubView(StorageReportPubView):
    base_filters = [["platform", FilterContains, 'azure']]

class EsxiStorageReportPubView(StorageReportPubView):
    base_filters = [["platform", FilterContains, 'esxi']]

class HypervStorageReportPubView(StorageReportPubView):
    base_filters = [["platform", FilterContains, 'hyperv']]

class StorageReportEditView(StorageReportPubView):
    base_permissions = [
        "can_list", "can_show", "menu_access", "can_add", "can_edit",
        "can_delete"
    ]

class StorageReportModelApi(ModelRestApi):
    resource_name = 'storage'
    datamodel = SQLAInterface(Storage_Report)

class EC2StorageReportEditView(EC2StorageReportPubView):
    base_permissions = [
        "can_list", "can_show", "menu_access", "can_add", "can_edit",
        "can_delete"
    ]

class AzureStorageReportEditView(AzureStorageReportPubView):
    base_permissions = [
        "can_list", "can_show", "menu_access", "can_add", "can_edit",
        "can_delete"
    ]

class EsxiStorageReportEditView(EsxiStorageReportPubView):
    base_permissions = [
        "can_list", "can_show", "menu_access", "can_add", "can_edit",
        "can_delete"
    ]

class HypervStorageReportEditView(HypervStorageReportPubView):
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
appbuilder.add_view(StorageReportPubView,
                    "Full Test Results",
                    icon="fa-folder-open-o",
                    category="StorageTestResult")
appbuilder.add_view(EC2StorageReportPubView,
                    "EC2 Test Results",
                    icon="fa-folder-open-o",
                    category="StorageTestResult")
appbuilder.add_view(AzureStorageReportPubView,
                    "Azure Test Results",
                    icon="fa-folder-open-o",
                    category="StorageTestResult")
appbuilder.add_view(EsxiStorageReportPubView,
                    "Esxi Test Results",
                    icon="fa-folder-open-o",
                    category="StorageTestResult")
appbuilder.add_view(HypervStorageReportPubView,
                    "Hyperv Test Results",
                    icon="fa-folder-open-o",
                    category="StorageTestResult")

appbuilder.add_view(StorageReportEditView,
                    "Edit Full Test Results",
                    icon="fa-folder-open-o",
                    category="Management")
appbuilder.add_view(EC2StorageReportEditView,
                    "Edit EC2 Test Results",
                    icon="fa-folder-open-o",
                    category="Management")
appbuilder.add_view(AzureStorageReportEditView,
                    "Edit Azure Test Results",
                    icon="fa-folder-open-o",
                    category="Management")
appbuilder.add_view(EsxiStorageReportEditView,
                    "Edit Esxi Test Results",
                    icon="fa-folder-open-o",
                    category="Management")
appbuilder.add_view(HypervStorageReportEditView,
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

appbuilder.add_api(StorageReportModelApi)

# appbuilder.add_separator("TestReports")
# appbuilder.add_separator("Management")
