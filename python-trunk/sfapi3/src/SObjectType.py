def verifySObjectType(cxn, sObjectType):
    if cxn.sfdc is None:
        raise NoConnectionError()
    elif sObjectType not in cxn.globalData.get('types'):
        errmsg = 'Type "%s" is an invalid SFDC Object type.' %sObjectType
        raise SObjectTypeError(errmsg)
    
    return
## END verifySObjectType

class SObjectTypeError(TypeError):
    pass
## END class SOBjectTypeError
