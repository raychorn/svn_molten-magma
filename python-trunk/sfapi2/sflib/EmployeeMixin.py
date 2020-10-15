class EmployeeMixin:

    def __init__(self):
        errmsg = "%s is a mixin and is not to be instantiated directly!" \
                 %self.__class__
        raise(NotImplementedError(errmsg))
    ## END __init__
        
    def queryEmpNo(klass, sfTool, empNo, fields='all'):
        empNo = checkEmpNo(empNo)
        where = []

        if not hasattr(klass, 'empNoField'):
            errmsg = "Mixin cannot be used in a class that does not provide empNoField attribute."
            raise(AttributeError(errmsg))
        
            
        where = [[klass.empNoField, '=', empNo]]
        return klass.queryWhere(sfTool, where, fields)
    queryEmpNo = classmethod(queryEmpNo)
    ## END queryEmployeeNumber

    pass
## END EmployeeMixin

def checkEmpNo(empNo):
    """ Employee number must be a string representation of an integer """
    return str(int(empNo))
## END checkEmpNo
