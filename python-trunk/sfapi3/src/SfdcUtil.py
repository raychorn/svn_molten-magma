"""
Various utility functions used throughout the package.
"""
import pprint
import types
import string

from baseconvert import *

##def listify(maybeList):
##    """
##    Ensure that input is a list, even if only a list of one item
##    """
##    definitelyList = []
##    if type(maybeList) == types.TupleType:
##        definitelyList = list(maybeList)
##    elif type(maybeList) != types.ListType:
##        definitelyList = list([maybeList,])
##    else:
##        definitelyList = maybeList
##        pass

##    return definitelyList
#### END listify

def uniqIdList(idList):
    """
    Takes a list of IDs, ensure they are all id18 (in case they are mixed)
    and cull any duplicates while retaining the order
    """
    uniqueIdList = []
    for candidateId in idList:
        candidateId = id15to18(candidateId)
        if candidateId not in uniqueIdList:
            uniqueIdList.append(candidateId)
            pass
        continue
    return uniqueIdList
## END uniqIdList
    

def id18to15(id18):
    """
    Truncate an 18 char sObject ID to the case-sensitive 15 char variety.
    """
    return id18[:15]
## END is18to15

def id15to18(id15):
    """
    Translate a 15 char sObject ID to the case-insensitive 18-char variety.
    """
    chunkSize = 5
    caseSafeExt = ''

    if len(id15) != 15:
        if len(id15) == 18:
            return id15
        id15 = id15[:15]
        
    idStr = id15
    while len(idStr) > 0:
        chunk = idStr[:chunkSize]
        idStr = idStr[chunkSize:]
        caseSafeExt += _convertChunk(chunk)

    return "%s%s" %(id15, caseSafeExt)
## END convertId15ToId18


def _convertChunk(chunk):
    """
    Used by convertId15ToId18. Not much use otherwise.
    """
    TRANSLATION_TABLE = string.ascii_uppercase + string.digits[:6]

    chunkBinList = []

    # for each character in chunk, give that position a 1 if uppercase,
    # 0 otherwise (lowercase or number)
    for character in chunk:
        if character in string.ascii_uppercase:
            chunkBinList.append('1')
        else:
            chunkBinList.append('0')

    chunkBinList.reverse() # flip it around so rightmost bit is most significant
    chunkBin = "".join(chunkBinList) # compress list into a string of the binary num
    chunkCharIdx = baseconvert(chunkBin, BINARY, DECIMAL) # convert binary to decimal
    return TRANSLATION_TABLE[int(chunkCharIdx)] # look it up in our table
## END convertChunk


