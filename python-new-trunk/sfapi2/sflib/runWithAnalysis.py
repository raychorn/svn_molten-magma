import os, sys
import traceback

from vyperlogix import misc
from vyperlogix.misc import ioTimeAnalysis

import types

import SfStats

sf_stats = SfStats.SfStats()

def dummy():
    pass

def init_AnalysisDataPoint(name):
    ioTimeAnalysis.initIOTime(name)

def begin_AnalysisDataPoint(name):
    ioTimeAnalysis.ioBeginTime(name)

def end_AnalysisDataPoint(name):
    ioTimeAnalysis.ioEndTime(name)
    
def count_query():
    sf_stats.count_query()

def runWithAnalysis(func=dummy,args=[],_ioElapsedTime=dummy):
    caller = misc.callersName()
    ioTimeAnalysis.initIOTime('%s::%s' % (__name__,caller)) 
    ioTimeAnalysis.ioBeginTime('%s::%s' % (__name__,caller))
    val = None
    try:
        if (len(args) == 0):
            val = func()
        else:
            val = func(args)
    except:
        exc_info = sys.exc_info()
        info_string = '\n'.join(traceback.format_exception(*exc_info))
        print >>sys.stderr, '(%s) Reason: %s' % (misc.funcName(),info_string)
    ioTimeAnalysis.ioEndTime('%s::%s' % (__name__,caller))
    ioTimeAnalysis.ioTimeAnalysisReport()

    _et = 0
    _key_list = [k for k in ioTimeAnalysis._ioTime.keys() if (k.find('SOQL') > -1)]
    for _key in _key_list:
        _et += (0 if (len(_key) == 0) else ioTimeAnalysis._ioTime[_key][0])
    if (_et > 0):
        _soql_per_sec = sf_stats.query_count / _et
        if (_soql_per_sec > 0):
            _ms_per_soql = 1000 / _soql_per_sec
        else:
            if (sf_stats.query_count == 0):
                print >>sys.stderr, '(%s) 1.0 Cannot correctly report ms per SOQL because SOQL per Second reported 0 and we cannot divide Zero by some number at this time; recommend using the functions that count queries from this module.' % (misc.funcName())
            elif ():
                print >>sys.stderr, '(%s) 1.0 Cannot correctly report ms per SOQL because SOQL per Second reported 0 and we cannot divide by Zero at this time.' % (misc.funcName())
            _ms_per_soql = -1
    else:
        print >>sys.stderr, '(%s) 1.0 Cannot correctly report ms per SOQL because SOQL per Second because there is no reported elapsed time from SOQL activities.' % (misc.funcName())

    try:
        v_ioElapsedTime = float(ioTimeAnalysis._ioElapsedTime)
        if (v_ioElapsedTime > 0):
            soql_per_sec = sf_stats.query_count / v_ioElapsedTime
            if (soql_per_sec > 0):
                ms_per_soql = 1000 / soql_per_sec
            else:
                print >>sys.stderr, '(%s) 2.0 Cannot correctly report ms per SOQL because SOQL per Second reported 0 and we cannot divide by Zero at this time.' % (misc.funcName())
                ms_per_soql = -1
            t_analysis_1 = '%-10.2f' % soql_per_sec
            t_analysis_2 = '%-10.4f' % ms_per_soql
            print >>sys.stdout, '(Apparent) SOQL per second = %s or %s ms per SOQL.' % (t_analysis_1.strip(),t_analysis_2.strip())
            if (_et > 0):
                _t_analysis_1 = '%-10.2f' % _soql_per_sec
                _t_analysis_2 = '%-10.4f' % _ms_per_soql
                print >>sys.stdout, '(Actual) SOQL per second = %s or %s ms per SOQL.' % (_t_analysis_1.strip(),_t_analysis_2.strip())
            else:
                print >>sys.stderr, 'Unable to perform Actual SOQL per second analysis because there is no reported elapsed time from SOQL activities.'
        else:
            print >>sys.stderr, 'Unable to perform Actual SOQL per second analysis because _ioElapsedTime is %4.2f.' % (v_ioElapsedTime)
    except:
        exc_info = sys.exc_info()
        info_string = '\n'.join(traceback.format_exception(*exc_info))
        print >>sys.stderr, '(%s) Reason: %s' % (misc.funcName(),info_string)
    print >>sys.stdout, 'SOQL Count=%d' % sf_stats.query_count
    return val
    
