import cStringIO
import traceback

from sfConstant import *

class ReportSection:

    userCache = {}

    def __init__(self, sfTool):
        #self.props = notifier.props
        self.sfTool = sfTool

        self.header = None
        self.footer = None
        self.section = cStringIO.StringIO()
        self.hasContentFlag = False

        self.baseUrl = self.sfTool.sfc.get('main', 'sf_base_url')
    ## END __init__(self)

    def hasContent(self):
        """ Accessor to hasContentFlag """
        return self.hasContentFlag
    ## end hasContent
        
    def getSection(self):
        if len(self.section.getvalue()) == 0:
            self.generateSection()
        return self.section.getvalue()
    ## END getSection(self)


    def fmtSecHeader(self):
        hdr = ''
        if self.header is not None:
            hdr  = "-"*50 + "\n"
            hdr += "%s\n" %self.header
            hdr += "-"*50 + "\n\n"
        return hdr
    ## END fmtSecHeader(self):


    def fmtSecFooter(self):
        ftr = ''
        if self.footer is not None:
            ftr  = "%s\n" %self.footer
        ftr += '\n\n'
        return ftr
    ## END fmtSecFooter(self):


    def fmtSectionError(self, error):
        msg  = "The following error occurred while generating this section:\n"
        msg += "\t%s" %error
        return msg
    ## END  fmtSectionError(self, error)

 
    def generateSection(self):
        self.section.write(self.fmtSecHeader())

        body = ''
        try:
            body = self.buildSecBody()
        except Exception, e:
            body = self.fmtSectionError(e)
            traceback.print_exc()
            self.hasContentFlag = True # We want the error section to go out
            self.sfTool.setLog("Exception caught generating report: %s" %e,
                               'error')

        self.section.write(body)
            
        self.section.write(self.fmtSecFooter())
    ## END generateSection(self)


    def buildSecBody(self):
        # abstract method - subclasses must provide
        raise NotImplementedError
    ## END buildSecBody(self)


    def lookupUserByIdCache(self, userId):
        """
        Lookup a single user by ID using a simple cache map to prevent
        multiple fetched of the same user record.
        """
        if not self.userCache.has_key(userId):
            userList = self.sfTool.retrieve([userId], USER_OBJ)
            if userList not in BAD_INFO_LIST:
                self.userCache[userId] = userList[0]
            else:
                self.userCache[userId] = None

        return self.userCache[userId]
    ## END lookupUserByIdCache
