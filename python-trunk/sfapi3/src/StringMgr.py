"""
Passed a message code and a list of arguments, format and return a string
Subclass this for managing other message libraries
"""

import re
import msgStrings

class MsgMgr:

    _MsgLibFile = 'msglib.cfg'
    _MsgLibSection = 'Main'

    _MapMsgLib = {} # static map of message libraries
    # {Section: {code1: msg1, code2: msg2}}

    def __init__(self, libSection=None, libFile=None, forceLoad=False):
        global _MsgLibFile
        global _MsgLibSection
        global _MapMsgLib

        self.msgLibFile = _MsgLibFile
        if libFile is not None:
            self.msgLibFile = libFile
            pass
        
        self.msgLibSection = _MsgLibSection
        if libSection is not None:
            self.msgLibSection = libSection
            pass

        # merge the specified section of the lib file into the gloabal msg lib
        
        

        self.msgMap = _MapMsgLib.get(self.msgLibSection, {})
        return
    ## END __init__

    def format(self, msgCode, *subs):

        msgStr = self.msgMap.get(msgCode, None)

        if msgStr is None:
            msgStr = 'The message code "%s" cannot be found in message library %s, section %s' %(msgCode, self.msgLibFile, self.msgLibSection)
            msgCode = 'ERR_MSGNFND'
            subs = ()

        ctSub = 0
        for sub in subs:
            ctSub += 1

            # format the sequential substitution token
            pattern = '%%s' ctSub
            
            # replace the first occurrence of the sub token
            re.sub(pattern, sub, msgStr, 1)
            continue

        # prepend the message code to the beginning of the message
        return '%s: %s' %(msgCode, msgStr)
    ## END format
        
