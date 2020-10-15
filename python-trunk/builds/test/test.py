#!/usr/local/bin/python
#
sfUrl = 'https://na1.salesforce.com'
try: 
    from sfMagma import *
except:
    print 'Couldnt import sfMagma'

class Test(SFMagmaTool):
    logname = 'Test'

    def getUserChangeObjects(self):
        soql="Select Id, FirstName,LastName from User  where LastName ='Dragojevic'"
        ret=self.query('User', soql=soql)
        print "VALUE OF Query: %s" %ret 
        for rt in ret:
            fn = rt.get('FirstName')
        print fn
        return
def main():    
    n=Test()
    n.getUserChangeObjects()

if __name__ == "__main__":
    main()
    