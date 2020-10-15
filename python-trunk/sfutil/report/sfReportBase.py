import cStringIO
import time

class ReportBase:
    """
    Base class for common elements in generating periodic reports
    """

    def __init__(self, notifier, userId, contact):
        self.notifier = notifier
        self.props = notifier.props
        self.conn = notifier.conn
        self.userId = userId
        self.contact = contact

        self.subject = ""
        self.body = cStringIO.StringIO()
        self.sectionContentMap = {}

        self.ct_fld = self.conn.contactFields
    ## END __init__

    def generateReport(self):
        raise NotImplementedError
    ## END generateReport


    def generateReportFooter(self):
        ftr  = "\n\n--\n"
        ftr += "You may visit your salesforce.com contact record\n"
        ftr += "in order to change your report subscription settings:\n"
        ftr += "%s/%s\n" %(self.props.get('notify', 'baseurl'),
                         self.contact['id'])
        ftr += "\n"
        ftr += "If you have questions or comments about this report, please contact:\n"
        ftr += "\tsalesforce-support@molten-magma.com"
        return ftr
    ## END generateReportFooter(self)

    def getBody(self):
        return self.body.getvalue()
    ## END getBody(self)
    
    def getSubject(self):
        return self.subject
    ## END getSubject(self)

    def hasContent(self):
        """
        Looks at section content map. If any section generated
        has produced content, it's member in the section content map will be
        set to true.
        
        Method returns 'True' if ANY section has content,
        otherwise returns False.
        """
        return True in self.sectionContentMap.values()
    ## END hasContent
    
## END class ReportBase
