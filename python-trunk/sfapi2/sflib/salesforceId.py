#!/usr/bin/env python2.3
"""
Simple function that can convert a 15 character salesforce ID string
to the case-safe 18-character version
"""

import string
import types
import sys


TRANSLATION_TABLE = string.ascii_uppercase + string.digits[:6]


def convertId15ToId18(id15):
    
    validLen = 15
    chunkSize = 5
    caseSafeExt = ''
    
    if id15 > validLen:
        id15 = id15[:validLen]
        
    if len(id15) != validLen:
        #error case
        msg = "Parameter id15 must be exactly %s characters long" %validLen
        raise ValueError, msg
        pass

    idStr = id15
    while len(idStr) > 0:
        chunk = idStr[:chunkSize]
        idStr = idStr[chunkSize:]
        caseSafeExt += convertChunk(chunk)

    return "%s%s" %(id15, caseSafeExt)
## END convertId15ToId18


def convertChunk(chunk):
    """
    Used by convertId15ToId18
    """
    global BINARY, DECIMAL
    global TRANSLATION_TABLE
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


########################################################################
# base converter utility function - may go to live with other utility
# classes someday...
########################################################################

BASE2  = string.digits[:2]
BINARY = BASE2

BASE8  = string.octdigits
OCTAL = BASE8

BASE10 = string.digits
DECIMAL = BASE10

BASE16 = string.digits + string.ascii_uppercase[:6]
HEX = BASE16

def baseconvert(number,fromdigits,todigits):
    if str(number)[0]=='-':
        number = str(number)[1:]
        neg = True
    else:
        neg = False

    # make an integer out of the number
    x=long(0)
    for digit in str(number):
       x = x*len(fromdigits) + fromdigits.index(digit)
    
    # create the result in base 'len(todigits)'
    res=''
    while x>0:
        digit = x % len(todigits)
        res = todigits[digit] + res
        x /= len(todigits)
    if len(res) == 0:
        res = 0
    if neg:
        res = "-%s" %res

    return res
## END baseconvert


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Usage: salesforceId.py <15 character SF ID>"
        sys.exit(1)
        
    print convertId15ToId18(sys.argv[1])

