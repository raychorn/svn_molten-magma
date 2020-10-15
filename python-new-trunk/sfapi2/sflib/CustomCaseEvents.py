"""
Actual events to poll for and operate upon
Sacns for events specified in the Interested Party Notification Object
"""
import copy
import datetime
import time
import pprint
import textwrap
import sys
from optparse import OptionParser

from CustomNotificationEventHandler import CustomNotificationEventHandler
from sfConstant import *
from sfTaskBranch import SFTaskBranch, SFTaskBranchTool
from MailNotification import MailNotification, WW
from MailMessageQueue import MailMessageQueue
from TimeUtil import parseSfIsoStr, dayNumToTxt
from sfUtil import convertId15ToId18
from sfMagma import *
from sfUtil import *

testMailAddr = 'ramya@molten-magma.com'
WW = 72
myTZ = 'US/Pacific'
dateTimeFmt = "%Y-%m-%dT%H:%M:%S.000Z"

class CustomCaseEvents(CustomNotificationEventHandler):
    """ Common bits for Approval Action events.
    An approval action is when a branch approval has been approved or rejected
    """
    role = None # must be provided by implementation
    notifyRoles = None # must be provided by implementation
    staticRecipients = None  
    eObj=None   
    
     
    
    def getCaseDescribeObject(self):        
    
        eObj=self.sfb.describeSObject('Case') 
        data={}
        for f in eObj._fields:                      
            label=  f._label       
            name = f._name                  
            data[label]=name
            pass          
        return data
    

    def poll(self):        
        rawEventList = []        
        rawEventList=self.getNotificationObject()
        
        self.rawEventList = rawEventList         
       
        return ## END poll"""
    
    
    """def getLastProcessDate(self):
        
        delta = datetime.timedelta(days=self.windowDays)
        
        dt = datetime.datetime.utcfromtimestamp(time.time())
        windowDateTime = dt - delta
        windowIsoDateTime = "%sZ" %windowDateTime.isoformat()            
        
        return windowIsoDateTime"""
    
    def getLastProcessDate(self):
        tmp_root = '/home/sfscript/tmp/processDates'
        #tmp_root = '/home/sfbeta/tmp/processDates'
        #tmp_root ='/home/ramya/sfsrc/sfapi2/tmp'
        filename='LastCaseWatcherProcessedDate'  
        checksince=None
                      
        curDirPath = os.getcwd()
        tmpDirPath = tmp_root    
        os.chdir(tmpDirPath)       
        
        #os.system('umask 000')
        tmpPath = os.path.join(tmp_root,filename)
        if os.path.isfile(tmpPath):
            #ph = os.popen(filename)
            curFile=open(tmpPath, "rb", 0)
            for line in curFile.readlines():
                #print "Lines read from  file: %s" %line
                checksince=line                
                continue
            curFile.close()
            #os.system('umask %s' %saveUmask)                                     
        
        #os.cat(filename)           
        
        if checksince in [None,'',""]:
            fromSecs = time.time()
            fromSecs = datetime.datetime.fromtimestamp(fromSecs)
            diff = datetime.timedelta(minutes=-15)
            previousHour=fromSecs + diff            
            previousHour=time.mktime(previousHour.timetuple())                    
            preHourStr = self.sfb.getAsDateTimeStr(previousHour)              
            checksince=preHourStr
        
        #checksince="2006-03-01T23:01:48.000Z"
            
        os.chdir(curDirPath)        
                              
        return  checksince
    
    def updateLastProcessDate(self):        
        tmp_root = '/home/sfscript/tmp/processDates'
        #tmp_root = '/home/sfbeta/tmp/processDates'
        #tmp_root ='/home/sfbeta/sfsrc/sfapi2/tmp'
        filename='LastCaseWatcherProcessedDate'  
        checksince=None
        filePresent=True
                      
        curDirPath = os.getcwd()
        tmpDirPath = tmp_root    
        os.chdir(tmpDirPath)       
        
        #os.system('umask 000')
        tmpPath = os.path.join(tmp_root,filename)
         
        try:
            #open file stream
            #secsAgo=60*60*24
            try:
                os.remove(filename)                
            except:                                                
                newfilename=os.path.join(tmp_root,filename)
                file = open(newfilename, 'a')
                #fromSecs = time.time()-secsAgo                       
                fromSecs = time.time()
                fromSecs = datetime.datetime.fromtimestamp(fromSecs)
                #diff = datetime.timedelta(days=-1)
                #previousDay=fromSecs + diff
                #print "Previous date: %s" %previousDay  
                currentDay=time.mktime(fromSecs.timetuple())                  
                dateStr = self.sfb.getAsDateTimeStr(currentDay)    
    
                file.write(dateStr)
                filePresent=False
                #file.write("\n")
                file.close()
                pass
            if filePresent is True:
                newfilename=os.path.join(tmp_root,filename)
                file = open(newfilename, 'a')
                #fromSecs = time.time()-secsAgo                       
                fromSecs = time.time()
                fromSecs = datetime.datetime.fromtimestamp(fromSecs)
                #diff = datetime.timedelta(days=-1)
                #previousDay=fromSecs + diff
                #print "Previous date: %s" %previousDay  
                currentDay=time.mktime(fromSecs.timetuple())                  
                dateStr = self.sfb.getAsDateTimeStr(currentDay)    
    
                file.write(dateStr)
                #file.write("\n")
                file.close()
        except IOError:
            msg= "There was an error writing to %s" %filename
            self.sfb.setLog(msg)
            pass     
            
        os.chdir(curDirPath)     
        
        return          
    
    
    
    def getNotificationObject(self):        
        rawEventList=[]
        sts = self.sfb.getServerTimestamp()
        currentSfDatetime = datetime.datetime(sts[0], sts[1], sts[2], sts[3], sts[4],
                                              sts[5], sts[6])
        cDesObj=self.getCaseDescribeObject()        
        fields = ('Id', 'Case_Fields_Deferred__c','Case_Number__c', 'Component__c', 'Account__c','Tech_Campaign__c', 'User__c','Case_Fields__c','LastModifiedDate', 'Name', 'Team__c')
        where = [['Id','!=',None]]
        #where = [['Name','=','Watcher 00089']]

        res = self.sfb.query('Case_Watcher__c', where, fields)
        if res in BAD_INFO_LIST:
            res = []
            pass       

        for nt in res:   
            mailEvents=[]         
            nid=nt.get('Id')
            watcherName=nt.get('Name')
            caseId=nt.get('Case_Number__c')
            compId=nt.get('Component__c')
            crFld=nt.get('Case_Fields__c')
            crDefFld=nt.get('Case_Fields_Deferred__c')
            techCmpId=nt.get('Tech_Campaign__c')
            usrId=nt.get('User__c')
            tmId=nt.get('Team__c')     
            acctId=nt.get('Account__c')                 
            if caseId is not None:
                caseSub=self.getCRFlds(caseId, crFld,crDefFld,cDesObj)
                #print "CR LENGHT: %s" %(len(caseSub))
                for cs in caseSub:
                    mailEvents.append(cs)                                  
                pass 
            
            if compId is not None:
                caseSub=self.getCompFlds(compId, crFld,crDefFld,cDesObj) 
                #print "COMP LENGHT: %s" %(len(caseSub))
                for cs in caseSub:
                    mailEvents.append(cs)                 
                pass
            
            if tmId is not None:
                caseSub=self.getTeamFlds(tmId, crFld,crDefFld,cDesObj)  
                #print "TEAM BRANCH LENGHT: %s" %(len(caseSub)) 
                for cs in caseSub:
                    mailEvents.append(cs)                
                pass   
                              
            if techCmpId is not None:
                caseSub=self.getTechCmpFlds(techCmpId, crFld,crDefFld,cDesObj)               
                for cs in caseSub:
                    mailEvents.append(cs)              
               
            if usrId is not None:
                caseSub=self.getUsrFlds(usrId, crFld,crDefFld,cDesObj)                  
                for cs in caseSub:
                    mailEvents.append(cs)           
                pass
            
            if acctId is not None:
                caseSub=self.getAccountFlds(acctId, crFld,crDefFld,cDesObj)   
                if caseSub not in [None,'']:
                    for cs in caseSub:
                        mailEvents.append(cs)           
                        pass
            
            if mailEvents not in [None, [], [{}], {}, '']:                
                distinctEvent=[]                
                for mv in mailEvents:
                    dupId=False
                    newId=mv.get('CaseId')
                    for disEv in distinctEvent:
                        disId=disEv.get('CaseId')
                        if disId==newId:
                            dupId=True
                            pass
                    if dupId is False:
                        distinctEvent.append(mv)
                    pass             
                    
                rawEvnt=self.mailFormat(distinctEvent, nid,watcherName)                
                for rv in rawEvnt:
                    rawEventList.append(rv)
                    pass
                pass
            pass  
        
        self.updateLastProcessDate()
        #print "rawEventList ........................... %s" %rawEventList
            
        return rawEventList
    
    
    def crNotificationList(self,ipId):  
        email=[]                      
        soql="Select Email__c, Id, Alias_Email__c ,Case_Watcher__c, Contact__c ,Name from Case_Watcher_List__c   where Case_Watcher__c= '%s'" %ipId
        fields=('Email__c', 'Id', 'Case_Watcher__c', 'Name')
        where=[['Case_Watcher__c','=','ipId']]       
        ret = self.sfb.query('Case_Watcher_List__c', soql=soql)
        if ret in BAD_INFO_LIST:                        
            msg="No Email address for the record"
            #print msg
            self.sfb.setLog(msg)                      
        else:            
            for ip in ret:                
                emailAdd=ip.get('Email__c') 
                isAlias=ip.get('Alias_Email__c') 
                contId=ip.get('Contact__c')               
                contMap={'Email':emailAdd,'ContactId':contId,'Alias_Email__c':isAlias}            
                email.append(contMap)
            pass
                
        return email
    
      
    
    """def getCaseFields(self,caseId, crFld,cObj,nid):
        data=[]
        emailToBeSent=self.crNotificationList(nid)        
        caseSub=self.getCRFlds(caseId, crFld,cObj)
        if caseSub is not None: 
            caseObj=caseSub[0]           
            for em in emailToBeSent:
                rawData={}
                email=em.get('Email')
                contId=em.get('ContactId')                
                chDt=caseObj.get('createdDate')
                chMsg=caseObj.get('subMg')
                rawData['TargetEmail']=email
                rawData['HistoryDate']=chDt
                rawData['Subject']=chMsg
                rawData['TargetId']=contId
                data.append(rawData)              
                pass                
            pass # outside if                
        return data"""
    
        
    def mailFormat(self,caseSub, nid,watcherName):   
        rawEvnt=[]     
        sts = self.sfb.getServerTimestamp()
        currentSfDatetime = datetime.datetime(sts[0], sts[1], sts[2], sts[3], sts[4],
                                              sts[5], sts[6])
        emailToBeSent=self.crNotificationList(nid)                
        if caseSub is not None: 
            for caseObj in caseSub:                     
                for em in emailToBeSent:
                    rawData={}
                    
                    email=em.get('Email')
                    contId=em.get('ContactId')
                    isEAlias=em.get('Alias_Email__c')                    
                    if isEAlias in ['Yes','None']:
                        contId='0033000000HPwQR'                                           
                    if contId is None:
                        contId='0033000000HPwQR' #satic salesforce contact if the target Id is none                                    
                    chDt=caseObj.get('createdDate')
                    triggerObjDatetime = parseSfIsoStr(chDt)
                    chMsg=caseObj.get('subMg')     
                    caseId=caseObj.get('CaseId')   
                    chDefMsg=caseObj.get('subMgDef') 
                    crNumber=caseObj.get('CaseNo')     
                    csSubject=caseObj.get('CaseSubject')                     
                    csTrack=caseObj.get('csTrack')
                    #isAlias=caseObj.get('isAlias')                            
                    
                    if chDefMsg not in ['',"",[],None]:                        
                        rawEvent = {'timestamp': datetime.datetime.now(),
                        'triggerObjDatetime': triggerObjDatetime,
                        'eventDatetime': currentSfDatetime,                        
                        'eventcode': self.eventcode,
                        'targetId': contId,
                        'subject':chDefMsg,
                        'relatedId':caseId,
                        'isAlias':isEAlias, 
                        'caseNo':crNumber,  
                        'CaseSubject':csSubject,
                        'csTrack':csTrack,
                        'subjectId':nid, 
                        'triggerId': nid,  
                        'watcherName':watcherName,                
                        'targetEmail': email, # branch dev
                        'targetDeferred': True,
                        'intPartyIdMap': {},
                        'partyDeferred': True}
                        rawEvnt.append(rawEvent)
                        pass
                    
                    if chMsg not in ['',"",[],None]:                           
                        rawEvent = {'timestamp': datetime.datetime.now(),
                        'triggerObjDatetime': triggerObjDatetime,
                        'eventDatetime': currentSfDatetime,                        
                        'eventcode': self.eventcode,
                        'targetId': contId,
                        'subject':chMsg,
                        'relatedId':caseId,
                        'isAlias':isEAlias, 
                        'caseNo':crNumber, 
                        'CaseSubject':csSubject, 
                        'csTrack':csTrack,
                        'subjectId':nid, 
                        'triggerId': nid,  
                        'watcherName':watcherName,                
                        'targetEmail': email, # branch dev
                        'targetDeferred': False,
                        'intPartyIdMap': {},
                        'partyDeferred': False}                        
                        rawEvnt.append(rawEvent)                                                
                        pass
                pass          
                            
            pass # outside if         
                
        return rawEvnt       
        
    
    
    def getCRFlds(self, crId, crFlds,crDefFlds,cObj):                
        newStr=""
        count=0        
        fld=crFlds
        emailMsg=[]                  
        chDate=None 
        caseComment=None 
        mg=""
        mgDef=""  
        temp=[]   
        temp=self.getCombinedFields(crFlds,crDefFlds) 
        caseHistory=self.getCaseHistory(crId)  
        crNum,csSub,csTrack=self.getCRNum(crId)
        
              
        """if fld!= None:
            temp=fld.split(";")
            pass"""
        for itr in temp:  
            msg={}                                    
            fldNames=itr            
            if fldNames=='Comments':
                caseComment=self.getCaseComments(crId)
                if caseComment is not None:
                    for cc in caseComment:
                        deff=None
                        imm=None
                        commentText=cc.get('CommentBody')
                        chDate=cc.get('CreatedDate')
                        dt=self.formatTime(chDate)
                        if crFlds!=None:
                            imm=crFlds.find(fldNames)                            
                        if crDefFlds!= None:
                            deff=crDefFlds.find(fldNames)
                        if imm  not in [-1,None,'']:                            
                            mg +="%s: Comment Addeed:" %dt
                            mg +="\n"
                            mg +="   '%s'" %(commentText)
                            mg +="\n"
                            #chDate=cc.get('CreatedDate')
                            pass
                        if deff not in [-1,None,'']:
                            mgDef +="%s: Comment Added:" %dt
                            mgDef +="\n"
                            mgDef +="   '%s'" %(commentText)
                            mgDef +="\n"
                            #chDate=cc.get('CreatedDate')
                            pass                           
                pass
            else:                                         
                nm=cObj.get(fldNames)                 
                if (caseHistory is not None) and (nm is not None):                        
                    for ch in caseHistory:
                        deff=None
                        imm=None
                        chFld=ch.get('Field')                       
                        chFld=chFld.split(".")
                        if len(chFld) >=2 :
                            chFld=chFld[1]                       
                        else:
                            chFld=chFld[0]                        
                        if chFld.lower()==nm.lower():                            
                            #msg={}                            
                            newVal=ch.get('NewValue')
                            oldVal=ch.get('OldValue')
                            chDate=ch.get('CreatedDate') 
                            dt=self.formatTime(chDate)                                                      
                            if crFlds!=None:
                                imm=crFlds.find(fldNames)                            
                            if crDefFlds!= None:
                                deff=crDefFlds.find(fldNames)
                            if imm  not in [-1,None,'']:    
                                mg +="%s: '%s' changed \n   FROM '%s' TO '%s'\n" %(dt,fldNames,oldVal,newVal)                                                                                          
                                pass
                            if deff not in [-1,None,'']:
                                mgDef +="%s: '%s' changed \n   FROM '%s' TO '%s'\n" %(dt,fldNames,oldVal,newVal)                                                                                          
                                pass                                                                                           
                            pass
                        pass #for                          
                    pass #if                 
                                                   
                pass   #else                  
            pass #for
        if chDate is not None:      
            msg['createdDate']=chDate
            msg['subMg']=mg
            msg['subMgDef']=mgDef
            msg['CaseId']=crId
            msg['CaseNo']=crNum
            msg['isAlias']=False
            msg['CaseSubject']=csSub
            msg['csTrack']=csTrack
            emailMsg.append(msg)  
            pass  
        
        return emailMsg
    
    def getCompFlds(self, compId, crFlds,crDefFlds,cObj):                
        newStr=""
        count=0        
        #fld=crFlds
        emailMsg=[] 
        caseComment=None          
        temp=[]   
        temp=self.getCombinedFields(crFlds,crDefFlds) 
        compName=self.getCompName(compId)
        windowIsoDateTime=self.getLastProcessDate()       
        soql="Select CaseNumber, Id, LastModifiedDate, Subject, CustomerTracking__c,Status ,Component__c from Case  where Component__c='%s' and Status !='Closed' and LastModifiedDate>= %s" %(compName,windowIsoDateTime)        
        #print "SQL ******  %s" %soql
        ret = self.sfb.query('Case', soql=soql)
        if ret in BAD_INFO_LIST:                        
            msg="No CR found for the component %s" %compName
            #print msg             
            self.sfb.setLog(msg)                     
        else:            
            for cp in ret: 
                mg=""   
                chDate=None 
                mgDef=""
                crId=cp.get('Id') 
                crNum=cp.get('CaseNumber')   
                csSub=cp.get('Subject')
                csTrack=cp.get('CustomerTracking__c')
                #print "Case Number %s ; and component %s" %(crNum,compName)
                caseHistory=self.getCaseHistory(crId)               
                """if fld!= None:
                    temp=fld.split(";")
                    pass"""
                for itr in temp:  
                    msg={}                                    
                    fldNames=itr            
                    if fldNames=='Comments':
                        caseComment=self.getCaseComments(crId)
                        if caseComment is not None:
                            for cc in caseComment:
                                deff=None
                                imm=None
                                commentText=cc.get('CommentBody')
                                chDate=cc.get('CreatedDate')
                                dt=self.formatTime(chDate)
                                if crFlds!=None:
                                    imm=crFlds.find(fldNames)                            
                                if crDefFlds!= None:
                                    deff=crDefFlds.find(fldNames)
                                if imm  not in [-1,None,'']:                            
                                    mg +="%s: Comment Added:"%dt
                                    mg +="\n"
                                    mg +="   '%s'" %(commentText)
                                    mg +="\n"
                                    #chDate=cc.get('CreatedDate')
                                    pass
                                if deff not in [-1,None,'']:
                                    mgDef +="%s: Comment Added:"%dt
                                    mgDef +="\n"
                                    mgDef +="   '%s'" %(commentText)
                                    mgDef +="\n"
                                    #chDate=cc.get('CreatedDate')
                                    pass                           
                        pass
                    else:                                         
                        nm=cObj.get(fldNames)                 
                        if (caseHistory is not None) and (nm is not None):                       
                            for ch in caseHistory:
                                deff=None
                                imm=None
                                chFld=ch.get('Field') 
                                #print ("Comp Field %s and nm %s field" %(chFld,nm))                      
                                chFld=chFld.split(".")
                                if len(chFld) >=2 :
                                    chFld=chFld[1]                       
                                else:
                                    chFld=chFld[0]  
                                if nm not in [None,'']:
                                    if chFld.lower()==nm.lower():                            
                                        #msg={}                            
                                        newVal=ch.get('NewValue')
                                        oldVal=ch.get('OldValue')
                                        chDate=ch.get('CreatedDate') 
                                        dt=self.formatTime(chDate)                           
                                        if crFlds!=None:
                                            imm=crFlds.find(fldNames)                            
                                        if crDefFlds!= None:
                                            deff=crDefFlds.find(fldNames)
                                        if imm  not in [-1,None,'']:    
                                            mg +="%s: %s' changed \n   FROM '%s' TO '%s' \n" %(dt,fldNames,oldVal,newVal)                                                                                          
                                            pass
                                        if deff not in [-1,None,'']:
                                            mgDef +="%s: '%s' changed \n   FROM '%s' TO '%s' \n" %(dt,fldNames,oldVal,newVal)                                                                                          
                                            pass                                                                                           
                                        pass
                                    pass #if
                                pass #for                          
                            pass #if                 
                                                           
                        pass   #else                  
                    pass #for
                               
                if chDate is not None:                    
                    msg['createdDate']=chDate
                    msg['subMg']=mg
                    msg['subMgDef']=mgDef
                    msg['CaseId']=crId
                    msg['CaseNo']=crNum
                    msg['isAlias']=True
                    msg['CaseSubject']=csSub
                    msg['csTrack']=csTrack
                    emailMsg.append(msg)  
                    pass  
        
        return emailMsg
    
    def getAccountFlds(self, acctId, crFlds,crDefFlds,cObj):                
        newStr=""
        count=0     
        lastcount=0   
        #fld=crFlds
        emailMsg=[] 
        caseComment=None  
        contStr=None    
        conts=[]    
        temp=[]   
        temp=self.getCombinedFields(crFlds,crDefFlds) 
        #compName=self.getCompName(compId)
        contIds=self.getContactIds(acctId)                
        for i in range(len(contIds)):            
                      
            if i ==lastcount:
                contStr="(ContactId='%s'"%contIds[i]
            else:
                if(len(contStr) >9000):                    
                    if contStr not in [None,'']:
                        contStr=contStr+")"
                    conts.append(contStr)
                    lastcount=i+1;
                    continue
                else:
                    contStr=contStr+" or " +"ContactId='%s'"%contIds[i]
                    count=count+1
            pass
        
        if contStr not in [None,'']:
            contStr=contStr+")"
            conts.append(contStr)        
        
                   
        
        #sys.exit(0)
        for cs in conts:        
            if cs not in [None,'']:       
                windowIsoDateTime=self.getLastProcessDate()       
                soql="Select CaseNumber, Id, ContactId, Subject,CustomerTracking__c,LastModifiedDate, Status ,Component__c from Case  where %s and Status !='Closed' and LastModifiedDate>= %s" %(cs,windowIsoDateTime)        
                ret = self.sfb.query('Case', soql=soql)
                #print "CASE QUERY ........................................... ******************* %s" %soql
                if ret in BAD_INFO_LIST:                        
                    msg="No CR found for the Account %s" %acctId
                    #print msg             
                    self.sfb.setLog(msg)                     
                else:            
                    for cp in ret: 
                        mg=""   
                        chDate=None 
                        mgDef=""
                        crId=cp.get('Id') 
                        crNum=cp.get('CaseNumber')         
                        csSub=cp.get('Subject')
                        csTrack=cp.get('CustomerTracking__c')
                        caseHistory=self.getCaseHistory(crId)               
                        """if fld!= None:
                            temp=fld.split(";")
                            pass"""
                        for itr in temp:  
                            msg={}                                    
                            fldNames=itr            
                            if fldNames=='Comments':
                                caseComment=self.getCaseComments(crId)
                                if caseComment is not None:
                                    for cc in caseComment:
                                        deff=None
                                        imm=None
                                        commentText=cc.get('CommentBody')
                                        chDate=cc.get('CreatedDate')
                                        dt=self.formatTime(chDate)
                                        if crFlds!=None:
                                            imm=crFlds.find(fldNames)                            
                                        if crDefFlds!= None:
                                            deff=crDefFlds.find(fldNames)
                                        if imm  not in [-1,None,'']:                            
                                            mg +="%s: Comment Added:"%dt
                                            mg +="\n"
                                            mg +="   '%s'" %(commentText)
                                            mg +="\n"
                                            #chDate=cc.get('CreatedDate')
                                            pass
                                        if deff not in [-1,None,'']:
                                            mgDef +="%s: Comment Added:"%dt
                                            mgDef +="\n"
                                            mgDef +="   '%s'" %(commentText)
                                            mgDef +="\n"
                                            #chDate=cc.get('CreatedDate')
                                            pass                           
                                pass
                            else:                                         
                                nm=cObj.get(fldNames)                 
                                if (caseHistory is not None) and (nm is not None):                        
                                    for ch in caseHistory:
                                        deff=None
                                        imm=None
                                        chFld=ch.get('Field')                       
                                        chFld=chFld.split(".")
                                        if len(chFld) >=2 :
                                            chFld=chFld[1]                       
                                        else:
                                            chFld=chFld[0]                        
                                        if chFld.lower()==nm.lower():                            
                                            #msg={}                            
                                            newVal=ch.get('NewValue')
                                            oldVal=ch.get('OldValue')
                                            chDate=ch.get('CreatedDate') 
                                            dt=self.formatTime(chDate)                           
                                            if crFlds!=None:
                                                imm=crFlds.find(fldNames)                            
                                            if crDefFlds!= None:
                                                deff=crDefFlds.find(fldNames)
                                            if imm  not in [-1,None,'']:    
                                                mg +="%s: '%s' changed \n   FROM '%s' TO '%s' \n" %(dt,fldNames,oldVal,newVal)                                                                                          
                                                pass
                                            if deff not in [-1,None,'']:
                                                mgDef +="%s: '%s' changed \n   FROM '%s' TO '%s' \n" %(dt,fldNames,oldVal,newVal)                                                                                          
                                                pass                                                                                           
                                            pass
                                        pass #for                          
                                    pass #if                 
                                                                   
                                pass   #else                  
                            pass #for
                                       
                        if chDate is not None:                    
                            msg['createdDate']=chDate
                            msg['subMg']=mg
                            msg['subMgDef']=mgDef
                            msg['CaseId']=crId
                            msg['CaseNo']=crNum
                            msg['isAlias']=True
                            msg['CaseSubject']=csSub
                            msg['csTrack']=csTrack
                            emailMsg.append(msg)  
                            pass  
                
                return emailMsg
    
    def getTeamFlds(self, tmId, crFlds,crDefFlds,cObj):                
        newStr=""
        count=0        
        fld=crFlds
        emailMsg=[] 
        caseComment=None         
        temp=[]   
        temp=self.getCombinedFields(crFlds,crDefFlds) 
        teamName=self.getTeamName(tmId)
        windowIsoDateTime=self.getLastProcessDate()  
             
        soql="Select Branch_Status__c, Id, LastModifiedDate, Name, Task_Branch__c, Team__c, Team_Branch__c, User__c from Branch_Team_Link__c where Team__c='%s' and LastModifiedDate>= %s " %(teamName,windowIsoDateTime)        
        #print "Team Query %s" %soql   
        ret = self.sfb.query('Branch_Team_Link__c', soql=soql)
        if ret in BAD_INFO_LIST:                        
            msg="No branches found for the Team %s" %teamName
            #print msg             
            self.sfb.setLog(msg)                     
        else:            
            for cp in ret: 
                tbId=cp.get('Task_Branch__c')          
                soql2="Select Branch_Status__c, Case__c, Component__c, Component_Link__c, Id, Name, Task_Branch__c from Branch_CR_Link__c  where Task_Branch__c ='%s'" %tbId
                #print "CR LINK QUERY %s" %soql2
                ret2 = self.sfb.query('Branch_CR_Link__c', soql=soql2)
                if ret2 in BAD_INFO_LIST:                        
                    msg="No CR's found liniked with the task branch %s" %tbId
                    #print msg             
                    self.sfb.setLog(msg)  
                    pass
                else:
                    for tb in ret2:   
                        mg=""   
                        chDate=None    
                        mgDef=""                      
                        crId=tb.get('Case__c') 
                        crNum,csSub,csTrack=self.getCRNum(crId)
                        #print "CASE ID: %s" %crId     
                        caseHistory=self.getCaseHistory(crId)                       
                        """if fld!= None:
                            temp=fld.split(";")
                            pass"""
                        for itr in temp:  
                            msg={}                                    
                            fldNames=itr            
                            if fldNames=='Comments':
                                caseComment=self.getCaseComments(crId)
                                if caseComment is not None:
                                    for cc in caseComment:
                                        deff=None
                                        imm=None
                                        commentText=cc.get('CommentBody')
                                        chDate=cc.get('CreatedDate')
                                        dt=self.formatTime(chDate)
                                        if crFlds!=None:
                                            imm=crFlds.find(fldNames)                            
                                        if crDefFlds!= None:
                                            deff=crDefFlds.find(fldNames)
                                        if imm  not in [-1,None,'']:                            
                                            mg +="%s: Comment Added:"%dt
                                            mg +="\n"
                                            mg +="   '%s'" %(commentText)
                                            mg +="\n"
                                            #chDate=cc.get('CreatedDate')
                                            pass
                                        if deff not in [-1,None,'']:
                                            mgDef +="%s: Comment Added:"%dt
                                            mgDef +="\n"
                                            mgDef +="   '%s'" %(commentText)
                                            mgDef +="\n"
                                            #chDate=cc.get('CreatedDate')
                                            pass                           
                                pass
                            else:                                         
                                nm=cObj.get(fldNames)                 
                                if (caseHistory is not None) and (nm is not None):                        
                                    for ch in caseHistory:
                                        deff=None
                                        imm=None
                                        chFld=ch.get('Field')                       
                                        chFld=chFld.split(".")
                                        if len(chFld) >=2 :
                                            chFld=chFld[1]                       
                                        else:
                                            chFld=chFld[0]                        
                                        if chFld.lower()==nm.lower():                            
                                            #msg={}                            
                                            newVal=ch.get('NewValue')
                                            oldVal=ch.get('OldValue')
                                            chDate=ch.get('CreatedDate') 
                                            dt=self.formatTime(chDate)                           
                                            if crFlds!=None:
                                                imm=crFlds.find(fldNames)                            
                                            if crDefFlds!= None:
                                                deff=crDefFlds.find(fldNames)
                                            if imm  not in [-1,None,'']:    
                                                mg +="%s: '%s' changed \n   FROM '%s' TO '%s' \n" %(dt,fldNames,oldVal,newVal)                                                                                          
                                                pass
                                            if deff not in [-1,None,'']:
                                                mgDef +="%s: '%s' changed \n   FROM '%s' TO '%s' \n" %(dt,fldNames,oldVal,newVal)                                                                                          
                                                pass                                                                                           
                                            pass
                                        pass #for                          
                                    pass #if                 
                                                                   
                                pass   #else                  
                            pass #for
                        if chDate is not None:                    
                            msg['createdDate']=chDate
                            msg['subMg']=mg
                            msg['subMgDef']=mgDef
                            msg['CaseId']=crId
                            msg['CaseNo']=crNum
                            msg['isAlias']=True
                            msg['CaseSubject']=csSub
                            msg['csTrack']=csTrack
                            emailMsg.append(msg)  
                            pass #if 
                        pass #for tb
                    pass #else
                pass #for cp
            pass #else           
            
        return emailMsg
    
    def getTechCmpFlds(self, techCmpId, crFlds,crDefFlds,cObj):                
        newStr=""
        count=0        
        fld=crFlds
        emailMsg=[] 
        caseComment=None         
        temp=[]   
        temp=self.getCombinedFields(crFlds,crDefFlds)                
        windowIsoDateTime=self.getLastProcessDate()       
        soql="Select Id,Parent_CR__c, Name, LastModifiedDate, Tech_Campaign__c from CR_Link__c  where Tech_Campaign__c='%s' and LastModifiedDate>= %s" %(techCmpId,windowIsoDateTime)
        ret = self.sfb.query('CR_Link__c', soql=soql)
        if ret in BAD_INFO_LIST:                        
            msg="No CR found for the TechCampaing with %s" %techCmpId
            #print msg             
            self.sfb.setLog(msg)                     
        else:            
            for cp in ret: 
                mg=""   
                chDate=None  
                mgDef="" 
                crId=cp.get('Parent_CR__c')          
                caseHistory=self.getCaseHistory(crId)
                crNum,csSub,csTrack=self.getCRNum(crId)               
                """if fld!= None:
                    temp=fld.split(";")
                    pass"""
                for itr in temp:  
                    msg={}                                    
                    fldNames=itr            
                    if fldNames=='Comments':
                        caseComment=self.getCaseComments(crId)
                        if caseComment is not None:
                            for cc in caseComment:
                                deff=None
                                imm=None
                                commentText=cc.get('CommentBody')
                                chDate=cc.get('CreatedDate')
                                dt=self.formatTime(chDate)
                                if crFlds!=None:
                                    imm=crFlds.find(fldNames)                            
                                if crDefFlds!= None:
                                    deff=crDefFlds.find(fldNames)
                                if imm  not in [-1,None,'']:                            
                                    mg +="%s: Comment Added:"%dt
                                    mg +="\n"
                                    mg +="   '%s'" %(commentText)
                                    mg +="\n"
                                    #chDate=cc.get('CreatedDate')
                                    pass
                                if deff not in [-1,None,'']:
                                    mgDef +="%s: Comment Added:"%dt
                                    mgDef +="\n"
                                    mgDef +="   '%s'" %(commentText)
                                    mgDef +="\n"
                                    #chDate=cc.get('CreatedDate')
                                    pass                           
                        pass
                    else:                                         
                        nm=cObj.get(fldNames)                 
                        if (caseHistory is not None) and (nm is not None):                       
                            for ch in caseHistory:
                                deff=None
                                imm=None
                                chFld=ch.get('Field')                       
                                chFld=chFld.split(".")
                                if len(chFld) >=2 :
                                    chFld=chFld[1]                       
                                else:
                                    chFld=chFld[0]                        
                                if chFld.lower()==nm.lower():                            
                                    #msg={}                            
                                    newVal=ch.get('NewValue')
                                    oldVal=ch.get('OldValue')
                                    chDate=ch.get('CreatedDate') 
                                    dt=self.formatTime(chDate)                           
                                    if crFlds!=None:
                                        imm=crFlds.find(fldNames)                            
                                    if crDefFlds!= None:
                                        deff=crDefFlds.find(fldNames)
                                    if imm  not in [-1,None,'']:    
                                        mg +="%s: '%s' changed \n   FROM '%s' TO '%s' \n" %(dt,fldNames,oldVal,newVal)                                                                                          
                                        pass
                                    if deff not in [-1,None,'']:
                                        mgDef +="%s: '%s' changed \n   FROM '%s' To '%s' \n" %(dt,fldNames,oldVal,newVal)                                                                                          
                                        pass                                                                                           
                                    pass
                                pass #for                          
                            pass #if                 
                                                           
                        pass   #else                  
                    pass #for
                if chDate is not None:                                                
                    msg['createdDate']=chDate
                    msg['subMg']=mg
                    msg['subMgDef']=mgDef
                    msg['CaseId']=crId
                    msg['CaseNo']=crNum
                    msg['isAlias']=True
                    msg['CaseSubject']=csSub
                    msg['csTrack']=csTrack
                    emailMsg.append(msg)  
                    pass  
        
        return emailMsg
    
    def getUsrFlds(self, usrId, crFlds,crDefFlds,cObj):                
        newStr=""
        count=0        
        fld=crFlds
        emailMsg=[] 
        caseComment=None        
        temp=[]   
        temp=self.getCombinedFields(crFlds,crDefFlds)           
        windowIsoDateTime=self.getLastProcessDate()       
        soql="Select Id,CaseNumber, ContactId, Subject,CustomerTracking__c,OwnerId, RecordTypeId, Status,LastModifiedDate from Case  where OwnerId ='%s' and Status !='Closed' and LastModifiedDate >= %s" %(usrId,windowIsoDateTime)
        #print "User QUERY : %s" %soql
        ret = self.sfb.query('Case', soql=soql)
        if ret in BAD_INFO_LIST:                        
            msg="No Case found for the User %s" %usrId
            #print msg             
            self.sfb.setLog(msg)                     
        else:            
            for cp in ret: 
                mg=""   
                chDate=None  
                mgDef="" 
                crId=cp.get('Id')
                crNum=cp.get('CaseNumber')
                csSub=cp.get('Subject')
                csTrack=cp.get('CustomerTracking__c')
                caseHistory=self.getCaseHistory(crId)                
                if fld!= None:
                    temp=fld.split(";")
                    pass
                for itr in temp:  
                    msg={}                                    
                    fldNames=itr            
                    if fldNames=='Comments':
                        caseComment=self.getCaseComments(crId)
                        if caseComment is not None:
                            for cc in caseComment:
                                deff=None
                                imm=None
                                commentText=cc.get('CommentBody')
                                chDate=cc.get('CreatedDate')
                                dt=self.formatTime(chDate)
                                if crFlds!=None:
                                    imm=crFlds.find(fldNames)                            
                                if crDefFlds!= None:
                                    deff=crDefFlds.find(fldNames)
                                if imm  not in [-1,None,'']:                            
                                    mg +="%s: Comment Added:"%dt
                                    mg +="\n"
                                    mg +="   '%s'" %(commentText)
                                    mg +="\n"
                                    #chDate=cc.get('CreatedDate')
                                    pass
                                if deff not in [-1,None,'']:
                                    mgDef +="%s: Comment Added:"%dt
                                    mgDef +="\n"
                                    mgDef +="   '%s'" %(commentText)
                                    mgDef +="\n"
                                    #chDate=cc.get('CreatedDate')
                                    pass                           
                        pass
                    else:                                         
                        nm=cObj.get(fldNames)                 
                        if (caseHistory is not None) and (nm is not None):                       
                            for ch in caseHistory:
                                deff=None
                                imm=None
                                chFld=ch.get('Field')                       
                                chFld=chFld.split(".")
                                if len(chFld) >=2 :
                                    chFld=chFld[1]                       
                                else:
                                    chFld=chFld[0]                        
                                if chFld.lower()==nm.lower():                            
                                    #msg={}                            
                                    newVal=ch.get('NewValue')
                                    oldVal=ch.get('OldValue')
                                    chDate=ch.get('CreatedDate')
                                    dt=self.formatTime(chDate)                            
                                    if crFlds!=None:
                                        imm=crFlds.find(fldNames)                            
                                    if crDefFlds!= None:
                                        deff=crDefFlds.find(fldNames)
                                    if imm  not in [-1,None,'']:    
                                        mg +="%s: '%s' changed \n   FROM '%s' TO '%s' \n" %(dt,fldNames,oldVal,newVal)                                                                                          
                                        pass
                                    if deff not in [-1,None,'']:
                                        mgDef +="%s: '%s' changed \n   FROM '%s' To '%s' \n" %(dt,fldNames,oldVal,newVal)                                                                                          
                                        pass                                                                                           
                                    pass
                                pass #for                          
                            pass #if                 
                                                           
                        pass   #else                  
                    pass #for
                if chDate is not None:                                                
                    msg['createdDate']=chDate
                    msg['subMg']=mg
                    msg['subMgDef']=mgDef
                    msg['CaseId']=crId
                    msg['CaseNo']=crNum
                    msg['isAlias']=False
                    msg['CaseSubject']=csSub
                    msg['csTrack']=csTrack
                    emailMsg.append(msg)  
                    pass  
        
        return emailMsg
    
    def getCombinedFields(self,crFlds,crDefFlds):
        comList=[]
        if crFlds!= None:
            temp=crFlds.split(";")
            pass
            for itr in temp: 
                comList.append(itr)            
                pass
        if crDefFlds!=None:
            temp1=crDefFlds.split(";")
            pass
            for itr1 in temp1: 
                contains=False
                for cl in comList:
                    if cl==itr1:
                        contains=True
                        pass
                    pass
                if contains is False:
                    comList.append(itr1)            
                pass        
        return comList
            
    
    def getCaseComments(self,crId):
        windowIsoDateTime=self.getLastProcessDate()             
              
        fields=('ParentId', 'CreatedById', 'CreatedDate', 'IsPublished', 'Id', 'CommentBody','SystemModstamp')
        where=[['ParentId','=',crId],'and',['LastModifiedDate','>=', windowIsoDateTime]]   
        #print "Where ***** %s" %where     
        res = self.sfb.query('CaseComment', where, fields)   
        if res in BAD_INFO_LIST:
            res = None
            pass    
        return res
        
        return
    
    def getTeamName(self,tmId):
        teamName=None
        idList = []
        idList.append(tmId)
        fields = ('Id','Name')
        ret = self.sfb.retrieve(idList, 'Product_Team__c', fieldList=fields)
        if ret in BAD_INFO_LIST: 
            msg ="Could not find any records for the Component Id: %s" %tmId
            #print msg
            self.sfb.setLog(msg, 'warn')
            pass                
        else:
            for cont in ret:
                teamName=cont.get('Name')                                         
            pass
        return teamName
    
    def getContactIds(self,acctId):
        
        contIds=[]
        #fields=('Id', 'AccountId')
        #where=[['AccountId','=',acctId]]        
        #res = self.sfb.query('Contact', where, fields)       
        soql="Select Id,AccountId from Contact  where AccountId='%s' " %(acctId)        
        #print "SQOL ..... ...%s"% soql
        res = self.sfb.query('Contact', soql=soql)
        if res not in BAD_INFO_LIST:
            for rs in res:
                cId=rs.get('Id')                
                contIds.append(cId)
                pass
            pass        
        return contIds
        
        
        
    def getCompName(self,compId):
        compName=None
        idList = []
        idList.append(compId)
        fields = ('Id','Name')
        ret = self.sfb.retrieve(idList, 'Component__c', fieldList=fields)
        if ret in BAD_INFO_LIST: 
            msg ="Could not find any records for the Component Id: %s" %compId
            #print msg
            self.sfb.setLog(msg, 'warn')
            pass                
        else:
            for cont in ret:
                compName=cont.get('Name')                                 
            pass
        return compName
    
    def getCRNum(self,caseId):
        crNum=None
        csSub=None
        csTrack=None
        idList = []
        idList.append(caseId)
        fields = ('Id','CaseNumber','Subject','CustomerTracking__c')
        ret = self.sfb.retrieve(idList, 'Case', fieldList=fields)
        if ret in BAD_INFO_LIST: 
            msg ="Could not find CR Number for the Case Id: %s" %caseId
            #print msg
            self.sfb.setLog(msg, 'warn')
            pass                
        else:
            for cont in ret:
                crNum=cont.get('CaseNumber')  
                csSub=cont.get('Subject')                               
                csTrack=cont.get('CustomerTracking__c') 
            pass
        #print "getCRNum ... %s" %csSub
        return crNum,csSub,csTrack
    
    def getCaseHistory(self,crId): 
               
        windowIsoDateTime=self.getLastProcessDate()             
        fields=('CaseId', 'CreatedById', 'CreatedDate', 'Field', 'Id', 'NewValue','OldValue')
        where=[['caseId','=',crId],'and',['CreatedDate','>=', windowIsoDateTime]]  
        #print "SQL ******  %s" %where       
        res = self.sfb.query('CaseHistory', where, fields)   
        if res in BAD_INFO_LIST:
            res = None
            pass            
        return res
    
    def formatTime(self,dt):             
        
        EpochSeconds = time.mktime(time.strptime(dt, '%Y-%m-%dT%H:%M:%S.000Z')) 
        nowDt = datetime.datetime.fromtimestamp(EpochSeconds)        
        nowLocal = datetime.datetime.now()           
        now=datetime.datetime.utcnow()      
        diff=now-nowLocal   
        new=nowDt+(-diff)        
        finaldate = new.strftime("%b %d %H:%M")        
        
        return finaldate
        


    def gatherRecipients(self, eventStruct):
        """ Determine the recipients of this message in a number of ways.
        Note the reason each recipient is getting the notice - Should be a
        phrase which completes the sentence, 'You are receiving this notice
        because...'
        """
        targetUserId = eventStruct.get('targetId')        
        
        subject=eventStruct.get('subject')
        recipientIdMap = {}

        # first, the target of the notification
        why = 'you have expressed interest in the following change of events'
        self.addRecipient(recipientIdMap, targetUserId, why)  

        return recipientIdMap
    ## END gatherRecipients


    def buildNotification(self, event):
        msgDate = "%s" %event.get('timestamp').strftime('%b %d %H:%M')
        targetId = event.get('targetId')  
        #print "EVENT %s" %event
        email=event.get('targetEmail')
        #print "TARGET EMAIL %s" %email
        targetId = convertId15ToId18(targetId)
        recipInfo = event.get('userMap').get(targetId)               
        if recipInfo not in [None,'']:
            recipName = "%s %s" %(recipInfo.get('FirstName',''), recipInfo.get('LastName'))
            recipName = recipName.strip()        
        id = event.get('relatedId')        
        subject=event.get('subject')   
        crNum=event.get('caseNo')
        caseSubject=event.get('CaseSubject')
        csTrack=event.get('csTrack')
        watcherName=event.get('watcherName')
        
        if email not in [None,'']:
            molten=email.find('@magma')
            if molten != -1:
                baUrl = '%s/%s' %(self.sfb.sfdc_base_url, id)
                csTrack=""
            else:
                baUrl ='%s/%s' %('https://molten.moltenmagma.com/cases/show',id)
        else:
            baUrl = '%s/%s' %(self.sfb.sfdc_base_url, id)      
            csTrack=""           
        
        
        #stream = tbData.get('Code_Stream__c')
        
        
        #tbUrl = '%s/%s' %(self.sfb.sfdc_base_url, tbId)

        # find the CR num for which the fix was rejected
       
        #datelineFmt = '%%%ss\n\n' %WW
        datelineFmt = '\n'         
        #msg  = datelineFmt %msgDate
        msg=msgDate
        msg+="   "
        if len(crNum)==8:
            crNum=crNum[3:8]
        
            
        ## Change to body on 07-23
        
        #msg += "CR:%s " %(crNum)    
        #msg+="   "
        #msg+="Case Watcher: %s \n"%watcherName
        
        if caseSubject not in [None,'']:
            if len(caseSubject)>72:
                #print "CASE Subject Length...%s.. "%len(caseSubject)
                caseSubject=caseSubject[0:72]
                
        if csTrack not in [None,'']:
            msg += "CR:%s " %(crNum)    
            msg +="   "
            msg +="Tracking ID: %s "%csTrack
            msg +="   "            
            msg +="Case Subject: %s \n"%caseSubject   
        else:     
            msg +="Case Watcher: %s "%watcherName
            msg +="   "
            msg += "CR:%s " %(crNum)    
            msg +="   "
            msg +="Case Subject: %s \n"%caseSubject
        
        
        #msg += "%s,\n\n" %recipName          
        #print "Message ... %s" %msg

        delinquentDelta =  event.get('eventDatetime') - event.get('triggerObjDatetime')
        deltaText = dayNumToTxt(delinquentDelta)
        
        #para = "The fix for CR %s in branch %s in stream %s has been rejected by the CR originator. For further information, please view the rejected Branch Approval record (linked below) to see if the originator left any notes, or contact the CR originator directly." %(crNum, branch, stream)
        para="This is a email relates to change of events on CRs, that you have subscribed for.."
        """msg += "%s\n\n" %textwrap.fill(para, WW)"""
        msg += "%s" %(subject)
        msg += " * Case Link: %s" %baUrl
        
        #print "FULL MESSAGE: %s" %msg      
      
        #print msg
        return msg
    ## END buildNotification

    def action(self):
        """ Process actionable events """
        msgQueue = MailMessageQueue(test=self.opts.testflag)

        for actionEvent in self.actionList:
            # Gather all recipients
            
            recipientMap = self.gatherRecipients(actionEvent)            
            actionEvent['intPartyIdMap'] = recipientMap            
            actionEvent['userMap'] = self.queryRecipients(recipientMap.keys())           
           
            delinquentDelta =  actionEvent.get('eventDatetime') - actionEvent.get('triggerObjDatetime')
            deltaText = dayNumToTxt(delinquentDelta)

            # build a notification and post it to each recipient's queue.
            # flag each with the immediate flag...
            body = self.buildNotification(actionEvent)
            subj = "Interested Event Notification."                   

            # post the message to each recipient's queue
            msgMap = {}
            for recipId, recipWhy in recipientMap.items():              
                
                
                userInfo = actionEvent.get('userMap').get(recipId)                            
                
                try:
                    notification = copy.copy(MailNotification.notification)
                    notification = {'subject': subj,
                                    'body': body,
                                    'timestamp': actionEvent.get('timestamp')}
    
                    # note the recipient's user info
                    email=actionEvent.get('targetEmail')
                    
                    #IF the email address is the generic account"   
                    #print "Target Id .............. %s"%(actionEvent.get('targetId'))
                    #print "TARGET Email ............%s" %email
                    if (actionEvent.get('targetId') in ['0033f000000HPwQRAAW','0033000000HPwQR']):
                        userInfo['FirstName']='Salesforce'
                        userInfo['LastName']='User'
                        userInfo['Email']=email 
                        pass
                    else:
                        userInfo['Email']=email                                        
                                   
                    notification['recipInfo'] = userInfo  
                    notification['email']=email              
                    if recipId == actionEvent.get('targetId'):
                        notification['deferred'] = actionEvent.get('targetDeferred')
                    else:
                        notification['deferred'] = actionEvent.get('partyDeferred')   
                        pass
                    notification['why'] = recipWhy
                    notification['eventcode']=actionEvent.get('eventcode')
                    notification['isAlias']=actionEvent.get('isAlias')   
                    notification['targetId'] = recipId             
                    # collect for batch enqueueing
                    #pprint.pprint(notification)
                    #msgMap[email]=notification
                    msgMap[recipId] = notification                
                except:
                    pass
                
                continue
            # now, enqueue all the messages at once
            #Uncomment later
            
            success = msgQueue.enqueue(msgMap)
            
            #self.sendImmediateNotification()
            
            """if success is True:
                # Finally, create the exclusion condition to prevent this
                # event from being processed again.
                self.exclude(actionEvent, subj, body)"""
                

            #break # for debug
            continue
        
        return ## END action

    pass
