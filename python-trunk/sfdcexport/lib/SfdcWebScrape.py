"""
Class with methods to support logging into the salesforce.com website
in order to support operations that the sforce API does not yet support.

Author:		Kevin Shuk <kshuk@molten-magma.com>
Date:		Mar 14, 2004
Copyright: 	(c) 2004 - 2005, Kevin Shuk and Magma Design Automation, Inc.
                All Rights Reserved
"""

ident = "$ID: $"

import re
import urllib
import urllib2

from Properties import Properties
props = Properties()

# FIXME:
# python 2.4 includes the "cookielib" which is, essentially ClientCookie
# as I don't use python 2.4, I can't verify compatibility, but it'd be nifty
# to have this code work with either ClientCookie or cookielib (if present).
# Get ClientCookie 1.0.3 or later from:
#  http://wwwsearch.sourceforge.net/ClientCookie/
import ClientCookie 

class SfdcWebScrape:
    
    def __init__(self, uname, pw):

        self.loggedIn = False
        self.cookieJar = ClientCookie.CookieJar()

        # Build a functional opener for regular pages
        # Uses class-persistent cookie store
        # can seek() on the response object
        # Responds correctly to refresh directives, opening target page
        # automagically
        self.urlOpener = ClientCookie.build_opener(ClientCookie.HTTPCookieProcessor(self.cookieJar),
                                                   ClientCookie.SeekableProcessor,
                                                   ClientCookie.HTTPEquivProcessor,
                                                   ClientCookie.HTTPRefreshProcessor,
                                                   ClientCookie.HTTPRefererProcessor)

        # Build a special opener for (binary) files
        # Uses class-persistent cookie store
        # can seek() on the response object
        # Cannot use HTTPEquivProcessor as HTMLParser will barf reading the
        # binary file data.
        self.fileOpener = ClientCookie.build_opener(ClientCookie.HTTPCookieProcessor(self.cookieJar),
                                                    ClientCookie.SeekableProcessor,
                                                    ClientCookie.HTTPRefererProcessor)

        if self.login(uname, pw):
            self.loggedIn = True
            pass
    ## END __init__

    def login(self, uname, pw):
        """
        Attempts a login page authentication with sfdc.

        Parameters:
        uname - sfdc username
        pw - unencoded sfdc password

        Returns:
        True if login was successful, otherwise False
        
        """
        loginElems = {'useSecure':'null',
                      'username': uname,
                      'un': uname,
                      'pw': pw}

        response = self.sendRequest(props.loginUrl, self.urlOpener,
                                    params=loginElems, method='POST')
        
        resultHdr = "%s" %response.info()

        loginSucceedPat = "^Set-Cookie:\s+oinfo="
        loginSuccess = False
        if re.search(loginSucceedPat, resultHdr, re.M|re.I) is not None:
            loginSuccess = True
            pass

        return loginSuccess
    ## END login


    def sendRequest(self, URL, opener=None, params=None, method='GET'):
        """
        Executes a request and returns the response.

        Parameters:
        URL - the URL to fetch
        opener - urrlib2 (by way of ClientCookie) opener object. Two are
                 available right now: urlOpener for regular HTML pages
                 and fileOpener for downloading files (inages, zips, etc.)
        params - dictionary of query parameters to send along with the
                 request
        method - how to send the query parameters with the request GET or POST
        
        Returns:
        file-like object that is the return of the urlOpener object open call

        """
        if opener is None:
            opener=self.urlOpener
            pass
        
        if params is not None:
            queryData = urllib.urlencode(params)
            pass
        
        if params is None:
            request = urllib2.Request(URL)
        elif method == 'GET':
            request = urllib2.Request("%s?%s" %(URL, queryData))
        else:  # use POST
            request = urllib2.Request(URL, queryData)
            pass
        
        return opener.open(request)
    ## END sendRequest

    pass
## END class SfdcWebScrape
