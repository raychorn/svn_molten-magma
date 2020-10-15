import datetime
import time
import os

from sfUtil import numToTxt

myTZ = 'US/Pacific'
dateTimeFmt = "%Y-%m-%dT%H:%M:%S.000Z"
def parseSfIsoStr(isoDate):
    """ Salesforce often returns ISO dates in UTC. This will parse it and
    return a UTC datetime """
    global myTZ
    global dateTimeFmt

    os.environ['TZ'] = 'UTC'
    time.tzset()

    timeStruct = time.strptime(isoDate, dateTimeFmt)
    dt = datetime.datetime(timeStruct[0], timeStruct[1], timeStruct[2],
                           timeStruct[3], timeStruct[4], timeStruct[5],
                           timeStruct[6])
    
    os.environ['TZ'] = myTZ
    time.tzset()

    return dt


def dayNumToTxt(inTimedelta):
    numDays = inTimedelta.days

    dayTxt = numToTxt(numDays)
    
    if numDays != 1:
        dayTxt += ' days'
    else:
        dayTxt += ' day'
        pass

    return dayTxt
## END dayNumToTxt
