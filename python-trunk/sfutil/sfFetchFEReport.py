#!/usr/bin/env python2.3
"""
Interactively log in and access the salesforce.com website in order to
down load a report as an excel spreadsheet and/or a .csv
"""

version = 1.0  # May 6, 2004. First FE report fetcher

import os
import re
import datetime
import cStringIO

import ConfigHelper
from sfWebScrape import WebScrape


### Global definitions ###
timestampFmt = '%Y%m%d-%H%M'
### END Global definitions ###

class FEReport(WebScrape):
    """
    Class to support the request and download of the FE Build report in
    both csv and Excel formats.
    """
    
    props = {}
    cookieJar = None
    urlOpener = None
    fileOpener = None
    backupPath = None

    report = cStringIO.StringIO()

    def __init__(self, props):
        self.props = props

        self.reportDate = {}
        self.startDate = None
        self.endDate = None

        uname = self.props.get('fereport','reportUname')
        encpw = self.props.get('fereport','reportEncPw')
        baseUrl = self.props.get('fereport','baseurl')

        reportId = self.props.get('fereport','reportId')
        self.reportFormURL = "%s/%s" %(baseUrl, reportId)
        
        self.__findReportDate()

        self.exportDir = self.props.get('fereport', 'exportDir')
        self.exportBaseFname = self.props.get('fereport', 'exportBaseFileName')

        # parent class init performs login
        WebScrape.__init__(self, props, uname, encpw)
    ## END __init__(self)

    def __findReportDate(self):
        """
        Private helper for setting the report date.
        """
        dateList = ConfigHelper.parseConfigList(self.props.get('fereport',
                                                               'dateList'))

        today = datetime.date.today()

        for dateStr in dateList:
            mon, day, year = dateStr.split('/')
            nextDate = datetime.date(int(year), int(mon), int(day))
            if nextDate >= today:
                break

        self.reportDate['mon'] = mon
        self.reportDate['day'] = day
        self.reportDate['year'] = year

        self.startDate = nextDate.strftime('%m/%d/%Y') 
        self.endDate = nextDate.strftime('%m/%d/%Y')
    ## END __findReportDate
            
    def dlCsvReport(self):
        """
        Request and save csv export of the report
        """
        requestElems = {'xf': 'csv'}
        requestElems.update(self.getReportConfig())
        
        csvdata = self.sendRequest(self.reportFormURL, self.fileOpener,
                                   requestElems, 'POST').read()

        self.writeExportFile('csv', csvdata)
    ## END dlCsvReport

    def dlXlsReport(self):
        """
        Request and save Excel export of the report
        """
        requestElems = {'xf': 'xls'}
        requestElems.update(self.getReportConfig())

        xlsdata = self.sendRequest(self.reportFormURL, self.fileOpener,
                                   requestElems, 'POST').read()

        self.writeExportFile('xls', xlsdata)
    ## END dlXlsReport

    def writeExportFile(self, fileExtension, fileData):
        """
        Write contents fileData to file at exportPath. Overwrite any
        file that may exist at that path. 
        """

        targetDate = "%s%s%s" %(self.reportDate['year'],
                                self.reportDate['mon'],
                                self.reportDate['day'])
        exportFname = "%s_%s.%s" %(self.exportBaseFname, targetDate,
                                   fileExtension)
        linkName = "%s.%s" %(self.exportBaseFname, fileExtension)

        exportPath = os.path.join(self.exportDir, exportFname)
        linkPath = os.path.join(self.exportDir, linkName)

        f = file(exportPath, 'w+')
        f.write(fileData)
        f.close()

        os.chown(exportPath, 30156, 101)
        os.chmod(exportPath, 0664) 

        os.remove(linkPath)
        os.symlink(exportPath, linkPath)
        
    ## END writeExportFile
        
    def getReportConfig(self):
        """
        Right now, tightly tied to just the one report (FE Build).
        In the future, parse the report page for a given report ID url
        to extract all the hidden form fields necessary to generate
        a given report.

        Returns a map of all the form values to post. 
        """
        requestElems = {'export': 'Export',
                        'enc': 'iso-8859-1',
                        
                        'colDt': '00N30000000eUbv',
                        'colDt_q':  'custom',
                        'colDt_y': '',
                        'sdate': self.startDate,
                        'edate': self.endDate,
                        'scope': 'organization',
                        'units': 'h',
                        
                        'uid': '00530000000buw3',
                        'rid': '',
                        'drill': '',
                        'format': 't',
                        'lcodes_0': 'CA,OW,CO,SU,00N30000000eUbv,AGE',
                        'break0': '00N30000000eUbv',
                        'break1': '',
                        'break2': '',
                        'break0a': '',
                        'break1a': '',
                        'brkord0': 'up',
                        'brkord1': 'up',
                        'brkord2': 'up',
                        'brkord0a': 'up',
                        'brkord1a': 'up',
                        'brkdat0': '0',
                        'brkdat1': '0',
                        'brkdat2': '0',
                        'brkdat0a': '0',
                        'brkdat1a': '0',
                        'co': '1',
                        'c_0': 'SU',
                        'c_1': 'CA',
                        'c_2': 'CO',
                        'c_3': 'AN',
                        'c_4': '00N30000000eUbv',
                        'cnt': '5',
                        'pc0': '00N30000000c9mM',
                        'pn0': 'sw',
                        'pv0': 'DFT,RTL',
                        'pc1': '',
                        'pn1': '',
                        'pv1': '',
                        'pc2': '',
                        'pn2': '',
                        'pv2': '',
                        'pc3': '',
                        'pn3': '',
                        'pv3': '',
                        'pc4': '',
                        'pn4': '',
                        'pv4': '',
                        'details': '',
                        'currency': '000',
                        'ct': 'none',
                        'ctitle': '',
                        'cp': 'b',
                        'cs': 'default',
                        'csize': '4',
                        'cfsize': '14',
                        'ctsize': '24',
                        'tfg': '16777215',
                        'fg': '16777215',
                        'bg1': '0',
                        'bg2': '100',
                        'bgdir': '2',
                        'l': '2',
                        'sal': 'no',
                        'rt': '10',
                        'sort': '',
                        'sortdir': '',
                        'v': '126',
                        'id': '00O30000000dYcR',
                        'cust_name': 'FE Group Build',
                        'cust_desc': '',
                        'owner': '00D3000000002QQ',
                        'entity': '',
                        'child': ''
                        }
        return requestElems




    def do(self):
        """
        The main flow for Backup
        """
        self.dlCsvReport()
        self.dlXlsReport()
    ## END do()


def main():
    # Fetch the config
    props = ConfigHelper.fetchConfig('conf/sfutil.cfg')
    
    report = FEReport(props)

    report.do()
## END main()    


if __name__=='__main__':
    main()