## END class BAActionAlarmHandler

def sendMessage(self, recip, subj, body):
        global testMailAddr
        
        fromAdd = 'salesforce-support@molten-magma.com'
        toAdd = recip.getDataMap()['Email']


        logmsg = 'Sending notification mail for %s' %toAdd
        if self.opts.testflag is True:
            logmsg = 'Notification mail for %s, sent to test recipient %s' \
                     %(toAdd, testMailAddr)
            toAdd = testMailAddr
            pass

        self.sfb.setLog(logmsg , 'info')

        try:
            msg = Message(fromAdd, toAdd, body, subj)
            self.mailserver.sendEmail(msg)
        except:
            return False

        return True


class CustomCaseEventsHandler(CustomCaseEvents):
   
    eventcode = "CUSTOM" #Custom notification    
    
    windowDays = 30
    intervalDays = 0
    limitTimes = 0    
    pass



class CustomCaseEventsHarness:
    
    handlers = ('CustomCaseEventsHandler',)

    def __init__(self, opts=None):
        self.opts = opts

    def do(self):
        sfTool = SFTaskBranchTool(logname='CustomEvents')
    
        for handlerName in self.handlers:
            runHandler = '%s(sfTool, self.opts)' %handlerName
            
            handler = eval(runHandler)
            handler.flow()
            #handler.getNotificationObject()
            #handler.testPoll()
            continue

        return


def main():
    op = OptionParser()
    op.add_option('-l', '--live', dest='testflag', action='store_false',
                  default=True,
                  help='connects to live storage for events - default is test')

    (opts, args) = op.parse_args()

    harness = CustomCaseEventsHarness(opts)
    harness.do()

    
if __name__ == '__main__':
    main()
