# /usr/bin/env python
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

logging.basicConfig(level=logging.DEBUG,
                    format='%(levelname)s:%(message)s')

if sys.version.startswith('2'):
    LOG.info("Please do not run it using python2")
    sys.exit(1)

ARG_PARSER = argparse.ArgumentParser(description="Write results to local db")
ARG_PARSER.add_argument('--csv_file', dest='csv_file', action='store',
                        help="specify log directory", default=None, required=False)
ARG_PARSER.add_argument('--db_file', dest='db_file', action='store',
                        help="specify database location", default=None, required=True)
ARG_PARSER.add_argument('--delete', dest='testrun_delete', action='store',
                        help="delete testrun if you want", default=None, required=False)
ARG_PARSER.add_argument('-d', dest='is_debug', action='store_true',
                            help='enable sqlalchemy output for debug purpose', required=False)
ARGS = ARG_PARSER.parse_args()


DB_ENGINE = create_engine('sqlite:///%s' % ARGS.db_file, echo=ARGS.is_debug)
DB_SESSION = sessionmaker(bind=DB_ENGINE)
DB_BASE = declarative_base()

# pylint: disable=R0902,R0903
class TestRun(DB_BASE):
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


class TestResult(DB_BASE):
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

def testrun_write():
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
    testrun = TestRun()
    testrun.testrun = tmp_raw['testrun']
    testrun.platform = tmp_raw['platform']
    testrun.flavor = tmp_raw['flavor']
    testrun.branch = tmp_raw['branch']
    testrun.compose = tmp_raw['compose']
    testrun.kernel = tmp_raw['kernel']
    testrun.casenum = case_count
    testrun.result = ''
    testrun.rawdata = tmp_raw['testrun']

    session = DB_SESSION()
    results = session.query(TestRun).filter_by(testrun=testrun.testrun).all()
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

def testrun_delete():
    if  ARGS.testrun_delete is None:
        LOG.info("Please specify --delete option to delete test run")
        return False
    testrun = ARGS.testrun_delete
    session = DB_SESSION()
    results = session.query(TestRun).filter_by(testrun=testrun).all()
    if len(results) == 0:
        LOG.info("Not found".format(ARGS.testrun_delete))
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

def testresult_write():
    tmp_raw = {}
    case_count = 0
    with open(ARGS.csv_file, newline='') as csv_h:
        readers = csv.DictReader(csv_h)
        for r in readers:
            tmp_raw = r
            case_count += 1
            testresult = TestResult()
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
            testresult.sample = tmp_raw['sample']
            testresult.rawdata = tmp_raw['Path']
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
    
def testresult_delete():
    if  ARGS.testrun_delete is None:
        LOG.info("Please specify --delete option to delete test run")
        return False
    case_count = 0
    testrun = ARGS.testrun_delete
    session = DB_SESSION()
    results = session.query(TestResult).filter_by(testrun=testrun).all()
    if len(results) == 0:
        LOG.info("Not found".format(ARGS.testrun_delete))
        return True
    for testresult in results:
        try:
            LOG.info("Delete test result:{}".format(testresult .testrun))
            session.delete(testresult)
            case_count += 1
        except Exception as err:
            session.rollback()
            LOG.info("{}".format(err))
        else:
            session.commit()
    LOG.info("Line delete: {}".format(case_count))

if __name__ == "__main__":
    if ARGS.csv_file is not None:
        testrun_write()
        testresult_write()
    if ARGS.testrun_delete is not None:
        testrun_delete()
        testresult_delete()