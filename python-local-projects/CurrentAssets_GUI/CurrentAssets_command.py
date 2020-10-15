import string

import os, sys
import time
import traceback

from vyperlogix import oodb

from vyperlogix.hash import lists

from vyperlogix.daemon.daemon import Log

from vyperlogix import misc
from vyperlogix.misc import _utils
from vyperlogix.lists.ListWrapper import ListWrapper
from vyperlogix.misc import threadpool

from vyperlogix.misc import ObjectTypeName

from vyperlogix.sf.hostify import hostify

from vyperlogix.parsers.CSV import CSV

from vyperlogix.wx.PopUpDialog import wx_PopUp_Dialog

import utils

__competitors_list_ = '''
 1. Email greater than  
 2. Email does not contain magma 
 3. Email Opt Out equals False 
 4. Email does not contain 0-in.com,acadcorp.com,accelchip.com,eesof.tm.agilent.com,aldec.com,ammocore.com,anasift.com,ansoft.com,apache-da.com,aplac.com,appwave.com,apriotech.com,aptix.com,artisan.com,athenads.com,atrenta.com,avertec.com,axiom-da.com,axysdesign.com,azuro.com,beachsolutions.com,berkeley-da.com,bindkey.com,blazedfm.com,bluepearlsoftware.com,bluespec.com,brion.com,cadence.com,calypto.com,carbondesignsytems.com,softwaredrivendesign.com,catalyticinc.com,celoxica.com,certess.com,chipmd.com,chipvision.com,ciranova.com,concept.de,coware.com,criticalblue.com,dafca.com,denalisoft.com,doulos.com,eecad.com,edxact.com,e-tools.com,dataxpress.com,elementcxi.com,esterel-technologies.com,eveteam.com,fintronic.com,fortedesignsystems.com,ftlsystems.com,genesystest.com,gigaic.com,ggtcorp.com,gradient-da.com,icmanage.com,icinergy.com,imperas.com,incentia.com,interrasystems.com,jasper-da.com,jedatechnologies.net,knowlent.com,legenddesign.com 
 5. Email does not contain libtech.com,logicvision.com,lorentzsolution.com,mri-nyc.com,mathworks.com,matrixone.com,mentor.com,mips.com,nangate.com,nannor.com,nascentric.com,novas.com,obsidiansoft.com,oea.com,orora.com,pdf.com,pontesolutions.com,prolificinc.com,pulsic.com,prosilog.com,pyxis.com,realintent.com,reshape.com,sagantec.com,sandwork.com,sequencedesign.com,sierrada.com,sigmac.com,sigrity.com,sicanvas.com,siliconds.com,sidimensions.com,silvaco.com,softjin.com,spiratech.com,sd.com,synappscorp.com,synchronicity.com,synfora.com,synopsys.com,synplicity.com,syntest.com,syntricity.com,takumi-tech.com,tharas.com,tenison.com,tensilica.com,terasystems.com,transeda.com,tuscanyda.com,vastsystems.com,verific.com,verisity.com,viragelogic.com,virtual-silicon.com,xpedion.com,yxi.com,zenasis.com 
 6. Last Name does not contain x-,-x 
'''
_symbol_competitors_fname_ = 'competitors.txt'

is_checkbox_value_true = lambda value:str(value).lower() in ['true','1','yes','ok']

_info_Copyright = "(c). Copyright %s, Magma Design Automation" % (_utils.timeStampLocalTime(format=_utils.formatDate_YYYY()))

_info_site_address = 'www.moltenmagma.com'

__copyright__ = """[**], All Rights Reserved.

THE AUTHOR MAGMA DESIGN AUTOMATION DISCLAIMS ALL WARRANTIES WITH REGARD TO
THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS, IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL,
INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING
FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION
WITH THE USE OR PERFORMANCE OF THIS SOFTWARE !

USE AT YOUR OWN RISK."""

