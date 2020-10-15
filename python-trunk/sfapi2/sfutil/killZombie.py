#!/usr/bin/env python2.3
#
# This script checks for Process running a certain program
# and notices if they are using no CPU over a period of time.
# - Requires the script to be run as root :/
# - Initially searches for process running as python2.3
#
version = 1.00    #Nov 15, 2004 - Simple first version

import os, re, sys, string, time, stat
import traceback
import cStringIO as StringIO
import cPickle, marshal
import csv
from optparse import OptionParser, OptionGroup
from sop import SFSOP, AccessFactory


class Process:
    """ Simple view of a process
    """
    cdate= 0                        # 0 seconds from epoch
    stat = ''
    flags = ''
    ppid = 0
    time = 0
    vmem = 0
    nice = 0
    data = []
    user = ''
    uid = ''
    pid = 0
    p2 = 0
    cpu = 0.0
    mem = 0.0
    rss = 0
    tty = ''
    cmd = ''
    head = ''
    
    def __init__(self, pid='', tool=None):
        """ create and load minimal info.
        """
        self.pid = pid
        if tool in [None,'']:
            tool = ProcessTool()
        self.tool = tool
    
    def check(self):
        """ check current state of process """
        pidFile = os.path.join(self.tool.getHome(),'.killZombiePID')
        os.system('ps uw %s > %s'%(self.pid,pidFile))
        #print 'Process.check sent output of pid %s to %s'%(self.pid,pidFile)
        pf = open(pidFile)
        pl = pf.readlines()
        pf.close()
        #os.remove(pidFile)
        #print 'PL: %s\n'%(pl)
        if len(pl) != 2:
            print ' Unknown output from ps uw for %s got\n%s'%(self.pid,pl)
            return []
        self.head = pl[0][:-1]
        p = pl[1]
        if p[-1] == '\n': p = p[:-1]
        if p in [None,'']:
            print ' %s Process must have just ended, skipping'%self.pid
            return []
        pinfo = p.split(' ')
        #print ' split output %s\n into %s'%(p,pinfo)
        #USER       PID %CPU %MEM   VSZ  RSS TTY      STAT START   TIME COMMAND
        #sfscript 23439 67.4  2.3 51276 49468 ?       R    18:15  15:03 /home/sfscript/python/bin/python2.3 /home/sfscript/src/sfapi2/sf
        elements = [self.user, self.p2, self.cpu, self.mem, self.vmem, self.rss, self.tty, self.stat, self.cdate, self.time, self.cmd]
        elIndex = 0
        result = []
        for ev in pinfo:
            if ev not in ['']:
                if len(elements) > elIndex:
                    elements[elIndex] = ev
                    result.append(ev)
                    elIndex +=1
                else:
                    elements[-1] = elements[-1] + ' ' + ev 
                    result[-1] = result[-1] + ' ' + ev
        return result
        

class ProcessCPUSOP(SFSOP):
    """
    Local cache of branch data gathered from ClearCase.
    """
    maxObjAge = 60*60*4 # 4 hours in seconds
    lastUpdate = 0
    lastEntity = ''
    resetStale = False

    def filename(self):
        # this is where the data will be pickled to
        return '/home/sfscript/data/killZombie.pickle'

    def __init__(self):
        SFSOP.__init__(self)

processMap = AccessFactory(ProcessCPUSOP)


class ProcessTool:
    """ long life object that monitors state of processes 
    """
    debug = 1
    map = processMap()
    
    def getMap(self, key, data={}, reset=False):
        """ main accessor for getting branch load status information
        """
        if key in [None,'']: return {}
        if self.debug > 0: print 'Load status for %s loaded %3d secs ago' %(branch, self.map.getAge(key))
        if reset: self.map.reset(True)
        if self.map.isStale(key):
            if self.debug > 2: print 'Updating sop for %s' %key
            self.setMap(key, data)
            if reset: self.map.reset(False)
        return self.map.getData(key)

    def setMap(self, key, data={}):
        """ load the latest metadata for process status into a simple object persitence dictionary
        """
        st = time.time()
        if key in [None,'']: return
        if data in [None,{},[],'']:
            data = {}
        if self.debug > 0: print '%2d sec Got %s keys and in %s' %(time.time()-self.startTime, len(data.keys()), key)
        self.map.setData(key, data)
        self.map.commit()

    def pidof(self, prog='python2.3'):
        pidFile = os.path.join(self.getHome(),'.killZombie')
        os.system('/sbin/pidof %s > %s'%(prog,pidFile))
        print 'pidof sent output of pidof %s to %s'%(prog,pidFile)
        pf = open(pidFile)
        p = pf.readline()
        pf.close()
        if p[-1] == '\n': p = p[:-1]
        pl = p.split(' ')
        print ' split output %s into %s'%(p,pl)
        return pl

    def getHome(self):
        """  Get the os specific home directory """
        home = '.'
        if os.name in ['posix','mac']:
           home = os.environ.get('HOME')
        if home in [None,'']:
            return '.'
        return home
        

        
#############################################################################################################
#   Methods called from the command line - cron oriented to update SalesForce
#############################################################################################################
def checkForZombies(prog='python2.3', maxZombie=600, maxRun=5000):
    """ main logic method to be called from command line
        searches for process run with 'prog' and records
        total CPU Time.  Looks for 2 times maxZombie and kills 
        processes that have no increate in total CPU time for 
        maxZombie seconds
    """
    pt = ProcessTool()
    pids = pt.pidof(prog)
    for pid in pids:
        pObj = Process(pid, tool=pt)
        pInfo = pObj.check()
        print pObj.head
        print pInfo 
        
    


def usage(err=''):
    """  Prints the Usage() statement for the program    """
    m = '%s\n' %err
    m += '  Default usage is to search for zombies then exit\n'
    m += ' '
    m += '    killZombies -p <program> -t <max no CPU seconds> do\n'
    m += '      or\n'
    m += '    killZombies -p python2.3 -t 600 do\n'
    return m


def main_CL():
    """ Command line parsing and and defaults method
    """
    parser = OptionParser(usage=usage(), version='%s'%version)
    parser.add_option("-p", "--prog", dest="prog", default="python2.3", help="program to search in processes")
    parser.add_option("-t", "--ago",  dest="ago",  default=600,         help="secs ago to allow no CPU usage.")
    parser.add_option("-n", "--num",  dest="num",  default=6000,        help="Max seconds to run")
    parser.add_option("-f", "--path",  dest="path", default="./.zombieCPU",  help="file path to store pid->CPU")
    parser.add_option("-q", "--quiet", dest='quiet', default="1",    help="Show less info in output")
    parser.add_option("-d", "--debug", dest='debug', action="count", help="The debug level, use multiple to get more.")
    (options, args) = parser.parse_args()
    if options.debug > 1:
        print ' verbose %s\tdebug %s' %(options.quiet, options.debug)
        print ' prog    %s' %options.prog
        print ' ago     %s' %options.ago
        print ' num     %s' %options.num
        print ' path    %s' %options.path
        print ' args:   %s' %args
    else:
        options.debug = 0
    ago = float(options.ago)
    prog = str(options.prog)
    num = int(options.num)
    if len(args) > 0: 
        branch = args[0]
        checkForZombies(prog,ago,num)
    else:
        print '%s' %usage()

if __name__ == '__main__':
    """ go juice """
    main_CL()
		