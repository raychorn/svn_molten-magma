#!/usr/bin/env python2.3
"""
Class and script to help clean up leads and contacts which bounce or
opt out of bulk email. 
"""

#version = 1.0  # Mar 16, 2004. First reworked version using only 2.0 API
version = 1.5  # Oct 25, 2004. Modified flow and treatment of hard bounces


import string, re, getpass, socket, time, pprint
import ConfigHelper
import cStringIO as StringIO

try:
    from sforceBase import *	    	    
except:
    print 'Please ensure that the "sforceXMLRPC.py[co]" file is in your'
    print 'PYTHONPATH environment variable list.'



### Global definitions ###
contactType = "contact"
leadType = "lead"

ContactStatus = '00N30000000cD2i'
### END Global definitions ###

class ManageEmailList(SalesForceBase):
    """
    This class creates an object for the specified case which
    presents certain case information and contains methods for
    inserting, updating, adding a task, or attaching to this case
    in the SalesForce.com database.
    """

    logName = "sf.maillist"

    def __init__(self, props):
        SalesForceBase.__init__(self, logname=self.logName)
        self.props = props
        self.setAction('update')
    ## END __init__(self)
    

    def getContactsByEmail(self, email):
        """
        Given an email address, query all contacts with a matching email.
        Just get contact ID for now.
        """
        # text field query is naturally case-insensitive
        f1 = {'field': 'email',
              'operator': 'equals',
              'value': email}

        qryF = [f1]

        retFldList = ['id', ContactStatus, 'firstName', 'lastName',
                      'description', 'email']
        contactResponse = self.getSFInfo(contactType, qryF, retFldList)

        if contactResponse is None:
            contactResponse = []

        return contactResponse
    ## END getContactsByEmail

    def getLeadsByEmail(self, email):
        """
        Given an email address, query all unconverted leads with a
        matching email. Just get lead ID for now.
        """
        # text field query is naturally case-insensitive
        f1 = {'field': 'email',
              'operator': 'equals',
              'value': email}
        f2 = {'field': 'converted',
              'operator': 'equals',
              'value': False}

        qryF = [f1, f2]

        retFldList = ['id', 'firstName', 'lastName', 'description',
                      'emailOptOut']
        leadResponse = self.getSFInfo(leadType, qryF, retFldList)

        if leadResponse is None:
            leadResponse = []

        return leadResponse
    ## END getLeadsByEmail

    def hardbounceFlow(self, emailListPath):
        """
        Remove email address from lead and contact records where
        email is reported as a hard bounce
        """
        # open the email list and loop over it
        elf = file(emailListPath, 'r')
        
        datestr = time.strftime('%m/%d/%Y')
        
        for email in elf.readlines():
            email = email.strip()
            print "Processing email: %s" %email
            # look up contact(s) with given email
            contacts = self.getContactsByEmail(email)

            # set each contact email fields accordingly
            for contact in contacts:
                newdescr = "%s: Contact marked inactive due to hard email bounce.\n\n%s" %(datestr, contact.get('description',''))
                contactUpdMap = {'id': contact['id'],
                                 'email': '',
                                 'firstName': contact.get('firstName','')+'-x',
                                 'lastName': contact['lastName']+'-x',
                                 'description': newdescr,
                                 'emailOptOut': True,
                                 ContactStatus: 'Inactive',}
                try:
                    self.setSFInfo(contactUpdMap, contactType)
                except Exception, e:
                    print "An error occurred while updating contact %s having email %s:\n%s" %(lead['id'], email, e)

            # look up lead(s) with given email
            leads = self.getLeadsByEmail(email)

            # set each lead email fields accordingly
            for lead in leads:
                # attempt to delete lead first.
                ret = self.delSFID(lead['id'], leadType)
                if ret is not None:
                    # delete succeeded. Continue with next lead found
                    continue
                
                # couldn't delete, so neuter the lead record
                newdescr = "%s: Lead marked inactive due to hard email bounce.\n\n%s" %(datestr, lead.get('description',''))
                
                leadUpdMap = {'id': lead['id'],
                              'firstName': lead.get('firstName','')+'-x',
                              'lastName': lead['lastName']+'-x',
                              'email': '',
                              'description': newdescr,
                              'emailOptOut': True,}
                try:
                    self.setSFInfo(leadUpdMap, leadType)
                except Exception, e:
                    print "An error occurred while updating lead %s having email %s:\n%s" %(lead['id'], email, e)
                
    ## END hardbounceFlow

    def optoutFlow(self, emailListPath):
        """
        Mark all leads and contacts matching email addresses in list
        to have Email Opt Out set.
        """
        # open the email list and loop over it
        elf = file(emailListPath, 'r')
        
        for email in elf.readlines():
            email = email.strip()
            print "Processing email: %s" %email
            # look up contact(s) with given email
            contacts = self.getContactsByEmail(email)

            # set each contact email fields accordingly
            for contact in contacts:
                contactUpdMap = {'id': contact['id'],
                                 'emailOptOut': True} 
                try:
                    self.setSFInfo(contactUpdMap, contactType)
                except Exception, e:
                    print "An error occurred while updating contact %s having email %s:\n%s" %(lead['id'], email, e)

            # look up lead(s) with given email
            leads = self.getLeadsByEmail(email)

            # set each contact email fields accordingly
            for lead in leads:
                leadUpdMap = {'id': lead['id'],
                              'emailOptOut': True}
                try:
                    self.setSFInfo(leadUpdMap, leadType)
                except Exception, e:
                    print "An error occurred while updating lead %s having email %s:\n%s" %(lead['id'], email, e)
    ## END optoutFlow
## END class ManageEmailList

def hardbounce_main(args):
    # Fetch the config
    props = ConfigHelper.fetchConfig('conf/sfutil.cfg')

    if len(args):
        emailListPath = args[0]
    else:
        print "You must provide the path to the list of emails to use"
        sys.exit(1)

    mel = ManageEmailList(props)
    mel.hardbounceFlow(emailListPath)
## END hardbounce_main()
    
def optout_main(args):
    # Fetch the config
    props = ConfigHelper.fetchConfig('conf/sfutil.cfg')

    if len(args):
        emailListPath = args[0]
    else:
        print "You must provide the path to the list of emails to use"
        sys.exit(1)

    mel = ManageEmailList(props)
    mel.optoutFlow(emailListPath)
## END optout_main()    


if __name__=='__main__':
    scriptname = sys.argv[0]
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        args = sys.argv[2:]
    else:
        mode = 0
    
    if mode == "optout":
        optout_main(args)
    elif mode == "hardbounce":
        hardbounce_main(args)
    else:
        print "specify either optout or hardbounce operation"

        
