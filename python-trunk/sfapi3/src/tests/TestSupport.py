import logging, logging.config

from Properties import Properties
from SfdcConnection import SfdcConnection

class TestCxn:
    """
    Singleton containing an sfdc connection for use across the test suite
    (aside from connection tests, of course)
    """
    _shared_state = {}
    
    def __init__(self):
        self.p = None
        
        self.__dict__ = self._shared_state
        
        if not hasattr(self, 'p') or self.p is None:
            logging.basicConfig()
            self.p = Properties()
            self.cxn = SfdcConnection(self.p.testUsername, self.p.testPassword)
            pass
        return
    ## END __init__
    
    pass
## END class TestCxn

class TestData:
    Case = {}
    Case[0] = {'Subject': '!@#$% Test Create Case Subject 1',
               'Status': 'New',
               'Origin': 'Email',
               'Description': 'Hommina hommina hommina',
               'Priority': 'Low'}
           
    Case[1] = {'Subject': '!@#$% Test Create Case Subject 2',
               'Status': 'New',
               'Origin': 'Phone',
               'Description': 'Bippity boppity boo!',
               'Priority': 'High'}

    pass