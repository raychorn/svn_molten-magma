#!/usr/bin/env python2.3
"""
A class to represent an SCM token and to provide basic functions with them
In the future, class shall get token creation abilities that are currently
embedded in the Branch object.
"""
import sys
import os
import shutil
import re
import string

# global constants
scm_rootDir   = '/magma/scm-release/submissions'  #'/home/sfscript/data/submissionsTest'
scm_shadowDir = '/home/sfscript/data/submissionsTest' #'/magma/scm-release/submissions'
scm_dropDir = '/home/sfscript/data/drop'

sfscmDir = os.path.join(scm_rootDir, 'sf-scm')
replacedTokenDir = os.path.join(sfscmDir, 'replaced')
tokenCRLimit = 20 # how many tokens allowed before we have to split token.

class BranchToken:

    def __init__(self, tokenPathList):
        """
        Assume all files for token are in the same directory
        """
        self.tfList = []
        self.numFiles = 0
        self.tokenDir = None
        self.tokenBaseName = None

        for tokenPath in tokenPathList:
            if os.path.exists(tokenPath):
                tf = {}
                tf['path'] = os.path.abspath(tokenPath)
                
                tf['dir'], tf['fileName'] = os.path.split(tf['path'])
                
                tf['atime'], tf['mtime'] = self.lookupFileTimes(tf['path'])
                
                tf['crStr'], tf['baseName'] = tf['fileName'].split('.', 1)

                self.tfList.append(tf)

                if self.tokenDir is None:
                    self.tokenDir = tf['dir']
                elif tf['dir'] != self.tokenDir:
                    msg = "All files of this token are not in the same directory!"
                    raise TokenException(msg)

                if self.tokenBaseName is None:
                    self.tokenBaseName = tf['baseName']
                elif tf['baseName'] != self.tokenBaseName:
                    msg = "All files of this token do not have the same base name!"
                    raise TokenException(msg)
                
            else:
                msg =  "Could not locate file: %s" %tokenPath
                raise TokenException(msg)
            
        self.tfList.sort(lambda a,b: cmp(a['mtime'], b['mtime']))
        self.numFiles = len(self.tfList)
    ## END def __init__(self, tokenPath)


    def lookupFileTimes(self, path):
        """
        Method gets the access and modified times of the file provided
        and returns the atime and mtime of the file.
        """
        atime = os.path.getatime(path)
        mtime = os.path.getmtime(path)
        return atime, mtime
    ## END def getFileTimes(self, tokenPath)


    def getPaths(self):
        pathList = []
        for tf in self.tfList:
            pathList.append(tf['path'])
        return pathList
    ## END getPaths(self)

    def formatPaths(self):
        pathList = self.getPaths()
        
        fileOrFiles = 'file'
        if len(pathList) > 1:
            fileOrFiles = 'files'
            pass

        
        msg = "This token consists of %s %s as follows:\n" %(len(pathList),
                                                               fileOrFiles)
        count = 1
        for path in pathList:
            msg += "Token path %s\n" %count
            msg += "%s\n" %path
            count += 1
            continue
        
        msg += "-"*75 + "\n"
        
        return msg
    ## END formatPaths

    def getCRNums(self):
        crList = []
        crNums = []
        for tf in self.tfList:
            crList.extend(tf['crStr'].split('_'))

        for cr in crList:
            try:
                crNums.append(int(cr))
            except Exception, e:
                pass
        return crNums
    ## END getCRNums(self)

    def setFileTimes(self):
        newTfList = []
        for tf in self.tfList:
            tf['atime'] = os.path.getatime(tf['path'])
            tf['mtime'] = os.path.getmtime(tf['path'])
            newTfList.append(tf)

        self.tfList = newTfList
    ## END setFileTimes(self)

    def getFileTimes(self):
        atimeList = []
        mtimeList = []
        for tf in self.tfList:
            atimeList.append(tf['atime'])
            mtimeList.append(tf['mtime'])

        return atimeList, mtimeList
    ## END getFileTimes(self)

    
    def createReplacementToken(self, oldToken):
        """
        Given a path, the Token instance copies the file to which it
        points to the path,  and returns a new Token instance representing
        the new Token.
        """
        global replacedTokenDir

        sortedCRList = []

        oldTokenDir = os.path.abspath(oldToken.tokenDir)
        oldTokenBaseName = oldToken.tokenBaseName

        # Get the new list of CRs by keeping the order from the old
        # token and appending new CRs at the end.
        sortedCRList = oldToken.getCRNums()
        sortedCRList.extend(oldToken.findNewCRs(self.getCRNums()))
            
        # Move the old token aside
        oldToken.move(replacedTokenDir)

        # copy this token to the old token's directory, changing the 
        # copy's baseName in the process
        newToken = self.magicCopy(oldTokenDir, sortedCRList, oldTokenBaseName)

        # Update times of the new token to match the old token
        newToken.matchTimes(oldToken)
        return newToken
    ## END def createReplacementToken(self, replacementPath)


    def findNewCRs(self, crList):
        """
        Returns a list of CRs from crList which are not in instance's
        list of CRs.
        """
        myCRNums = self.getCRNums()

        missList = []

        for cr in crList:
            if cr not in myCRNums:
                missList.append(int(cr))
                
        return  missList
    ## END matchCRList(self, crNums)


    def matchTimes(self, tokenToMatch):
        """
        Method sets Token instance file's atime and mtime attributes
        to match those of the Token instance passed as a paramter.
        Finally, method updated Token instance's member variables to
        reflect the change.
        """
        matchAtimes, matchMtimes = tokenToMatch.getFileTimes()

        # Make aure we have enough access and mod times for the
        # number of token files (in case enough new mods were added
        # to force creation of additional file(s)
        while len(matchAtimes) < len(self.tfList):
            matchAtimes.append(matchAtimes[-1] + 1)
        while len(matchMtimes) < len(self.tfList):
            matchMtimes.append(matchMtimes[-1] + 1)

        idx = 0
        for tf in self.tfList:
            os.utime(tf['path'], (matchAtimes[idx], matchMtimes[idx]))
        self.setFileTimes()
    ## END def matchDate(self, tokenToMatch)


    def magicCopy(self, toDir, crList, baseName):
        """
        Copies all files of this token to the specified directory.
        Renames the files in transit to match the CR ordering of the
        token it is replacing
        
        and returns a new token instance representing the copy
        """
        toDir = os.path.abspath(toDir)
        copyPathList = []

        newFileNames = formTokenNames(baseName, crList)

        idx = 0
        for newFileName in newFileNames:
            try:
                tf = self.tfList[idx]
            except IndexError:
                # More new file names than actual files. Just copy
                # the last file again (contents are to be identical)
                tf = self.tfList[-1] 

            toPath = os.path.join(toDir, newFileName) 

            shutil.copyfile(tf['path'], toPath)
            copyPathList.append(toPath)

            idx += 1

        return BranchToken(copyPathList)
    ## END copy(self, toDir)

    
    def remove(self):
        """
        Removes the token files represented by the Token instance
        """
        newTfList = []
        for tf in self.tfList:
            os.remove(tf['path'])
            tf['path'] = None
            newTfList.append(tf)
    
        self.tfList = newTfList
    ## END def remove(self)


    def move(self, newDir):
        """
        move the token's file(s) to the specified directory and update
        the member Token File list.

        Doesn't fail atomically right now
        """
        newDir = os.path.abspath(newDir)
        newTfList = []
        #print "elements in tfList: %s" %len(self.tfList)
        for tf in self.tfList:
            newPath = os.path.join(newDir, tf['fileName'])

            os.rename(tf['path'], newPath)
            tf['path'] = newPath
            newTfList.append(tf)

        self.tfList = newTfList
    ## END def rename(self, newPath)
        
