

sfUrl = 'https://na1.salesforce.com'

import pprint
import sys
import textwrap
from optparse import OptionParser
import datetime
from sfMagma import *
from sfConstant import *
from sfUtil import *

class Test(SFMagmaTool):
    logname = 'Test'
    
    
    def getUserChangeObjects(self):
        
        soql="Select Id, FirstName,LastName from User  where LastName ='magma'"
        ret=self.describeSObject('MoltenPost__c')
        
        
        #ret=self.query('User', soql=soql)
        print "VALUE OF Query: %s" %ret     
        return
    
    
    def isTime(self):
        tmp_root = '/home/ramya/sfsrc/sfapi2/tmp'
        filename='DateOfLastCustomNotication'  
        checksince=None
        isTime=False              
        curDirPath = os.getcwd()
        tmpDirPath = tmp_root    
        os.chdir(tmpDirPath)       
        
        #os.system('umask 000')
        tmpPath = os.path.join(tmp_root,filename)
        if os.path.isfile(tmpPath):
            #ph = os.popen(filename)
            curFile=open(tmpPath, "rb", 0)
            for line in curFile.readlines():
                print "Lines read from  file: %s" %line
                checksince=line                
                continue
            curFile.close()
            #os.system('umask %s' %saveUmask)                  
            os.remove(filename)            
        
        #os.cat(filename)    
        try:
            #open file stream
            secsAgo=60*60*24
            print "CHECK SINCE %s" %checksince
            newfilename=os.path.join(tmp_root,filename)
            file = open(newfilename, 'a')
            fromSecs = time.time()-secsAgo
            print" Current day: %s" %fromSecs
            now = datetime.date.today()
            print "NEW Current Time .....%s" %now
            
            """fromSecs = datetime.datetime.fromtimestamp(fromSecs)
            diff = datetime.timedelta(days=-1)
            previousDay=fromSecs - diff
            print "PREVIOUS DAY .............%s" %previousDay
            currentDate=time.mktime(fromSecs.timetuple())
            #print "Previous date: %s" %previousDay  
            #previousDay=time.mktime(previousDay.timetuple())  
            print "Current day: %s"%currentDate      
            dateStr = self.getAsDateTimeStr(currentDate)"""
            #print"date time str %s"%(datetime.date(checksince[0:3], checksince[5:6],checksince[8:9]))
            if checksince not in [None,"",'']:
                lastTime=time.mktime(time.strptime(checksince,"%Y-%m-%d"))
                print lastTime
                epc = datetime.date.fromtimestamp(lastTime)
                print "EPC %s" %epc
                parseEpc = epc.strftime("%Y-%m-%d")
                print "Parse Epc %s" %parseEpc
                dif=(epc-now)
                print "Diff.......%s" %dif                                
                if dif.days < 0:
                    print "ISTIME"
                    
                
            #print "NEW Diffrenct %s" %(datetime.date(checksince[0:3], checksince[5:6],checksince[:]) - datetime.date(2000, 8, 6))
            dateStr = now.strftime("%Y-%m-%d")
            dateStr="2006-04-02"
            print "Current formated date: %s"%dateStr   
            
            #print "Difference: %s"%(checksince-dateStr) 

            file.write(dateStr)
            #file.write("\n")
            file.close()
        except IOError:
            print "There was an error writing to", filename
            pass
        os.chdir(curDirPath)       
                              
        return  isTime   
           
        
    
def main():    
    n=Test()
    n.getUserChangeObjects()
    n.isTime()
    

if __name__ == "__main__":
    main()
    