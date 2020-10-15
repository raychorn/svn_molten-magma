#!/bin/env python2.3
"""
Collection of useful constants
"""

# SF Type constants and ID signatures
ACCOUNT_OBJ='Account'
ACCOUNT_SIG='001'

CONTACT_OBJ='Contact'
CONTACT_SIG='003'

LEAD_OBJ='Lead'
LEAD_SIG='00Q'

NOTE_OBJ='Note'
NOTE_SIG='002'

QUEUE_OBJ='Queue'
QUEUE_SIG='00G'

USER_OBJ='User'
USER_SIG='005'

CASE_OBJ='Case'
CASE_SIG='500'

CASE_HISTORY_OBJ='CaseHistory'

TASK_BRANCH_OBJ='Task_Branch__c'
TASK_BRANCH_SIG='a01'

TEAM_BRANCH_OBJ='Team_Branch__c'
TEAM_BRANCH_SIG='a0B'

BRANCH_CR_LINK_OBJ='Branch_CR_Link__c'

BRANCH_APPROVAL_OBJ='Branch_Approval__c'


#-----

# Record Types
RECTYPE_CR = '01230000000001YAAQ'
RECTYPE_PVCR = '0123000000003qfAAA'
RECTYPE_PLDCR = '0123000000003qfAAA'
RECTYPE_SC = '01230000000001XAAQ'
RECTYPE_PLDSC = '0123000000000DCAAY'

LEAD_OWNER_SIG=[USER_SIG, QUEUE_SIG]


BAD_INFO_LIST = [None, [], [{}], {}, '', 'fail', 'warn']


#----

LEGACY_STREAMS = ('3','3.0','3.1','3.2','4.0', '4.1', '4','5')

#ALL_STREAMS = ('3','3.0','3.1','3.2', 'blast4.0', 'blast4.1', 'blast4', 'blast5', 'capi1')
ALL_STREAMS = ('3','3.0','3.1','3.2', '4.0', '4.1', '4', 'blast5', 'talus1.0', 'qf2','mcapi1')

#ACTIVE_STREAMS = ('blast4.0', 'blast4.1', 'blast4', 'blast5', 'capi1')
ACTIVE_STREAMS = ('blast5', 'talus1.0', 'qf2','mcapi1')

#DEFAULT_STREAM = 'blast4'
DEFAULT_STREAM = ''
