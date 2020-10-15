"""
Actual events to poll for in a CR and operate upon and send Event Notifications
"""
import copy
import datetime
import time
import pprint
import textwrap
from optparse import OptionParser

from NotificationEventHandler import NotificationEventHandler
from sfConstant import *
from sfTaskBranch import SFTaskBranch, SFTaskBranchTool
from MailNotification import MailNotification, WW
from MailMessageQueue import MailMessageQueue
from TimeUtil import parseSfIsoStr, dayNumToTxt

class CR(NotificationEventHandler):
    """ Common bits for Branch Notification events.
    """
    role = None # must be provided by implementation
    notifyRoles = None # must be provided by implementation
    staticRecipients = None

    # override these in the subclasses
#    triggerDays = 7
#    intervalDays = 0
#    windowDays = 1
#    limitTimes = 5

    def timeCal(self):
        rawEventList = []

        # deltaDays is set in the event instance
        delta = datetime.timedelta(days=self.windowDays)
        
        print " Delta :%s" %delta
        
        dt = datetime.datetime.utcfromtimestamp(time.time())
        
        print "DT  :%s" %dt
        
        windowDateTime = dt - delta
        
        print "Window date time: %s" %windowDateTime
        windowIsoDateTime = "%sZ" %windowDateTime.isoformat()
        
        print "ISO Date: %s" %windowIsoDateTime

        # use the window to just as an additional limit so we are only checking
        # branches which may have become "ripe" since windowDays ago.

        sts = self.sfb.getServerTimestamp()
        
        print " STS : %s %s %s %s %s %s %s " %(sts[0], sts[1], sts[2], sts[3],
                                              sts[4], sts[5], sts[6])
                                              
        currentSfDatetime = datetime.datetime(sts[0], sts[1], sts[2], sts[3],
                                              sts[4], sts[5], sts[6])
        
        print " CurrentSFDate Time is: %s" %currentSfDatetime     
        
        print " Limit Times %s" %self.limitTimes
        if hasattr(self, 'limitTimes') and self.limitTimes > 0:
            
            print "Inside if"
            maxTriggerDays = self.triggerDays + (self.intervalDays * self.limitTimes)
            
            print "Max Trigger days %s" %maxTriggerDays
            delta = datetime.timedelta(days=maxTriggerDays) 
            
            print "New Delta %s" %delta           
            maxDateTime = dt - delta
            print "Max date Time %s" %maxDateTime
            maxIsoDateTime = "%sZ" %maxDateTime.isoformat()
            
            print "Max ISO date %s" %maxIsoDateTime
            
        print "End"
                                                                                  
                                  

        
        return ## END poll


   
    

    

class CRTime(CR):
    
    triggerDays = 0
    windowDays = 2
    intervalDays = 0
    limitTimes = 0
    
    pass ## END class TeamInboxReadyHandler
        

class CREvent:
    
    print "Inside CR Event class"
    handlers = ('CRTime',)

    def __init__(self, opts=None):
        self.opts = opts

    def do(self):
        sfTool = SFTaskBranchTool(logname='CRTest')
    
        for handlerName in self.handlers:
            runHandler = '%s(sfTool, self.opts)' %handlerName
            
            handler = eval(runHandler)
            handler.timeCal()
            continue

        return


def main():
    print "Inside main function"
    op = OptionParser()
    op.add_option('-l', '--live', dest='testflag', action='store_false',
                  default=True,
                  help='connects to live storage for events - default is test')

    (opts, args) = op.parse_args()

    harness = CREvent(opts)
    harness.do()

    
if __name__ == '__main__':
    main()
