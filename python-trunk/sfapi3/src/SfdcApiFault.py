import new

from SOAPpy import Types
import PysfdcLogger, logging
log = logging.getLogger('pysfdc.fault')

FaultTypeMap = {}

class SfdcApiFault(Exception):
    """ Abstract base class for all sforce API faults """
    _apiFaultType = None

    def __init__(self, message=''):
        """
        Not called directly to instantiate salesforce objects - called by
        other static constructor methods
        """
        if self._apiFaultType is None:
            raise NotImplemetedError
        
        self.message = message
        
        return
    ## END __init__

    def __str__(self):
        return self.message
    ## END __str__

    pass
## END SfdcApiFault

def SfdcApiFaultFactory(apiFaultType):
    global FaultTypeMap
    if not FaultTypeMap.has_key(apiFaultType):
        faultClass = new.classobj(apiFaultType, (SfdcApiFault,), {})
        faultClass._apiFaultType = apiFaultType
        FaultTypeMap[apiFaultType] = faultClass
        pass
    return FaultTypeMap.get(apiFaultType)
## END SfdcApiFaultFactory

def parseFaultObject(faultObj):
    """
    Parse a fault object to return the raw componets as a dict
    """
    faultDict = {}
    
    # unpack the fault struct
    faultObjDict = faultObj._asdict()
    if type(faultObjDict.get('detail')) == type(Types.structType()):
        faultDetailDict = faultObjDict['detail']._asdict()
        faultDict = faultDetailDict['fault']._asdict()
    else:
        faultDict = faultObjDict
        pass
    
    return faultDict
## END parseFaultObject

def handleFault(fault):
    """
    Unpacks data of fault thrown from an sforce SOAP call and
    create an appropriately typed SfdcApiFault exception.

    Calling method decides whether to raise the exception or not
    """
    faultTypeStr = "PySfdc_Unknown_Fault"
    faultMsg = "PySfdc cannot parse the fault: %s" %fault
    
    faultData = parseFaultObject(fault)
    if faultData.has_key('exceptionCode'):
        faultTypeStr = faultData['exceptionCode']
        faultMsg = faultData.get('exceptionMessage')
    elif faultData.has_key('faultcode'):
        faultTypeStr = faultData.get('faultcode')
        faultMsg = faultData.get('faultstring')
        pass
        
    faultClass = SfdcApiFaultFactory(faultTypeStr)
    fault = faultClass(faultMsg)
    
    return fault
## END handleFault
