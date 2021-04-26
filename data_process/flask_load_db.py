#!/usr/bin/env python
'''
Write/delete test data to sqlite for flask

'''
from __future__ import print_function
import json
import sys
import re
import os
import argparse
import logging
import time
import csv
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

LOG = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(message)s')

if sys.version.startswith('2'):
    LOG.info("Please do not run it using python2")
    sys.exit(1)

ARG_PARSER = argparse.ArgumentParser(description="Write results to local db")
ARG_GROUP = ARG_PARSER.add_mutually_exclusive_group(required=True)
ARG_PARSER.add_argument('--csv_file',
                        dest='csv_file',
                        action='store',
                        help="specify log directory",
                        default=None,
                        required=False)
ARG_PARSER.add_argument('--db_file',
                        dest='db_file',
                        action='store',
                        help="specify database location",
                        default=None,
                        required=True)
ARG_PARSER.add_argument('--delete',
                        dest='testrun_delete',
                        action='store',
                        help="delete testrun if you want",
                        default=None,
                        required=False)
ARG_PARSER.add_argument('-d',
                        dest='is_debug',
                        action='store_true',
                        help='enable sqlalchemy output for debug purpose',
                        required=False)
ARG_GROUP.add_argument('--network',
                       dest='is_network',
                       action='store_true',
                       help='write net test result',
                       required=False)
ARG_GROUP.add_argument('--storage',
                       dest='is_storage',
                       action='store_true',
                       help='write storage test result',
                       required=False)
ARGS = ARG_PARSER.parse_args()

DB_ENGINE = create_engine('sqlite:///%s' % ARGS.db_file, echo=ARGS.is_debug)
DB_SESSION = sessionmaker(bind=DB_ENGINE)
DB_BASE = declarative_base()


# pylint: disable=R0902,R0903
class NetworkRun(DB_BASE):
    '''
    The network run table's schema definication.
    '''
    __tablename__ = 'network_run'
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
    sqlite_autoincrement = True


class NetworkResult(DB_BASE):
    '''
    The network result table's schema definication.
    '''
    __tablename__ = 'network_result'
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
    instance = Column(Integer)
    sample = Column(Integer)
    throughput = Column(String(50))
    trans = Column(String(50))
    latency = Column(Integer)
    tool_version = Column(String(50))
    date = Column(String)
    rawdata = Column(String, nullable=True)
    comments = Column(String, nullable=True)
    sqlite_autoincrement = True


class StorageTestRun(DB_BASE):
    '''
    The table's schema definication.
    '''
    __tablename__ = 'storage_run'
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
    rawdata = Column(String)
    sqlite_autoincrement = True


class StorageTestResult(DB_BASE):
    '''
    table for storing test result
    '''
    __tablename__ = 'storage_result'
    id = Column(Integer, primary_key=True)
    testrun = Column(String(100))
    kernel = Column(String(50))
    branch = Column(String(50))
    backend = Column(String(50))
    driver = Column(String(50), nullable=True)
    format = Column(String(50), nullable=True)
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
    date = Column(String)
    comments = Column(String, nullable=True)
    sample = Column(String, nullable=True)
    testrun = Column(String(100))
    rawdata = Column(String, nullable=True)
    sqlite_autoincrement = True


def network_testrun_write():
    tmp_raw = {}
    case_count = 0
    with open(ARGS.csv_file, newline='') as csv_h:
        readers = csv.DictReader(csv_h)
        for r in readers:
            tmp_raw = r
            case_count += 1

    if case_count == 0:
        LOG.info("No row found, please check!")
        sys.exit(1)
    testrun = NetworkRun()
    testrun.testrun = tmp_raw['Testrun']
    testrun.platform = tmp_raw['Platform']
    testrun.flavor = tmp_raw['Flavor']
    testrun.branch = tmp_raw['Branch']
    testrun.compose = tmp_raw['Compose']
    testrun.kernel = tmp_raw['Kernel']
    testrun.casenum = case_count
    testrun.result = ''
    testrun.rawdata = tmp_raw['Testrun']

    if not testrun.testrun.startswith('uperf_'):
        LOG.error('TestRun ID "{}" is invalid.'.format(testrun.testrun))
        return 1

    session = DB_SESSION()
    results = session.query(NetworkRun).filter_by(
        testrun=testrun.testrun).all()
    if len(results) >= 1:
        LOG.info("{} already exists!".format(testrun.testrun))
        sys.exit(1)
    try:
        LOG.info("Create new test run:{}".format(testrun.testrun))
        session.add(testrun)
    except Exception as err:
        session.rollback()
        LOG.info("{}".format(err))
    else:
        session.commit()


