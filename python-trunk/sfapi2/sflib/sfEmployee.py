from types import ListType

from sfCrudObject import ObjectNotFoundError
from EmployeeMixin import checkEmpNo
from sfUtil import convertId15ToId18
from sfUser2 import SFUser
from sfContact2 import SFContact

class Employee:
    def __init__(self, userObj, contactObj):
        self.userObj = userObj
        self.contactObj = contactObj
        return
    ## END __init__

    def queryEmpNo(klass, sfTool, empNo):
        empNo = checkEmpNo(empNo)
        contactList = SFContact.queryEmpNo(sfTool, empNo)

        contact = None
        if len(contactList) == 0:
            msg = "No Contact found for employee number %s" %empNo
            raise ObjectNotFoundError(msg)
        elif len(contactList) > 0:
            if len(contactList) > 1:
                msg = "More than one Contact found with employee number %s" %empNo
                sfTool.setLog(msg, 'error')
                pass
            contact = contactList[0]
            pass

        contactData = contact.getDataMap()
        contactId = contactData.get('Id')
        contactUserId = contactData.get('Contact_User_Id__c')

        user = None

        if contactUserId is not None:
            contactUserId = convertId15ToId18(contactUserId)
            user = SFUser.retrieve(sfTool, contactUserId)
            if user is None:
                msg = "No User found for contact %s" %contactId
                sfTool.setLog(msg, 'warn')
                pass
            pass

        if user is not None:
            userData = user.getDataMap()
            userId = userData.get('Id')
            userContactId = convertId15ToId18(\
                userData.get('User_Contact_Id__c'))

            if userContactId != contactId:
                msg = "Contact ID on User Record does not match the ID of the Contact Record which listed this user: User - %s; Contact %s" %(userContactId, contactId)
                print msg
                sfTool.setLog(msg, 'error')
                pass
            

        employee = klass(user, contact)
        return employee
    queryEmpNo = classmethod(queryEmpNo)

    def update(self):
        if self.userObj is not None:
            self.userObj.update()
            pass

        if self.contactObj is not None:
            self.contactObj.update()
            pass

        return
        
    pass


            
