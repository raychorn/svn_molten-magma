import sys
import pprint
import urlparse
import StringIO, os, getopt
import copy, re
from ZSI import wsdl2python
from ZSI.wstools.TimeoutSocket import TimeoutError
from ZSI.wstools.WSDLTools import WSDLReader
from ZSI.wstools.Utility import HTTPResponse
from optparse import OptionParser

class Wsdl2pythonWrap:
    """
    """
    def __init__(self, path, output):
        """ create basic object """
        self.path = path
        self.output_path = output

    def generate_code(self):
        try:
            if self.path[:7] == 'http://':
                wsdl = WSDLReader().loadFromURL(self.path)
            else:
                wsdl = WSDLReader().loadFromFile(self.path)
        except TimeoutError:
            print "connection timed out"
            sys.stdout.flush()
            return 0
        except HTTPResponse:
            print "initial connection with service problem"
            sys.stdout.flush()
            return 0
        except:
            self.path = self.path + ": load failed, unable to start"
            raise
        codegen = wsdl2python.WriteServiceModule(wsdl)
        f_types, f_services = codegen.get_module_names()
        hasSchema = len(codegen._wa.getSchemaDict())
        
        testDir = self.output_path

        if hasSchema:
            strFile = StringIO.StringIO()
            typesFileName = f_types + ".py"
            testdiff = TestDiff(self, testDir, typesFileName)
            try:
                codegen.write_service_types(f_types, strFile)
            except:
                self.path = self.path + ": write_service_types"
                raise
            if strFile.closed:
                print "trouble"
            testdiff.failUnlessEqual(strFile)
            strFile.close()

        strFile = StringIO.StringIO()
        servicesFileName = f_services + ".py"
        testdiff = TestDiff(self, testDir, servicesFileName)
        try:
            signatures = codegen.write_services(f_types,
                             f_services, strFile, hasSchema)
        except:
            self.path = self.path + ": write_services"
            raise
        testdiff.failUnlessEqual(strFile)
        strFile.close()
    
    def failUnlessEqual(self, origLine, testLine):
        """ just print out differences """
        print 'The following lines are different Org: %s New: %s' %(origLine, testLine)

class TestDiff:
    """TestDiff encapsulates comparing a string or StringIO object
       against text in a test file.  Test files are located in a
       subdirectory of the current directory, named diffs if a name
       isn't provided.  If the sub-directory doesn't exist, it will
       be created.  If a single test file is to be generated, the file
       name is passed in.  If not, another sub-directory is created
       below the diffs directory, in which a file is created for each
       test.

       The calling unittest.TestCase instance is passed
       in on object creation.  Optional compiled regular expressions
       can also be passed in, which are used to ignore strings
       that one knows in advance will be different, for example
       id="<hex digits>" .

       The initial running of the test will create the test
       files.  When the tests are run again, the new output
       is compared against the old, line by line.  To generate
       a new test file, remove the old one from the sub-directory.
       The tests also allow this to be done automatically if the
       -d option is passed in on the command-line.
    """

    def __init__(self, testInst, testFilePath='diffs', singleFileName='', deleteFile=False,
                *ignoreList):
        self.diffsFile = None
        self.testInst = testInst
        self.origStrFile = None
        self.expectedFailures = copy.copy(ignoreList)

        if not os.path.exists(testFilePath):
            os.mkdir(testFilePath)

        if not singleFileName:
            #  if potentially multiple tests will be performed by
            #  a test module, create a subdirectory for them.
            testFilePath = testFilePath + os.sep + testInst.__class__.__name__
            if not os.path.exists(testFilePath):
                os.mkdir(testFilePath)

                # get name of test method, and name the diffs file after
                # it
            f = inspect.currentframe()
            fullName = testFilePath + os.sep + \
                       inspect.getouterframes(f)[2][3] + '.diffs'
        else:
            fullName = testFilePath + os.sep + singleFileName

        if deleteFile:
            try:
                os.remove(fullName)
            except OSError:
                print fullName

        try:
            self.diffsFile = open(fullName, "r")
            self.origStrFile = StringIO.StringIO(self.diffsFile.read())
        except IOError:
            try:
                self.diffsFile = open(fullName, "w")
            except IOError:
                print "exception"


    def failUnlessEqual(self, buffer):
        """failUnlessEqual takes either a string or a StringIO
           instance as input, and compares it against the original
           output from the test file.  
        """
            # if not already a string IO 
        if not isinstance(buffer, StringIO.StringIO):
            testStrFile = StringIO.StringIO(buffer)
        else:
            testStrFile = buffer
            testStrFile.seek(0)

        hasContent = False
        if self.diffsFile.mode == "r":
            for testLine in testStrFile:
                origLine = self.origStrFile.readline() 
                if not origLine:
                    break
                else:
                    hasContent = True

                    # take out expected failure strings before
                    # comparing original against new output
                for cexpr in self.expectedFailures:
                    origLine = cexpr.sub('', origLine)
                    testLine = cexpr.sub('', testLine)

                if origLine != testLine:
                    self.testInst.failUnlessEqual(origLine, testLine)
            return

        if (self.diffsFile.mode == "w") or not hasContent:
                # write new test file
            for line in testStrFile:
                self.diffsFile.write(line)

        self.diffsFile.close()

def createPythonModules(wsdlPath, output):
    """ """
    w2p = Wsdl2pythonWrap(wsdlPath, output)
    w2p.generate_code()
    print '%s' %w2p
    

def usage(err=''):
    """  Prints the Usage() statement for the program    """
    m = '%s\n' %err
    m += '  Default usage is to rebuild the python base code from a wsdl.\n'
    m += ' '
    m += '    genBase  <wsdl path> \n'
    m += '      or\n'
    m += '    genBase -b <base name> -p <output_path>  <wsdl path> \n'
    return m

version = '1.0'

def main_CL():
    """ Command line parsing and and defaults methods
    """
    parser = OptionParser(usage=usage(), version='%s'%version)
    parser.add_option("-b", "--base",  dest="base",   default="service",  help="base string to add to module name.")
    parser.add_option("-p", "--path",  dest="path",  default="generated",    help="Path to output of python modules.")
    parser.add_option("-d", "--debug", dest='debug', action="count",help="The debug level, use multiple to get more.")
    (options, args) = parser.parse_args()
    if options.debug > 1:
        print ' base    %s' %options.base
        print ' path    %s' %options.path
        print ' args:   %s' %args
    if len(args) > 0: 
        wsdlPath = args[0]
        createPythonModules(wsdlPath, options.path)
    else:
        print '%s' %usage()

if __name__ == "__main__":
    main_CL()

