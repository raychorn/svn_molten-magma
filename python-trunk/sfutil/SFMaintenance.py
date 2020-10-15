#!/usr/bin/python

'''
SFMaintenance is a harness for managing the various maintenance tasks that
must be performed.

To add a task, define a handler to wrap the task, and add the handler to
the queue. Preference is to make use of the config file for settings to
any tasks to be managed here.

To run a queue, SFMaintenance is invoked with the name of the queue to run.

Scheduling is provided by cron. Add a cron line to run an
SFMaintenance queue at the desired time(s). For example to run
SFMaintenance every five minutes:

0,5,10,15,20,25,30,35,40,45,50,55 * * * * ~/sfsrc/sfutil/bin/SFMaintenance every5
'''

import os, glob, re, stat, time, sys
import ConfigHelper

## Defines queues and the handlers to run, in order, for each queue here
queues = {'every5':['tokenMinderHandler'],
          'hourly':['hideCasesHandler'],
          'weekly':['sfBackupHandler'],
          'daily':['crossUserContactHandler'],
          'test': ['crossUserContactHandler']}


###########################################################################
#
# Define task handlers here, including importing any add'l libraries
# needed only for said handler
#
###########################################################################

def tokenMinderHandler():
    import TokenMinder
    tm = TokenMinder.TokenMinder(props)
    tm.do()
## END tokenMinderHandler()


def hideCasesHandler():
    import hideCases
    hc = hideCases.hideCaseBase(props)
    hc.do()
## END hideCRsHandler()

def sfBackupHandler():
    import sfBackup
    hc = sfBackup.Backup(props)
    hc.do()
## END hideCRsHandler()

def sfNotifyHandler():
    import sfNotify
    sfn = sfNotify.Notify(props)
    sfn.do()
## END hideCRsHandler()

def feGroupReportHandler():
    import sfFetchFEReport
    fereport = sfFetchFEReport.FEReport(props)
    fereport.do()
## END hideCRsHandler()

def crossUserContactHandler():
    import crossUserContactId
    u2cm = crossUserContactId.User2ContactMatch()
    u2cm.expandId15ToId18()
    u2cm.expandContactIDRefFields()
## END crossUserContactHandler()

## END handlers ############################################################
    

def usage(err=None):
    """
    Formats a usage mesage for SFMaintenance
    """
    msg = ""

    if err:
        msg += "\nError: %s\n\n" %err

    msg +=  "usage:\n"
    msg += "SFMaintenance QUEUENAME\n\n"
    msg += "Valid queues are:\n"

    for queuename in queues.keys():
        msg += "\t%s\n" %queuename
        
    return msg
## END usage()


def main():
    """
    The main SFmaintenance flow -
    Runs handlers for all tasks listed in the specified queue
    """
    # Fetch the config - tuck into a global variable for easy access by
    # handlers
    global props
    props = ConfigHelper.fetchConfig('conf/sfutil.cfg')
    batchOwner = props.get('main', 'batchOwner')

    if len(sys.argv) != 2:
        print usage("Wrong number of arguments!")
        sys.exit()
    else:
        runqueue = sys.argv[1]
    
    # script must run as batchOwner
    try:
        if os.getlogin() != batchOwner:
            print "Script must run as " + batchOwner
            sys.exit()
    except OSError:
        # os.getlogin doesn't work if run from cron
        pass
    
    if queues.has_key(runqueue):
        for task in queues[runqueue]:
            runCmd = "%s()" %task
            try:
                exec runCmd
            except Exception, e:
                print "An error occurred while running handler %s in queue %s:\n%s" %(runCmd, runqueue, e)
    else:
        print usage("Invalid queue name: %s" %runqueue)
## END main()
    
if __name__ == '__main__':
    main()