def network_testresult_write():
    tmp_raw = {}
    case_count = 0
    with open(ARGS.csv_file, newline='') as csv_h:
        readers = csv.DictReader(csv_h)
        for r in readers:
            tmp_raw = r
            case_count += 1
            print('.', end='', flush=True)
            testresult = NetworkResult()
            testresult.testrun = tmp_raw['Testrun']
            testresult.run_type = tmp_raw['Type']
            testresult.platform = tmp_raw['Platform']
            testresult.flavor = tmp_raw['Flavor']
            testresult.cpu_model = tmp_raw['CPU_Model']
            testresult.cpu = tmp_raw['CPU']
            testresult.hypervisor = tmp_raw['Hypervisor']
            testresult.branch = tmp_raw['Branch']
            testresult.compose = tmp_raw['Compose']
            testresult.kernel = tmp_raw['Kernel']
            testresult.vcpu = tmp_raw['vCPU']
            testresult.memory = tmp_raw['Memory']
            testresult.net_driver = tmp_raw['Net-Driver']
            testresult.net_duplex = tmp_raw['Net-Duplex']
            testresult.net_speed = tmp_raw['Net-Speed']
            testresult.protocol = tmp_raw['Protocol']
            testresult.testtype = tmp_raw['TestType']
            testresult.msize = tmp_raw['MSize']
            testresult.instance = tmp_raw['Instance']
            testresult.sample = tmp_raw['Sample']
            testresult.throughput = tmp_raw['Throughput(Mb/s)']
            testresult.trans = tmp_raw['Trans(t/s)']
            testresult.latency = tmp_raw['Latency(us)']
            testresult.tool_version = tmp_raw['Tool_Version']
            testresult.rawdata = tmp_raw['Path']
            testresult.date = tmp_raw['Date']
            testresult.comments = ''

            if not testresult.testrun.startswith('uperf_'):
                LOG.error('TestRun ID "{}" is invalid.'.format(
                    testresult.testrun))
                return 1

            session = DB_SESSION()
            try:
                session.add(testresult)
            except Exception as err:
                session.rollback()
                LOG.info("{}".format(err))
            else:
                session.commit()
        print('Done')

    if case_count == 0:
        LOG.info("No row found, please check!")
        sys.exit(1)
    else:
        LOG.info("Line wrote: {}".format(case_count))


def storage_testrun_write():
    tmp_raw = {}
    case_count = 0
    with open(ARGS.csv_file, newline='') as csv_h:
        readers = csv.DictReader(csv_h)
        for r in readers:
            tmp_raw = r
            case_count += 1

    if case_count == 0:
        LOG.info("No row found, please check!")
        sys.exit(1)
    testrun = StorageTestRun()
    testrun.testrun = tmp_raw['testrun']
    testrun.platform = tmp_raw['platform']
    testrun.flavor = tmp_raw['flavor']
    testrun.branch = tmp_raw['branch']
    testrun.compose = tmp_raw['compose']
    testrun.kernel = tmp_raw['kernel']
    testrun.casenum = case_count
    testrun.result = ''
    testrun.rawdata = tmp_raw['testrun']

    if not testrun.testrun.startswith('fio_'):
        LOG.error('TestRun ID "{}" is invalid.'.format(testrun.testrun))
        return 1

    session = DB_SESSION()
    results = session.query(StorageTestRun).filter_by(
        testrun=testrun.testrun).all()
    if len(results) >= 1:
        LOG.info("{} already exists!".format(testrun.testrun))
        sys.exit(1)
    try:
        LOG.info("Create new test run:{}".format(testrun.testrun))
        session.add(testrun)
    except Exception as err:
        session.rollback()
        LOG.info("{}".format(err))
    else:
        session.commit()


