#!/usr/bin/env python3
"""
File:  models.py @flask-appbuilder
Owner: Frank Liang <xiliang@redhat.com>
"""

from flask import Markup, url_for
from flask_appbuilder import Model
from flask_appbuilder.filemanager import ImageManager
from flask_appbuilder.models.mixins import ImageColumn, BaseMixin
from flask_appbuilder.security.sqla.models import User
from sqlalchemy import (Column, ForeignKey, Integer, String, Text, Date, Float,
                        MetaData, DateTime)
from sqlalchemy.orm import relationship
from flask import request
import os

from flask_appbuilder.models.mixins import ImageColumn

import yaml


# Load perf-insight configure
with open(os.path.expanduser('~/.perf-insight.yaml'), 'r') as f:
    user_config = yaml.safe_load(f)

config = user_config.get('global', {})
config.update(user_config.get('dashboard', {}))

FILE_SERVER = config.get('file_server', 'localhost')


class NetworkRun(Model):
    '''
    table for storing network test result
    '''
    id = Column(Integer, primary_key=True)
    testrun = Column(String(100))
    platform = Column(String(50))
    flavor = Column(String(50))
    branch = Column(String(50))
    compose = Column(String(50), nullable=True)
    kernel = Column(String(50))
    casenum = Column(Integer)
    result = Column(String(50))
    # metadata location in the file system
    rawdata = Column(String, nullable=True)

    def rawdata_url(self):
        if self.rawdata:
            return Markup('<a href=http://' + FILE_SERVER +
                          '/perf-insight/testruns/' + str(self.rawdata) +
                          '> rawdata </a>')
        else:
            return self.rawdata

    def __repr__(self):
        return self.id

    def result_url(self):
        print("testrun is {}".format(self.testrun))
        if self.testrun is not None and self.testrun != '' and "None" not in self.testrun:
            self.result = url_for('NetworkResultPubView.list',
                                  _flt_0_testrun=str(self.testrun),
                                  _flt_0_platform=str(self.platform))
            print("testrun is {}".format(self.testrun))
        return Markup('<a href="' + self.result + '">result</a>')


class NetworkResult(Model):
    '''
    table for storing network test result
    '''
    id = Column(Integer, primary_key=True)
    testrun = Column(String(200))
    run_type = Column(String(50))
    platform = Column(String(50))
    flavor = Column(String(50), nullable=True)
    cpu_model = Column(String(100), nullable=True)
    cpu = Column(String(100), nullable=True)
    hypervisor = Column(String(100), nullable=True)
    branch = Column(String(50))
    compose = Column(String(100), nullable=True)
    kernel = Column(String(100))
    vcpu = Column(Integer)
    memory = Column(String(100), nullable=True)
    net_driver = Column(String(100))
    net_duplex = Column(String(100))
    net_speed = Column(String(100))
    protocol = Column(String(100))
    testtype = Column(String(100))
    msize = Column(Integer)
    case_id = Column(String(100), nullable=True)
    instance = Column(Integer)
    sample = Column(Integer)
    throughput = Column(String(50))
    trans = Column(String(50))
    latency = Column(Integer)
    tool_version = Column(String(50))
    date = Column(Date)
    rawdata = Column(String, nullable=True)
    comments = Column(String, nullable=True)

    def rawdata_url(self):
        if self.rawdata:
            return Markup('<a href=http://' + FILE_SERVER +
                          '/perf-insight/testruns/' + str(self.testrun) + '/' +
                          str(self.rawdata) + '> rawdata </a>')
        else:
            return self.raw


class StorageRun(Model):
    '''
    table for storing storage test result
    '''
    id = Column(Integer, primary_key=True)
    testrun = Column(String(100))
    platform = Column(String(50))
    flavor = Column(String(50))
    branch = Column(String(50))
    compose = Column(String(50), nullable=True)
    kernel = Column(String(50))
    casenum = Column(Integer)
    result = Column(String(50))
    # metadata location in the file system
    rawdata = Column(String, nullable=True)

    def rawdata_url(self):
        if self.rawdata:
            return Markup('<a href=http://' + FILE_SERVER +
                          '/perf-insight/testruns/' + str(self.rawdata) +
                          '> rawdata </a>')
        else:
            return self.rawdata

    def __repr__(self):
        return self.id

    def result_url(self):
        print("testrun is {}".format(self.testrun))
        if self.testrun is not None and self.testrun != '' and "None" not in self.testrun:
            self.result = url_for('StorageResultPubView.list',
                                  _flt_0_testrun=str(self.testrun),
                                  _flt_0_platform=str(self.platform))
            print("testrun is {}".format(self.testrun))
        return Markup('<a href="' + self.result + '">result</a>')


