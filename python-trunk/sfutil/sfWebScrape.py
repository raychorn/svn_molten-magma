#!/usr/bin/env python2.3
"""
Class with methods to support logging into the salesforce.com website
in order to support operations that the sforce API does not yet support.
"""

import re
import urllib
import urllib2
import base64
import ClientCookie # must be installed: http://wwwsearch.sourceforge.net/ClientCookie/

class WebScrape:


    def __init__(self, props, uname, encpw):

        self.loggedIn = False
        self.cookieJar = ClientCookie.CookieJar()

        self.props = props

        self.uname = uname
        self.encpw = encpw

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

        if self.sfLogin():
            self.loggedIn = True
    ## END __init__(self)

    def sfLogin(self):
        uname = self.uname
        passwd = base64.decodestring(self.encpw)
        #passwd = "WrongPasswd"
        
        loginURL = self.props.get('webscrape','loginURL')
        #print loginURL
        
        loginElems = {'useSecure':'null',
                      'username': uname,
                      'un': uname,
                      'pw': passwd}

        response = self.sendRequest(loginURL, self.urlOpener,
                                    params=loginElems, method='POST')
        
        resultHdr = "%s" %response.info()
        #print response.read()
        loginSucceedPat = "^Set-Cookie:\s+oinfo="
        if re.search(loginSucceedPat, resultHdr, re.M|re.I) is not None:
            return True
        else:
            return False
    ## END sfLogin(self)


    def sendRequest(self, URL, opener=None, params=None, method='GET'):
        """
        Executes a request and returns the response.

        URL - the URL to fetch
        opener - urrlib2 (by way of ClientCookie) opener object. Two are
                 available right now: urlOpener for regular HTML pages
                 and fileOpener for downloading files (inages, zips, etc.)
        params - dictionary of query parameters to send along with the
                 request
        method - how to send the query parameters with the request GET or POST
        """
        if opener is None:
            opener=self.urlOpener
        
        if params is not None:
            queryData = urllib.urlencode(params)

        if params is None:
            request = urllib2.Request(URL)
        elif method == 'GET':
            request = urllib2.Request("%s?%s" %(URL, queryData))
        else:  # use POST
            request = urllib2.Request(URL, queryData)

        response = opener.open(request)

        return response
    ## end sendRequest
