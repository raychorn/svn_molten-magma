#!/usr/bin/python

'''
TokenMinder is a class intended to clean up SCM token files created by test scripts.

TokenMinder uses the sftest.cfg config file for configuration

Use is simple:

tm = TokenMinder(ConfigObj)
tm.do()

where ConfigObj is a ConfigParser that has read in the sftest.cfg file.

The approach of tokenminder is two-fold:

First, token minder checks its personal tokenminder inbox (currently:
/home/sfscript/tmDrop) for drop files containing a token path and removes
the represented token file and the drop file.

Second, it will scan the SCM token drop box for test tokens older than
a certain age and remove them under the assumption that the token has
been abandoned by the test script that was responsible for it.
'''

import os, glob, re, stat, time, sys
import ConfigHelper

class TokenMinder:

    def __init__(self, props):
        self.props = props

        # set up properties
        self.testId = props.get('main', 'testId')

        self.tokenDir = self.props.get('main', 'tokenDir')
        
        self.batchOwnerHome = self.props.get('main', 'batchOwnerHome')

        self.tokenminderInboxName = self.props.get('main', 'tokenminderInbox')
        self.tokenminderInbox = os.path.join(self.batchOwnerHome,
                                             self.tokenminderInboxName)
        
        # tokens older than specified will be considered abandoned
        self.abandonedTokenSecs = self.props.getint('main',
                                               'abandonedTokenMins') * 60
        
        # NOTE: this relies on the batch owner's (sfscript) primary group being
        # 'develop'
        self.batchOwnerUid = os.getuid()
        self.developGid = os.getgid()
    ## END __init__(self, props)

    def isTokenOurs(self, tokenPath):
        '''
        Determines if a token name is one that we are insterested in or not
        by testing for pattern verityTag__\d{8}_\d{6}
        
        Returns True if the token matches the pattern and False if it does not.
        '''
        (tokenDir, tokenFile) = os.path.split(tokenPath)
        
        testTokenRE = self.testId + "_\d{8}_\d{6}"
        testTokenPat = re.compile(testTokenRE)
        
        testTokenMatch = testTokenPat.search(tokenFile)
        
        if testTokenMatch is not None:
            return True
        else:
            return False
    ## END def isTokenOurs(verityTag, tokenPath)
        
    def isTokenAged(self, tokenPath):
        now = time.time()
        
        if os.path.exists(tokenPath):
            modTime = os.stat(tokenPath)[8]
            if (now - modTime) > self.abandonedTokenSecs:
                return True
            
            return False
    ## END def isTokenAged(boundAgeSecs, tokenPath)

    def removeToken(self, tokenPath):
        if sys.stderr.isatty():
            print "removing token at: " + tokenPath
        try:
            os.remove(tokenPath)
            foo=None
        except:
            # do nothing so that we have silent failure.
            foo=None
    ## END def safeRemoveToken(testId, tokenFilePath)


    def do(self):
        # Check for the drop box - create if necessary
        if os.path.isdir(self.tokenminderInbox) is not True:
            os.makedirs(self.tokenminderInbox)
            os.chown(self.tokenminderInbox,
                     self.batchOwnerUid, self.developGid)
            os.chmod(self.tokenminderInbox, 0770)
            
        # First, check our drop box for references to tokens to remove immediately
        if sys.stderr.isatty():
            print "checking " + self.tokenminderInbox
        dropFileGlob = os.path.join(self.tokenminderInbox, '*.tm')
        toDoList = glob.glob(dropFileGlob)

        for dropFile in toDoList:
            fd = file(dropFile, 'r+')
            tokenFilePath = fd.readline()
            fd.close()
            tokenFilePath = tokenFilePath.strip()
            
            if self.isTokenOurs(tokenFilePath):
                self.removeToken(tokenPath=tokenFilePath)
                if sys.stderr.isatty():
                    print "Removing dropFile: " + dropFile
                os.remove(dropFile)

        # Next, check the SCM token drop dir for any of our tokens that are
        # old enough to be presumed abandoned by the test script.
        if sys.stderr.isatty():
            print "checking " + self.tokenDir
        tokenFileGlob = os.path.join(self.tokenDir, '*.%s_*' %self.testId)
        toDoList = glob.glob(tokenFileGlob)

        for tokenFilePath in toDoList:
            if (self.isTokenOurs(tokenFilePath) and
                self.isTokenAged(tokenPath=tokenFilePath)):
                self.removeToken(tokenPath=tokenFilePath)
    ## END do(self)
    

## END class TokenMinder

def main():
    # Fetch the config
    props = ConfigHelper.fetchConfig('conf/sfutil.cfg')
    
    tm = TokenMinder(props)
    tm.do()
## END def main()
    
if __name__ == '__main__':
    main()



