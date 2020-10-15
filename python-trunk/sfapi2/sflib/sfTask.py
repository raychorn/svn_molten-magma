import pprint
import copy

from sfCrudObject import SFCrudObject
import mail

class SFTask(SFCrudObject):
    obj = "Task"

    def notifyTaskOwner(self, body=None, subject=None, ccAddrs=None):
        from sfUser2 import SFUser
        taskData = self.getDataMap()
        
        if subject is None:
            subject = "Task: %s" %taskData.get('Subject', 'No Task Subject')
            pass

        if body is None:
            body  = "%s\n" %subject
            body += "%s/%s\n" %(self.sfTool.sfdc_base_url, taskData.get('Id'))
            body += "\n\n%s\n" %taskData.get('Description',
                                             'No Task Description')
            pass

        # Find the owner's email
        taskOwnerId = taskData.get('OwnerId')
        owner = SFUser.retrieve(self.sfTool, taskOwnerId)
        ownerData = owner.getDataMap()
        ownerEmail = ownerData.get('Email')
        
        message = mail.Message(self.sfTool.from_addr, ownerEmail, body,
                               subject, ccAddrs)

        mailServer = self.sfTool.mailServer2()

        mailServer.sendEmail(message)
        return 

   
if __name__ == "__main__":
    from sfMagma import SFMagmaTool
    sfTool = SFMagmaTool()

    taskData = {'OwnerId': '00530000000cZcRAAU',
                'Status': 'Not Started',
                'Description': 'This was created using the API',
                'Subject': 'Test Task',
                'Priority': 'Normal'}

    task = SFTask.create(sfTool, taskData)

    if task is None:
        print "Failed"
    else:
        taskDat = task.getData(SFTask.obj)
        pprint.pprint(taskDat)
