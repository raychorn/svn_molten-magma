""" 
This is the new CaseWatcherList process - the old one seems dead. 

SalesForce Data: Last Process Time
Notifications ?
""" 
import pprint 
import sys 
import textwrap 
import datetime 
from optparse import OptionParser 
 
from sfMagma import * 
from sfConstant import * 
from sfUtil import * 

sfUrl = salesForceURL()

_stdOut = None

class CaseWatcherList(SFMagmaTool): 
     
    logname = 'CaseWatherList2' 
    
    d_caseWatchers = {}
     
    def _getLastProcessDate(self):
        checksince = getLastProcessDate2({'update' : False, 'filename' : 'LastCaseWatcherProcessedDate', 'diff_minutes' : -15})
        return  checksince
    
    def getCaseWatcherById(self, id): 
        soql="Select c.Account__c, c.Case_Fields__c, c.Case_Fields_Deferred__c, c.Case_Number__c, c.Case_Scope__c, c.Component__c, c.Id, c.Name, c.Tech_Campaign__c, c.User__c from Case_Watcher__c c where c.Id='%s'" % id
        ret = self.query('Case_Watcher__c', soql=soql)
        if ret in BAD_INFO_LIST:
            msg ="Could not find any Case_Watcher__c Object(s) for %s()" % functionName()
            print >> sys.stderr, msg 
        else: 
            return ret[0]
        return None

    def getComponentById(self, id): 
        soql="Select c.Id, c.Name from Component__c c where c.Id='%s'" % id
        ret = self.query('Component__c', soql=soql)
        if ret in BAD_INFO_LIST:
            msg ="Could not find any Component__c Object(s) for %s()" % functionName()
            print >> sys.stderr, msg 
        else: 
            return ret[0]
        return None

    def getAccountById(self, id): 
        soql="Select a.Id, a.Name from Account a where a.Id='%s'" % id
        ret = self.query('Account', soql=soql)
        if ret in BAD_INFO_LIST:
            msg ="Could not find any Account Object(s) for %s()" % functionName()
            print >> sys.stderr, msg 
        else: 
            return ret[0]
        return None
    
    def getAccountParentByAccountId(self, id): 
        soql="Select a.Id, a.ParentId from Account a where a.Id='%s'" % id
        ret = self.query('Account', soql=soql)
        if ret in BAD_INFO_LIST:
            msg ="Could not find any Account Object(s) for %s()" % functionName()
            print >> sys.stderr, msg 
        else: 
            return ret[0]
        return None
    
    def getAccountsByParentId(self, id): 
        soql="Select a.Id, a.ParentId from Account a where a.ParentId='%s'" % id
        ret = self.query('Account', soql=soql)
        if ret in BAD_INFO_LIST:
            msg ="Could not find any Account Object(s) for %s()" % functionName()
            print >> sys.stderr, msg 
        else: 
            return ret
        return []
    
    def getAccountTreeById(self, id,partial=False):
        accts = []
        parent = self.getAccountParentByAccountId(id)
        if (parent) and (parent.has_key('Id')):
            accts.append(parent)
            if (not partial):
                p_id = parent['Id']
                for a in self.getAccountsByParentId(p_id):
                    accts.append(a)
        else:
            msg ="Could not find any Account Object(s) for %s()" % functionName()
            print >> sys.stderr, msg 
        return accts
    
    def getCRLinksById(self, id): 
        soql="Select c.Parent_CR__c from CR_Link__c c where c.Tech_Campaign__c='%s'" % id
        ret = self.query('CR_Link__c', soql=soql)
        if ret in BAD_INFO_LIST:
            msg ="Could not find any CR_Link__c Object(s) for %s()" % functionName()
            print >> sys.stderr, msg 
        else: 
            return ret
        return None

    def getCasesByTeamId(self, team_id, windowIsoDateTime): 
        soql="Select c.CaseNumber, c.Component__c, c.LastModifiedDate, c.Subject, c.OwnerId, c.Component_Link__c, c.Component_Link__r.Product_Team__c from Case c where c.Component_Link__r.Product_Team__c = %s and c.Status != 'Closed' and c.LastModifiedDate >= %s" % (team_id,windowIsoDateTime)
        ret = self.query('Case', soql=soql)
        if ret in BAD_INFO_LIST:
            msg ="Could not find any Case Object(s) for %s()" % functionName()
            print >> sys.stderr, msg 
        else: 
            return ret
        return []

    def getCasesByUserId(self, user_id, windowIsoDateTime): 
        soql="Select c.CaseNumber, c.Component__c, c.LastModifiedDate, c.Subject, c.OwnerId from Case c where c.OwnerId = '%s' and c.Status != 'Closed' and c.LastModifiedDate >= %s" % (user_id,windowIsoDateTime)
        ret = self.query('Case', soql=soql)
        if ret in BAD_INFO_LIST:
            msg ="Could not find any Case Object(s) for %s()" % functionName()
            print >> sys.stderr, msg 
        else: 
            return ret
        return []

    def getCasesByComponentName(self, cname, windowIsoDateTime): 
        soql="Select c.CaseNumber, c.Component__c, c.LastModifiedDate, c.Subject from Case c where c.Component__c = '%s' and c.Status != 'Closed' and c.LastModifiedDate >= %s" % (cname,windowIsoDateTime)
        ret = self.query('Case', soql=soql)
        if ret in BAD_INFO_LIST:
            msg ="Could not find any Case Object(s) for %s()" % functionName()
            print >> sys.stderr, msg 
        else: 
            return ret
        return []

    def getCasesByAccountId(self, id, windowIsoDateTime): 
        soql="Select c.CaseNumber, c.Component__c, c.LastModifiedDate, c.Subject from Case c where c.AccountId = '%s' and c.Status != 'Closed' and c.LastModifiedDate >= %s" % (id,windowIsoDateTime)
        ret = self.query('Case', soql=soql)
        if ret in BAD_INFO_LIST:
            msg ="Could not find any Case Object(s) for %s()" % functionName()
            print >> sys.stderr, msg 
        else: 
            return ret
        return []
    
    def getCaseById(self, id, windowIsoDateTime): 
        soql="Select c.CaseNumber, c.Component__c, c.LastModifiedDate, c.Subject from Case c where c.Id = '%s' and c.Status != 'Closed' and c.LastModifiedDate >= %s" % (id,windowIsoDateTime)
        ret = self.query('Case', soql=soql)
        if ret in BAD_INFO_LIST:
            msg ="Could not find any Case Object(s) for %s()" % functionName()
            print >> sys.stderr, msg 
        else: 
            return ret[0]
        return None

    def process(self): 
        windowIsoDateTime = self._getLastProcessDate()

        soql="Select c.Case_Watcher__c, c.Id, c.LastModifiedDate, c.Name, c.Alias_Email__c, c.Email__c from Case_Watcher_List__c c"
        ret = self.query('Case_Watcher_List__c', soql=soql)
        if ret in BAD_INFO_LIST:
            msg ="Could not find any Case_Watcher_List__c Object(s) for %s()" % functionName()
            print >> sys.stderr, msg 
        else:
            print 'Collecting my thoughts...'
            for ip in ret:
                _id = ip['Case_Watcher__c']
                if (not self.d_caseWatchers.has_key(_id)):
                    self.d_caseWatchers[_id] = [ip]
                else:
                    l = self.d_caseWatchers[_id]
                    l.append(ip)
                    self.d_caseWatchers[_id] = l
            for k,v in self.d_caseWatchers.iteritems():
                _cases = []
                print k
                cw = self.getCaseWatcherById(k)
                if (cw.has_key('Name')):
                    print >> _stdOut, 'Case Watcher Name: %s' % cw['Name']
                if (cw.has_key('Case_Fields__c')):
                    print >> _stdOut, 'Case Fields: %s' % cw['Case_Fields__c']
                if (cw.has_key('Component__c')):
                    comp_id = cw['Component__c']
                    comp = self.getComponentById(comp_id)
                    print >> _stdOut, 'Component: %s' % str(comp)
                    if (comp.has_key('Name')):
                        for c in self.getCasesByComponentName(comp['Name'], windowIsoDateTime):
                            _cases.append(c)
                if (cw.has_key('Team__c')):
                    team_id = cw['Team__c']
                    for c in self.getCasesByTeamId(team_id, windowIsoDateTime):
                        _cases.append(c)
                if (cw.has_key('User__c')):
                    user_id = cw['User__c']
                    for c in self.getCasesByUserId(user_id, windowIsoDateTime):
                        _cases.append(c)
                if (cw.has_key('Case_Number__c')):
                    _cr = self.getCaseById(cw['Case_Number__c'],windowIsoDateTime)
                    if (_cr):
                        _cases.append(_cr)
                        print >> _stdOut, '\tCR: %s' % str(_cr)
                if (cw.has_key('Case_Scope__c')):
                    caseScope = cw['Case_Scope__c']
                    print >> _stdOut, 'Case Scope: %s' % caseScope
                    if (cw.has_key('Account__c')):
                        acct_id = cw['Account__c']
                        acct = self.getAccountById(acct_id)
                        print >> _stdOut, 'Account: %s' % str(acct)
                        if (caseScope.lower() == 'account only'):
                            if (acct_id):
                                for c in self.getCasesByAccountId(acct_id, windowIsoDateTime):
                                    _cases.append(c)
                        else:
                            if (caseScope.lower() == 'whole account tree'):
                                acct_tree = self.getAccountTreeById(acct_id)
                            elif (caseScope.lower() == 'account and parents'):
                                acct_tree = self.getAccountTreeById(acct_id,partial=True)
                                acct_tree.append(acct)
                            print >> _stdOut, 'Account Tree: %s' % str(acct_tree)
                            if (acct_tree):
                                for a in acct_tree:
                                    for c in self.getCasesByAccountId(a[Id], windowIsoDateTime):
                                        _cases.append(c)
                if (cw.has_key('Tech_Campaign__c')):
                    crLinks = self.getCRLinksById(cw['Tech_Campaign__c'])
                    if (crLinks):
                        msg = 'Tech_Campaign:'
                        print msg
                        print >> _stdOut, msg
                        for cr in crLinks:
                            if (cr.has_key('Parent_CR__c')):
                                _cr = self.getCaseById(cr['Parent_CR__c'],windowIsoDateTime)
                                if (_cr):
                                    _cases.append(_cr)
                                    print >> _stdOut, '\tParent_CR: %s' % str(_cr)
                    else:
                        print >> _stdOut, '\tNo Cr_Link for "%s".' % cw['Tech_Campaign__c']
                print >> _stdOut, str(cw)
                for item in v:
                    if (item.has_key('Name')) and (item.has_key('Email__c')):
                        print >> _stdOut, '\tName: %s, Email: %s' % (item['Name'],item['Email__c'])
                if (_cases) and (len(_cases) > 0):
                    msg = 'Send Notification for this list (%s Cases) !' % len(_cases)
                    print >> _stdOut, '\n'+msg+'\n'
                    print msg
                print >> _stdOut, ''
                print
        return 
     
def main():
    n=CaseWatcherList() 
    n.process() 
 
if __name__ == "__main__": 
    _stdOut = open('stdout.txt','w')
    main() 
    _stdOut.flush()
    _stdOut.close()
    print 'Done !'
    
 