## END class Token

class TokenException(Exception):
    def __init__(self, msg):
        self.args = msg
## END class TokenException

def formTokenNames(branchLabel, crList):
    """
    Forms multiple file names for a token by combining the list of
    CR's joined by an underbar plus '.branchLabel'

    Multiple names will be returned if the number of CRs exceeds the
    per-file limit.
    """
    global tokenCRLimit

    tokenFileNames = []
    
    myCRList = []
    for cr in crList:
        myCRList.append(str(cr))
    
    while len(myCRList) > 0:
         subSet = myCRList[:tokenCRLimit]
         myCRList = myCRList[tokenCRLimit:]

         # Generate the filename for the branch.
         crString = string.join(subSet, '_')
         fileName = '%s.%s' % (crString, branchLabel)

         tokenFileNames.append(fileName)
         
    return tokenFileNames
## END formTokenNames(branchLabel, crList)
 
def replaceToken(oldToken, newToken):
    """
    Calls newToken's replace method to move the oldToken (provided as argument)
    to the replacement dir and then move the newToken to the location of the
    oldToken
    """
    global replacedTokenDir

    replacementToken = newToken.createReplacementToken(oldToken)

    if replacementToken is None:
        msg = "Could not copy replacement token to %s" %oldToken.getPaths()
        raise TokenException(msg)
    
    replacementToken.matchTimes(oldToken)

## END replaceToken(oldToken, newToken)


def findTokensFromBranch(branch):
    """
    Searches the SCM directory for matches to this branch label.
    Groups identical labels by directory (assumed to be a unit if two
    files with the same branch segment are in the same directory)
    
    Returns a list of BranchTokens
    """
    branchPat = "\.%s($|-)" %branch
    branchRE = re.compile(branchPat)

    replacedRE=re.compile("/replace(d|ment)$")
    
    found = {}
    for root, dirs, files in os.walk(scm_rootDir):
        for file in files:
            if branchRE.search(file):
                if replacedRE.search(root):
                    # Filter out old tokens in the "replaced" directory
                    pass
                else:
                    if not found.has_key(root):
                        found[root] = []
                    path = os.path.join(root, file)
                    found[root].append(path)

    tokenList = []
    for rootPath in found.keys():
        tokenList.append(BranchToken(found[rootPath]))
        
    return tokenList
## END findTokensFromBranch(branch)



def updateToken(branch, newTokenPathList):
    
    newToken = BranchToken(newTokenPathList)

    foundTokens = findTokensFromBranch(branch)

    if len(foundTokens) < 1:
        msg =  "No token matching branch %s was found. Cannot continue replacement" %branch
        raise TokenException(msg)
    
    else:
        for oldToken in foundTokens:
            replaceToken(oldToken, newToken)

        newToken.remove()
## END def updateToken(branch, newTokenPath)
        
        
def usage(err=''):
     m =  '%s\n' %err
     m += 'Usage:\n'
     m += '    %s <branch name>  <new token pathname>\n' %sys.argv[0]
     return m
 ## END def usage(err)

def main_renamer():
    if len(sys.argv) >= 3:
        branchName = sys.argv[1]
        newTokenPathList = sys.argv[2:]
        updateToken(branchName, newTokenPathList)
    else:
        print usage()
        sys.exit(1)
## END main_renamer()


if __name__ == '__main__':
    main_renamer()

