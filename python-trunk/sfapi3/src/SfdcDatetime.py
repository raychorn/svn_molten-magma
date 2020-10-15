""" Dealing with dates, times and timezones  programmatically is a beast!
Let's draw a line in the sand with what we can rely upon:
sforce always returns dates and datetimes as ISO format in UTC
userinfo provides the user's timezone.

What I'm not sure of, but is easily provable:
sforce expects times in inserts/updates as UTC?
sforce expects times in queries as UTC?

What is best avoided:
relying upon the local machine's idea of localtime.

"""
import os
import time
from datetime import datetime, timedelta
from pytz import timezone

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
DATE_FORMAT = '%Y-%m-%d'


UTC = timezone('UTC')


class SfdcDatetime(datetime):
    """ Specialized subclass of datetime to support the date or datetime
    format used by Salesforce.com. """

    def fromSfIso(klass, sfDatetimeString):
        """ construct an SfdcDatetime instance from a datetime string
        in UTC fetched from sfdc """
        global UTC
        global DATETIME_FORMAT
        
        timestamp = sfDatetimeString.split('.', 1)[0]
        timestruct = time.strptime(timestamp, DATETIME_FORMAT)

        return SfdcDatetime(timestruct[0], # year
                            timestruct[1], # month
                            timestruct[2], # day
                            timestruct[3], # hour
                            timestruct[4], # minute
                            timestruct[5], # second
                            0, # microsecond
                            UTC)
    fromSfIso = classmethod(fromSfIso)