def storage_testresult_write():
    tmp_raw = {}
    case_count = 0
    with open(ARGS.csv_file, newline='') as csv_h:
        readers = csv.DictReader(csv_h)
        for r in readers:
            tmp_raw = r
            case_count += 1
            testresult = StorageTestResult()
            testresult.testrun = tmp_raw['testrun']
            testresult.kernel = tmp_raw['kernel']
            testresult.branch = tmp_raw['branch']
            testresult.backend = tmp_raw['backend']
            testresult.driver = tmp_raw['driver']
            testresult.format = tmp_raw['format']
            testresult.rw = tmp_raw['rw']
            testresult.bs = tmp_raw['bs']
            testresult.iodepth = tmp_raw['iodepth']
            testresult.numjobs = tmp_raw['numjobs']
            testresult.iops = tmp_raw['iops']
            testresult.latency = tmp_raw['lat(ms)']
            testresult.clat = tmp_raw['clat(ms)']
            testresult.tool_version = tmp_raw['']
            testresult.compose = tmp_raw['tool_version']
            testresult.cpu = tmp_raw['cpu']
            testresult.cpu_model = tmp_raw['cpu_model']
            testresult.memory = tmp_raw['memory']
            testresult.platform = tmp_raw['platform']
            testresult.flavor = tmp_raw['flavor']
            #tmp_date = time.strptime(tmp_raw['date'], "%a %b %d %H:%M:%S %Z %Y")
            #testresult.date = "{}-{}-{}".format(tmp_date.tm_year,tmp_date.tm_mon,tmp_date.tm_mday)
            testresult.date = tmp_raw['date']
            testresult.comments = tmp_raw['comments']
            testresult.sample = tmp_raw['Sample']
            testresult.rawdata = tmp_raw['Path']

            if not testresult.testrun.startswith('fio_'):
                LOG.error('TestRun ID "{}" is invalid.'.format(
                    testresult.testrun))
                return 1

            session = DB_SESSION()
            try:
                session.add(testresult)
            except Exception as err:
                session.rollback()
                LOG.info("{}".format(err))
            else:
                session.commit()

    if case_count == 0:
        LOG.info("No row found, please check!")
        sys.exit(1)
    else:
        LOG.info("Line wrote: {}".format(case_count))


def testrun_delete(runmode=None):
    if ARGS.testrun_delete is None:
        LOG.info("Please specify --delete option to delete test run")
        return False
    testrun = ARGS.testrun_delete
    session = DB_SESSION()
    results = session.query(runmode).filter_by(testrun=testrun).all()
    if len(results) == 0:
        LOG.info("Not found in test runs".format(ARGS.testrun_delete))
        return True
    for testrun in results:
        try:
            LOG.info("Delete test run:{}".format(testrun.testrun))
            session.delete(testrun)
        except Exception as err:
            session.rollback()
            LOG.info("{}".format(err))
        else:
            session.commit()


def testresult_delete(resultmode=None):
    if ARGS.testrun_delete is None:
        LOG.info("Please specify --delete option to delete test run")
        return False
    case_count = 0
    testrun = ARGS.testrun_delete
    session = DB_SESSION()
    results = session.query(resultmode).filter_by(testrun=testrun).all()
    if len(results) == 0:
        LOG.info("Not found in test results".format(ARGS.testrun_delete))
        return True
    for testresult in results:
        try:
            print('.', end='', flush=True)
            #LOG.info("Delete test result: id-{} {}".format(testresult.id, testresult.testrun))
            session.delete(testresult)
            case_count += 1
        except Exception as err:
            session.rollback()
            LOG.info("{}".format(err))
        else:
            session.commit()
    print('Done')
    LOG.info("Line delete: {}".format(case_count))


if __name__ == "__main__":
    if ARGS.csv_file is not None:
        if ARGS.is_network:
            network_testrun_write()
            network_testresult_write()
        elif ARGS.is_storage:
            storage_testrun_write()
            storage_testresult_write()
    if ARGS.testrun_delete is not None:
        if ARGS.is_network:
            testrun_delete(runmode=NetworkRun)
            testresult_delete(resultmode=NetworkResult)
        elif ARGS.is_storage:
            testrun_delete(runmode=StorageTestRun)
            testresult_delete(resultmode=StorageTestResult)