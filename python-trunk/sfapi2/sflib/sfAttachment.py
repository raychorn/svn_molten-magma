import pprint
import copy
import os.path
import base64

from sfNoteAttach import SFNoteAttach
from sfMagma import SFMagmaTool

class SFAttachment(SFNoteAttach):
    obj = "Attachment"

    def writeToFile(self, path):
        """ Write an attachment to a file"""
        attData = self.getDataMap()
        filename = attData.get('Name',None)
        if filename is None:
            filename = attData.get('Id')
            pass

        body = attData.get('Body',None)
        if body is not None:
            filepath = os.path.join(path, filename)
            f = file(filepath, 'w+')
            f.write(base64.decodestring(body))
            f.close()
            pass

        return
    ## END writeToFile

if __name__ == '__main__':
    sfTool = SFMagmaTool()

    srcObjId = '50030000000MEva'
    dstObjId = '50030000000MEve'
    
    attList = SFAttachment.queryParent(sfTool, srcObjId)
    
    for att in attList:
        att = att.relink(dstObjId)
