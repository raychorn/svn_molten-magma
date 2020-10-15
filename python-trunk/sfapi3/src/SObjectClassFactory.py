import types

from SOAPpy.Types import stringType

from SObjectCrudBase import SObjectCrudBase
from RawSfdcConnection import NoConnectionError

from SObjectType import verifySObjectType

import PysfdcLogger, logging
log = logging.getLogger('pysfdc.sobject')
    
class SObjectClassFactory(type):
    """
    Class factory for all Salesforce.com objects which inherit sObjectCrudBase
    """
    sObjectTypeMap = {}
    
    def __new__(klass, cxn, sObjectTypeStr, baseArg=[], attrArg={}):
        listBase = klass.procBases(baseArg, sObjectTypeStr)
        mapAttr = klass.procAttrs(attrArg)

        verifySObjectType(cxn, sObjectTypeStr)

        if not klass.sObjectTypeMap.has_key(sObjectTypeStr):
            newclass = type.__new__(klass, sObjectTypeStr, listBase, mapAttr)
            newclass.cxn = cxn
            # fetch and install the metadata for this sObjectType
            newclass._sObjectTypeStr = sObjectTypeStr
            newclass._metadata = newclass.describeSObject()

            newclass._sObjectTypeStr = newclass._metadata.name
            
            # FIXME: may want to determine the namespace attr programmatically later, but for now, this works.
            newclass._sObjectSoapType = stringType(newclass._sObjectTypeStr, name='type', typed=False, attrs={'xmlns': 'urn:sobject.partner.soap.sforce.com'})

            # install a custom logger for the sobject type
            newclass.log = logging.getLogger('pysfdc.sobject.%s' %sObjectTypeStr)
            
            # cache the class
            klass.sObjectTypeMap[sObjectTypeStr] = newclass
            pass
        return klass.sObjectTypeMap.get(sObjectTypeStr)
    ## END __new__


    def __init__(klass, cxn, sObjectTypeStr, baseArg=[], attrArg={}):
        listBase = klass.procBases(baseArg, sObjectTypeStr) 
        mapAttr = klass.procAttrs(attrArg)
        
        super(SObjectClassFactory, klass).__init__(sObjectTypeStr,
                                                   listBase, mapAttr)
        return
    ## END __init__

    
    def procBases(baseArg, sObjectTypeStr):
        """ Accept either a list, tuple or single base class. Return a tuple
        that contains at least SfCrudBase as a blase class. """
        listBase = []
        if type(baseArg) == types.TupleType:
            listBase.extend(baseArg)
        elif type(baseArg) != types.ListType:
            listBase.append(baseArg)
            pass

        # Ensure that we always include SfCrudBase as a base class
        if SObjectCrudBase not in listBase:
            listBase.append(SObjectCrudBase)
            pass

        # if we're creating a lead, include lead-specific mixin base
        if sObjectTypeStr.lower() == 'lead':
            listBase.append(SObjectLeadMixin)
            pass
        
        return tuple(listBase)
    procBases = staticmethod(procBases)
    ## END procBases

      
    def procAttrs(klass, attrArg):
        """ Simply ensure that attrArg is a dictionary """
        if type(attrArg) != types.DictType:
            raise TypeError

        return attrArg
    procAttrs = classmethod(procAttrs)
    ## END procAttrs
## END class SObjectClassFactory

