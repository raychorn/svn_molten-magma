"""
A clean version of the sfUser object representation. 
"""
from sfCrudObject import SFCrudObject
from EmployeeMixin import EmployeeMixin

class SFUser(SFCrudObject, EmployeeMixin):
    obj = "User"

    empNoField = 'EmployeeNumber'