__copyright__ = __copyright__.replace('[**]',_info_Copyright)

_smtp_server_address = 'mailhost.moltenmagma.com:25'

_info_root_folder = 'c:\\'
wildcard_csv = "CSV File (*.csv)|*.csv"

_symbol_data_cleaned_fname = 'data_cleaned.csv'

_symbol_username = 'username'
_symbol_server_end_point = 'server_end_point'
_symbol_specific_end_point = 'specific_end_point'

l_domain_names = ['.moltenmagma.com']
utils.l_domains = l_domains = ['magma']
utils.l_domain_users = l_domain_users = [r'magma\rhorn']

from vyperlogix.products import data as products_data
_data_path_prefix = products_data._data_path_prefix

dbx_name = lambda name:oodb.dbx_name(name,_data_path)

_csv_model = CSV()

_isRunning = True

_thread_Q = threadpool.ThreadQueue(500)

from vyperlogix.mixins.magma.CurrentAssetsProcess_mixin import CurrentAssetsProcessMixin

class MainCommand(CurrentAssetsProcessMixin):
    def __init__(self, args):
	self.CurrentAssetsProcessMixin_init()
	self._csv_model = _csv_model
	self._log_path = _log_path
	
	self.args = args
	
	self.log = sys.stdout
	
        from vyperlogix.wx.pyax.SalesForceLoginModel import SalesForceLoginModel
        self.sf_login_model = SalesForceLoginModel(username=self.args.username,password=self.args.password,callback_developers_check=utils.is_running_securely_for_developers)
	
	self.__login_dialog__ = self
	
	self.competitors_list = []

        self.__contacts__ = []
	
	if (not _utils._isComputerAllowed) or (not _is_running_securely):
	    info_string = 'Sorry but you cannot use this program at this time due to Security Concerns.\nPlease try back later from safely behind the Magma Firewall as a user on the Magma domain.'
	    print >>sys.stderr, info_string
	else:
	    self.sf_login_model.isStaging = False
	    self.sf_login_model.perform_login(end_point='https://na6.salesforce.com/services/Soap/u/14.0')
	    if (self.sf_login_model.isLoggedIn):
		self.onProcess()
		self._doAfterExtractionProcessCompleted()
		self._doUploadToSalesForce()
		self.theExtractionProcessCompleted()
		sys.exit(1)
	
    def appendText(self,msg):
	print >>sys.stdout, msg
	
    def append_to_message_Q(self,msg):
	self.appendText(msg)
    
    def theExtractionProcessCompleted(self):
	info_string = '''The data has been extracted. Enjoy !'''
	print >>sys.stdout, info_string
    
    def onProcess(self):
	isError = False
	self.__competitors_list = self.competitors_list
	try:
	    if (len(self.last_error) > 0):
		isError = True
		print >>sys.stderr, self.last_error
	except Exception, details:
	    info_string = _utils.formattedException(details=details)
	    print >>sys.stderr, info_string
	if (not isError):
	    self.backgroundProcess(self)
    