class StorageResult(Model):
    '''
    table for storing storage test result
    '''
    id = Column(Integer, primary_key=True)
    testrun = Column(String(100))
    kernel = Column(String(50))
    branch = Column(String(50))
    backend = Column(String(50))
    driver = Column(String(50), nullable=True)
    format = Column(String(50), nullable=True)
    case_id = Column(String(100), nullable=True)
    rw = Column(String(50))
    bs = Column(String(50))
    iodepth = Column(Integer)
    numjobs = Column(Integer)
    iops = Column(Integer)
    latency = Column(Integer)
    clat = Column(Integer)
    tool_version = Column(String(50), nullable=True)
    compose = Column(String(50), nullable=True)
    cpu = Column(String(100), nullable=True)
    cpu_model = Column(String(100), nullable=True)
    memory = Column(String(100), nullable=True)
    platform = Column(String(50))
    flavor = Column(String(50), nullable=True)
    date = Column(Date)
    comments = Column(String, nullable=True)
    sample = Column(String, nullable=True)
    rawdata = Column(String, nullable=True)

    def rawdata_url(self):
        if self.rawdata:
            return Markup('<a href=http://' + FILE_SERVER +
                          '/perf-insight/testruns/' + str(self.testrun) + '/' +
                          str(self.rawdata) + '> rawdata </a>')
        else:
            return self.raw


class ComparedResult(Model):
    '''
    table for storing compared result
    '''
    id = Column(Integer, primary_key=True)
    report_id = Column(String(200))
    baseid = Column(String(200))
    testid = Column(String(200))
    createtime = Column(DateTime)
    reportlink = Column(String(300))
    comments = Column(String, nullable=True)
    benchmark_metadata = Column(Text)

    def report_url(self):
        if self.reportlink:
            return Markup('<a href=http://' + FILE_SERVER +
                          '/perf-insight/reports/{}/report.html '.format(
                              self.reportlink) + '> Report </a>')
        else:
            return self.reportlink


class FailureType(Model):
    '''
    general use: table for specify failure types, eg. product_bug, tool_bug,
                 env_bug
    '''
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(150), unique=True, nullable=True)

    def __repr__(self):
        return self.name


class FailureStatus(Model):
    '''
    general use: table for specify failure status, like closed, open, on_qa,
                 verified, blocker
    '''
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(150), unique=True, nullable=True)

    def __repr__(self):
        return self.name


class Bugs(Model):
    '''
    general use: table for recording all test failures.
    '''
    id = Column(Integer, primary_key=True)
    test_suite = Column(String(50))
    case_name = Column(String(50))
    bug_id = Column(Integer, nullable=True)
    bug_title = Column(String(200), nullable=True)
    failure_id = Column(Integer,
                        ForeignKey("failure_status.id"),
                        nullable=False)
    failure_status = relationship("FailureStatus")
    branch_name = Column(String(50), nullable=True)
    comments = Column(Text)
    last_update = Column(Date)
    create_date = Column(Date)
    failure_type_id = Column(Integer,
                             ForeignKey("failure_type.id"),
                             nullable=False)
    failure_type = relationship("FailureType")
    identify_keywords = Column(Text)
    identify_debuglog = Column(Text)
    contactor = Column(String(50), nullable=True)

    def __repr__(self):
        return self.log_id

    def bug_url(self):
        if self.bug_id:
            return Markup(
                '<a href="https://bugzilla.redhat.com/show_bug.cgi?id=' +
                str(self.bug_id) + '">' + str(self.bug_id) + '</a>')
        else:
            return self.bug_id


class Client(User):
    __tablename__ = "ab_user"
    extra = Column(String(50), unique=True, nullable=False)
