"""
A clean version of the sfContact object representation. 
"""
from sfCrudObject import SFCrudObject
from EmployeeMixin import EmployeeMixin

class SFContact(SFCrudObject, EmployeeMixin):
    obj = "Contact"

    empNoField = 'EmployeeNumber__c'
