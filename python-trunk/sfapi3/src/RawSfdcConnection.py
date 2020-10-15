"""
Authenticates a connection with the salesforce.com sforce api
maintains a session
provides server-scope calls
"""
import os

from SOAPpy import WSDL
from SOAPpy import structType
from SOAPpy import headerType
from SOAPpy import faultType

class RawSfdcConnection:

    def __init__(self, wsdlSource, namespace, username, password):
        """ construct an unconnected Sfdc connection """
        self.__username = username
        self.__password = password

        self.sfdc = None # container for the session. Used for all calls.

        self.userInfo = {}
        self.mapHdrRaw = {} # map of soap headers to set.

        self.__config()

        self.wsdlSource = wsdlSource
        self.sfdc = WSDL.Proxy(self.wsdlSource)

        # Assigning sforce namespace to each sforce method
        #
        # For some reason WSDLTools does not assign
        # "urn:partner.soap.sforce.com"
        # namespace to operations when it parses binding
        for method in self.sfdc.methods.itervalues():
            method.namespace = namespace
            continue

        self.__login()

        return

    def __config(self):
        WSDL.Config.debug = False
        WSDL.Config.namespaceStyle = '2001'
        WSDL.Config.simplify_objects = True
        WSDL.Config.typed = 0
        WSDL.Config.strictNamespaces = False
        WSDL.Config.force_refs_off = True
        WSDL.Config.force_typed_map_elements = False
        return
    ## END __config

    def __login(self):
        """ Perform all the negotiation with the endpoint and login
        to initiate a session """
        loginResult = self.sfdc.login(username=self.__username, 
                                      password=self.__password)
        self.userId = loginResult.get('userId')
        
        
        self.userInfo = loginResult.get('userInfo', {})  
        # Switch the binding to the returned endpoint
        for method in self.sfdc.methods.itervalues():
            method.location = loginResult.get('serverUrl')
            continue

        # set the session ID in the SOAP header
        self.buildSoapHdr('SessionHeader', 'sessionId', 
                          loginResult.get('sessionId'))
        self.setSoapHdr()

        return
    ## END __login

    def reLogin(self):
        self.__login()
        return
    ## END reLogin

    def buildSoapHdr(self, task, element, value):
        taskMap = self.mapHdrRaw.get(task, {})
        if taskMap.has_key(element) and value is None:
            # value was set to None - remove this header element
            del(taskMap[element])
        else:
            taskMap.update({element: value})
            pass
          
        self.mapHdrRaw[task] = taskMap
        return
    # END buildSoapHdr
          
    def setSoapHdr(self):
        """ iterates through the raw header map and build structs for each
        task, compiling a processed header map which is then installed
        into the soap proxy
        """
        mapHdrData = {}

        for task, taskMap in self.mapHdrRaw.items():
            if len(taskMap) == 0:
                # skip this task if there are no elements in it
                continue
               
            taskStruct = structType(data = taskMap)

            mapHdrData[task] = taskStruct
            continue

        # install the result header structure map into the soap proxy
        if len(mapHdrData):
            hd = headerType(data = mapHdrData)
            self.sfdc.soapproxy.header = hd
            pass
          
        return
    ## END setSoapHdr
    
    pass
## END class RawSfdcConnection


class NoConnectionError(Exception):
    pass
