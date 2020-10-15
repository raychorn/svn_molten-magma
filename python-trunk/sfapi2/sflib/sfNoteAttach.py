""" Common elements shared by both note and attachment objects
"""
import pprint
import copy
import base64

from sfCrudObject import SFCrudObject, DetailRecordMixin

class SFNoteAttach(SFCrudObject, DetailRecordMixin):
    """
    Class of properties and methods common to both notes and attachments
    """

    def relink(self, newParentObjId):
        """ Creates a duplicate attachment linked to the new parent obj
        and deletes the old attachemnt if that succeeds.
        requires that all fields have been fetched
        """
        attData = self.getDataMap()

        newIsPrivate = False 
        if attData.get('IsPrivate') == 'true':
            newIsPrivate = True
            pass

        newOwnerId = self.sfTool.cascadeToActiveUser(attData.get('OwnerId'))

        body = attData.get('Body')

        if self.obj == 'Attachment':
            if body in ['',None]:
                return None
        
            body = base64.decodestring(body)
            pass
        
        newAttData = {'Name': attData.get('Name'),
                      'Body': base64.decodestring(attData.get('Body')),
                      'IsPrivate': newIsPrivate,
                      'OwnerId': newOwnerId,
                      'ParentId': newParentObjId}

        #print "Creating attachment: %s" %pprint.pformat(newAttData)
        #self.sfTool.debug = 4

        # create the new attachment on the specified parent obj
        newAtt = self.__class__.create(self.sfTool, newAttData)
        
        #print self.sfTool.lastRet
        if newAtt is not None:
            # remove the old attachment
            print "Deleting attachment %s" %attData.get('Id')
            self.delete()
        self.sfTool.debug = 0
        
        return newAtt
    ## END relink