def main(argv=None):
    global _data_path, _log_path
    
    d_args = lists.HashedLists2()

    is_command_line = ObjectTypeName.typeClassName(argv).find('misc.Args.Args') > -1
    if argv is None:
        argv = sys.argv
    else:
	_isVerbose = False
	try:
	    if _argsObj.booleans.has_key('isVerbose'):
		_isVerbose = _argsObj.booleans['isVerbose']
	except Exception, details:
	    info_string = _utils.formattedException(details=details)
	    print >>sys.stderr, info_string
	d_args['isVerbose'] = _isVerbose

	_isHelp = False
	try:
	    if _argsObj.booleans.has_key('isHelp'):
		_isHelp = _argsObj.booleans['isHelp']
	except Exception, details:
	    info_string = _utils.formattedException(details=details)
	    print >>sys.stderr, info_string
	d_args['isHelp'] = _isHelp
	    
	_isDebug = False
	try:
	    if _argsObj.booleans.has_key('isDebug'):
		_isDebug = _argsObj.booleans['isDebug']
	except Exception, details:
	    info_string = _utils.formattedException(details=details)
	    print >>sys.stderr, info_string
	d_args['isDebug'] = _isDebug

	_isNopsyco = False
	try:
	    if _argsObj.booleans.has_key('isNopsyco'):
		_isNopsyco = _argsObj.booleans['isNopsyco']
	except Exception, details:
	    info_string = _utils.formattedException(details=details)
	    print >>sys.stderr, info_string
	d_args['isNopsyco'] = _isNopsyco

	_username = ''
	try:
	    if _argsObj.arguments.has_key('username'):
		_username = _argsObj.arguments['username']
	except Exception, details:
	    info_string = _utils.formattedException(details=details)
	    print >>sys.stderr, info_string
	d_args['username'] = _username
	
	_password = ''
	try:
	    if _argsObj.arguments.has_key('password'):
		_password = _argsObj.arguments['password']
	except Exception, details:
	    info_string = _utils.formattedException(details=details)
	    print >>sys.stderr, info_string
	d_args['password'] = _password
	
	_token = ''
	try:
	    if _argsObj.arguments.has_key('token'):
		_token = _argsObj.arguments['token']
	except Exception, details:
	    info_string = _utils.formattedException(details=details)
	    print >>sys.stderr, info_string
	d_args['token'] = _token
	
    from vyperlogix.classes.SmartObject import SmartObject
    smart_args = SmartObject(d_args)

    _data_path = _utils.appDataFolder(prefix=_utils.getProgramName())
    _utils._makeDirs(_data_path)
    
    log_path = os.path.dirname(sys.argv[0])
    _log_path = _utils.safely_mkdir(fpath=log_path,dirname='logs')

    if (not _isBeingDebugged):
	_stdOut = open(os.sep.join([log_path,'stdout.txt']),'w')
	sys.stdout = Log(_stdOut)

    _stdErr = open(os.sep.join([log_path,'stderr.txt']),'w')
    sys.stderr = Log(_stdErr)

    try:
	if (is_command_line):
	    cmd = MainCommand(smart_args)
    except Exception, exception:
	type, value, stack = sys.exc_info()
	formattedBacktrace = ''.join(traceback.format_exception(type, value, stack, 5))
	info_string = 'An unexpected problem occurred:\n%s' % (formattedBacktrace)
	print >>sys.stderr, info_string

def exception_callback(sections):
    _msg = 'EXCEPTION Causing Abend.\n%s' % '\n'.join(sections)
    print >>sys.stdout, _msg
    print >>sys.stderr, _msg
    sys.exit(1)

if __name__ == '__main__':
    _isBeingDebugged = _utils.isBeingDebugged
    
    if (not _isBeingDebugged):
	from vyperlogix.handlers.ExceptionHandler import *
	excp = ExceptionHandler()
	excp.callback = exception_callback

    from vyperlogix.misc._psyco import *
    importPsycoIfPossible(func=main,isVerbose=True)

    _is_running_securely = utils.is_running_securely()
    _utils.isComputerAllowed(l_domain_names)

    from vyperlogix.misc import Args
    from vyperlogix.misc import PrettyPrint

    def ppArgs():
	pArgs = [(k,args[k]) for k in args.keys()]
	pPretty = PrettyPrint.PrettyPrint('',pArgs,True,' ... ')
	pPretty.pprint()

    args = {'--help':'show some help.',
	    '--verbose':'output more stuff.',
	    '--debug':'debug some stuff.',
	    '--nopsyco':'do not load Psyco when this option is used.',
	    '--staging':'use the staging server rather than production otherwise use production.',
	    '--username=?':'username, use as-needed.',
	    '--password=?':'password, use as-needed.',
	    '--token=?':'login token, use as-needed.',
	    }
    _argsObj = Args.Args(args)

    main(_argsObj)
