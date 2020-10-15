    ##################################################################################################
    #   Overall Status control mapping for Branch Approvals
    ##################################################################################################
class TaskBranchStatusMap:
    """ simple object to hold Status map dictionary until it can migrate to a server process
    """
    
    def getStatusMap(self):
        """ get a ordered list of possible MOD statuses """
        #if hasattr(self, 'statMap'): return self.statMap
        statMap = {}
        # coordinate these arcs with the endpoints defined below
        statMap['EngMgr_Action']        = {'approve':35.0, 'reject':30.0, 'cancel':2.0}
        statMap['ProdEng_Action']       = {'approve':36.0, 'reject':30.0, 'cancel':2.0}
        statMap['Pending_Approvals']    = {'approve':40.0, 'reject':36.0, 'cancel':2.0}
        statMap['SubmitToSCMAction']    = {'approve':42.0, 'reject':40.0, 'cancel':2.0}
        statMap['SCM_Action']           = {'approve':52.5, 'reject':43.0, 'cancel':2.0}
        statMap['SCM_RedBuildAction']   = {'approve':60.0, 'reject':54.0, 'cancel':2.0}
        statMap['OriginatorAction']     = {'approve':71.0, 'reject':74.0, 'cancel':2.0}
        
        # status endpoints defined by the order number, the CR status, and role
        # valid roles are ['dev','mgr','pe','scm','ae','admin']  AE means CR originator
        statMap['New']                          = {'order':1.0,  'role':'dev', 'crStatus':'Open', 'crStatusFirst':'Open'}
        statMap['Open']                         = {'order':2.0,  'role':'dev', 'crStatus':'Open', 'crStatusFirst':'Open'}
        statMap['Not Started']                  = {'order':3.0,  'role':'dev', 'crStatus':'Open', 'crStatusFirst':'Open'}
        statMap['Qualifying']                   = {'order':4.0,  'role':'dev', 'crStatus':'Open', 'crStatusFirst':'Open'}
        statMap['Confirming']                   = {'order':5.0,  'role':'dev', 'crStatus':'Open', 'crStatusFirst':'Open'}
        statMap['Pending Complete Test Case']   = {'order':10.0, 'role':'dev', 'crStatus':'Open', 'crStatusFirst':'Open'}
        statMap['Requested - Not Scheduled']    = {'order':11.0, 'role':'dev', 'crStatus':'Open', 'crStatusFirst':'Open'}
        statMap['Scheduled - Not Started']      = {'order':12.0, 'role':'dev', 'crStatus':'Open', 'crStatusFirst':'Open'}
        statMap['Verifying No Need']            = {'order':13.0, 'role':'dev', 'crStatus':'Open', 'crStatusFirst':'Open'}
        statMap['On Hold']                      = {'order':14.0, 'role':'dev', 'crStatus':'Open', 'crStatusFirst':'Open'}
        statMap['Can Not Reproduce']            = {'order':15.0, 'role':'dev', 'crStatus':'Open', 'crStatusFirst':'Open'}
        statMap['Awaiting Cust. Info']          = {'order':16.0, 'role':'dev', 'crStatus':'Open', 'crStatusFirst':'Open'}
        statMap['Awaiting R&D Input']           = {'order':17.0, 'role':'dev', 'crStatus':'Open', 'crStatusFirst':'Open'}
        statMap['Awaiting AE Input']            = {'order':18.0, 'role':'dev', 'crStatus':'Open', 'crStatusFirst':'Open'}
        statMap['In Process']                   = {'order':19.0, 'role':'dev', 'crStatus':'Open', 'crStatusFirst':'Open'}
        # leave room for at least 10 more here
        statMap['Fixing']                       = {'order':30.0, 'role':'dev', 'crStatus':'Fixing', 'crStatusFirst':'Fixing'}
        statMap['Rejecting']                    = {'order':32.0, 'role':'dev', 'crStatus':'Fixing', 'crStatusFirst':'Fixing'}
        statMap['Rejected by Mgr']              = {'order':32.1, 'role':'dev', 'crStatus':'Fixing', 'crStatusFirst':'Fixing'}
        statMap['Rejected by PE']               = {'order':32.2, 'role':'dev', 'crStatus':'Fixing', 'crStatusFirst':'Fixing'}
        statMap['Rejected by Partition Reviewer'] = {'order':32.3, 'role':'dev', 'crStatus':'Fixing', 'crStatusFirst':'Fixing'}
        statMap['Rejected by SCM'] = {'order':32.4, 'role':'dev', 'crStatus':'Fixing', 'crStatusFirst':'Fixing'}
        statMap['Submitted']                    = {'order':33.0, 'role':'dev', 'crStatus':'Fixing', 'crStatusFirst':'Fixing'}

        statMap['Approving by Partition Reviewer']         = {'order':33.5, 'role':'part', 'crStatus':'Approving', 'crStatusFirst':'Fixing'}
        statMap['Approved by Partition Reviewer']          = {'order':33.7, 'role':'part', 'crStatus':'Approving', 'crStatusFirst':'Fixing'}

        statMap['Approving by Manager']         = {'order':34.0, 'role':'mgr', 'crStatus':'Approving', 'crStatusFirst':'Fixing'}
        statMap['Approved by Manager']          = {'order':34.2, 'role':'mgr', 'crStatus':'Approving', 'crStatusFirst':'Fixing'}
        statMap['Approving by PE']              = {'order':35.0, 'role':'pe',  'crStatus':'Approving', 'crStatusFirst':'Fixing'}
        statMap['Approved by PE']               = {'order':35.2, 'role':'pe',  'crStatus':'Approving', 'crStatusFirst':'Fixing'}
        statMap['Approved, pending Branch']     = {'order':36.0, 'role':'dev', 'crStatus':'Approved', 'crStatusFirst':'First-Approved'}

        statMap['Approved, pending Team Branch']= {'order':36.5, 'role':'dev', 'crStatus':'Approved', 'crStatusFirst':'First-Approved'}

        statMap['Awaiting Branches']            = {'order':37.0, 'role':'team', 'crStatus':'Awaiting Branches', 'crStatusFirst':'First-Awaiting Branches'}
        statMap['Submitted to Team Testing']    = {'order':37.5, 'role':'team', 'crStatus':'Team-Testing', 'crStatusFirst':'First-Team'}
        
        statMap['Team Branch Hold']             = {'order':38.0, 'role':'team', 'crStatus':'Team Hold', 'crStatusFirst':'First-Team Hold'}
        statMap['Team-Building-Testing']        = {'order':38.2, 'role':'team', 'crStatus':'Team-Testing', 'crStatusFirst':'First-Team Testing'}
        statMap['Team Testing Done']            = {'order':38.4, 'role':'team', 'crStatus':'Team-Done', 'crStatusFirst':'First-Team Done'}
        statMap['Team-Approving']               = {'order':41.8, 'role':'team', 'crStatus':'Team-Approving', 'crStatusFirst':'First-Team-Approving'}
        statMap['Team-Approved']                = {'order':42.0, 'role':'team', 'crStatus':'Team-Approved', 'crStatusFirst':'First-Team-Approved'}
        statMap['Team Testing']                 = {'order':38.4, 'role':'team', 'crStatus':'Team-Testing', 'crStatusFirst':'First-Team Testing'}


        statMap['Submitted to SCM']     = {'order':44.0, 'role':'scm', 'crStatus':'Approved', 'crStatusFirst':'First-Approved'}
        statMap['SCM-Submitted']        = {'order':44.5, 'role':'dev', 'crStatus':'Approved', 'crStatusFirst':'First-Approved'}
        statMap['SCM-Received']         = {'order':45.0, 'role':'dev', 'crStatus':'SCM-Received', 'crStatusFirst':'First-SCM-Received'}

        statMap['SCM-Need Branch']      = {'order':46.2, 'role':'dev', 'crStatus':'SCM-Hold', 'crStatusFirst':'First-SCM-Hold'}
        
        statMap['SCM-QOR Building']     = {'order':47.2, 'role':'dev', 'crStatus':'SCM-Merging', 'crStatusFirst':'First-SCM-Merging'}
        statMap['SCM-QOR Testing']      = {'order':47.3, 'role':'dev', 'crStatus':'SCM-Merging', 'crStatusFirst':'First-SCM-Merging'}
        statMap['SCM-QOR Results']      = {'order':47.4, 'role':'dev', 'crStatus':'SCM-Merging', 'crStatusFirst':'First-SCM-Merging'}

        statMap['SCM-Hold']             = {'order':47.8, 'role':'dev', 'crStatus':'SCM-Hold', 'crStatusFirst':'First-SCM-Hold'}
        statMap['post_release']         = {'order':47.9, 'role':'dev', 'crStatus':'SCM-Hold', 'crStatusFirst':'First-SCM-Hold'}
        statMap['SCM-Post-Release']     = {'order':47.9, 'role':'dev', 'crStatus':'SCM-Hold', 'crStatusFirst':'First-SCM-Hold'}
        
        statMap['SCM-Ready to Bundle']  = {'order':48.0, 'role':'dev', 'crStatus':'SCM-Merging', 'crStatusFirst':'First-SCM-Merging'}
        statMap['SCM-Bundle Building']  = {'order':48.2, 'role':'dev', 'crStatus':'SCM-Merging', 'crStatusFirst':'First-SCM-Merging'}
        statMap['SCM-Bundle Testing']   = {'order':48.4, 'role':'dev', 'crStatus':'SCM-Merging', 'crStatusFirst':'First-SCM-Merging'}
        statMap['SCM-Bundle Results']   = {'order':48.8, 'role':'dev', 'crStatus':'SCM-Merging', 'crStatusFirst':'First-SCM-Merging'}
        
        statMap['SCM-Approved']           = {'order':49.0, 'role':'dev', 'crStatus':'SCM-Merging', 'crStatusFirst':'First-SCM-Merging'}
        
        statMap['SCM-Patch-Build-Delayed']= {'order':49.1, 'role':'dev', 'crStatus':'SCM-Merging', 'crStatusFirst':'First-SCM-Merging'}
        
        statMap['SCM-Patch-Building']     = {'order':52.0, 'role':'dev', 'crStatus':'SCM-Merging', 'crStatusFirst':'First-SCM-Merging'}
        statMap['SCM-Patch-Build Testing']= {'order':52.4, 'role':'dev', 'crStatus':'SCM-Merging', 'crStatusFirst':'First-SCM-Merging'}
        statMap['SCM-Patch-Build Results']= {'order':52.8, 'role':'dev', 'crStatus':'SCM-Merging', 'crStatusFirst':'First-SCM-Merging'}
        statMap['SCM-Red-Building']       = {'order':52.6, 'role':'dev', 'crStatus':'SCM-Merging', 'crStatusFirst':'First-SCM-Merging'}        
        statMap['SCM-Red-Build Results']  = {'order':52.8, 'role':'dev', 'crStatus':'SCM-Merging', 'crStatusFirst':'First-SCM-Merging'}
        statMap['SCM-Candidate-Building']     = {'order':52.0, 'role':'dev', 'crStatus':'SCM-Merging', 'crStatusFirst':'First-SCM-Merging'}
        statMap['SCM-Candidate-Build Testing']= {'order':52.4, 'role':'dev', 'crStatus':'SCM-Merging', 'crStatusFirst':'First-SCM-Merging'}
        statMap['SCM-Candidate-Build Results']= {'order':52.8, 'role':'dev', 'crStatus':'SCM-Merging', 'crStatusFirst':'First-SCM-Merging'}


        statMap['SCM-Patch-Build Today']    = {'order':52.9, 'role':'dev', 'crStatus':'SCM-Merging', 'crStatusFirst':'First-SCM-Merging'}
        statMap['SCM-Ready-for-Patch-Build']= {'order':52.9, 'role':'dev', 'crStatus':'SCM-Merging', 'crStatusFirst':'First-SCM-Merging'}
        statMap['SCM-Red-Build Today']      = {'order':52.9, 'role':'dev', 'crStatus':'SCM-Merging', 'crStatusFirst':'First-SCM-Merging'}
        
        statMap['Merged - Notifying Originator']  = {'order':54.0, 'role':'ae', 'crStatus':'Testing', 'crStatusFirst':'First-Testing'}
        statMap['Merged - Testing by Originator'] = {'order':54.5, 'role':'ae', 'crStatus':'Testing', 'crStatusFirst':'First-Testing'}
        statMap['Merged']                         = {'order':54.5, 'role':'ae', 'crStatus':'Testing', 'crStatusFirst':'First-Testing'}
        statMap['Merged - Tested by Originator']  = {'order':55.0, 'role':'ae', 'crStatus':'Testing', 'crStatusFirst':'First-Testing'}
        
        statMap['Closed']               = {'order':70.0, 'role':'dev', 'crStatus':'Closed', 'crStatusFirst':'Closed'}
        statMap['Closed - Passed']      = {'order':71.0, 'role':'dev', 'crStatus':'Closed', 'crStatusFirst':'Closed'}
        statMap['Closed - Automatic']   = {'order':72.0, 'role':'dev', 'crStatus':'Closed', 'crStatusFirst':'Closed'}
        statMap['Closed - Incomplete']  = {'order':73.0, 'role':'dev', 'crStatus':'Testing Fail', 'crStatusFirst':'Testing Fail'}
        statMap['Closed - Failed']      = {'order':74.0, 'role':'dev', 'crStatus':'Testing Fail', 'crStatusFirst':'Testing Fail'}
        self.statMap = statMap
        return self.statMap
