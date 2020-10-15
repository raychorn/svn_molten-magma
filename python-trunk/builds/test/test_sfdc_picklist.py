#!/usr/local/bin/python
#    
# import Magma SFDC API and login to SFDC
try: 
    from sfMagma import *
except:
    print '--- ERROR:Couldnt import sfMagma'
    sys.exit()

class Test(SFMagmaTool):
    logname = 'Test'

############################################################################################
def main():    
    print "====================> Started processing at: ", time.ctime()
    h = Test()
#    em = h.getEntityMap('Task_Branch__c')
    plv = h.getPicklist('Task_Branch__c', 'Branch_Status__c')
    #em = h.SFEntitiesMixin.getEntityMapFromSF('Task_Branch__c')
    #print em
#    emfi = em.get('fieldInfo')
    #print emf
#    emf = emfi.get('Branch_Status__c')
    #print emf1
#    plv = emf.get('picklistValues')
    print plv
    print "====================> End processing at: ", time.ctime()
# end of main

if __name__ == "__main__":
    main()
