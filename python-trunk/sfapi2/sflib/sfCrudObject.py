"""
Proof of concept for sObject-based entity hierarchy
"""
import pprint
import copy
import types

from sfMagma import *
from sfConstant import *

SequenceTypes = (types.ListType, types.TupleType)

class SFCrudObject(SFMagmaEntity):
    """ Abstract base class for all sfdc objects. Provides basic CRUD
    features. Not intended to be instanced directly.
    """
    obj = None

    def __init__(self, sfTool, data={}, debug=0):
        """ sfTool is an SFMagmaTool instance
        data is a map of fields and values

        Not called directly to instantiate SFSolution objects - called by
        other static constructor methods
        """

        if self.obj is None:
            raise NotImplementedError

        self.sfTool = sfTool

        SFMagmaEntity.__init__(self, self.obj, data, sfTool=sfTool,
                               debug=debug)

        self.dataCopy = copy.deepcopy(self.getData(self.obj))
        
        return
    ## END __init__


    #############################
    ## Static constructor methods
    #############################

    def resultToObject(klass, sfTool, resultList, debug=0):
        """ Translate a list of query or retrieve results into objects
        """
        objList = []
        for res in resultList:
            data = { klass.obj: res }
            objInstance = klass(sfTool, data, debug=debug)
            objList.append(objInstance)
            continue
        
        return objList
    resultToObject = classmethod(resultToObject)
    ## END query


    def querySoql(klass, sfTool, soql):
        """ Run a query using a SOQL statement. Return a list of objects.
        """
        objList = []
        res = sfTool.query(klass.obj, soql=soql)
        if res not in BAD_INFO_LIST:
            objList = klass.resultToObject(sfTool, res)
            pass
        
        return objList
    querySoql = classmethod(querySoql)
    ## END query
    
    def queryWhere(klass, sfTool, where, fields='all'):
        """ Run a query using a where construct and an optional list of fields
        (or shortcut name). Return a list of objects.
        """
        objList = []
        res = sfTool.query(klass.obj, where=where, sc=fields)
        if res not in BAD_INFO_LIST:
            objList = klass.resultToObject(sfTool, res)
            pass
        
        return objList
    queryWhere = classmethod(queryWhere)
    ## END query

    def retrieve(klass, sfTool, id, fields='all'):
        """ Pass in a list of IDs, get back a list of objects. Pass in a
        single ID, get a single object. """
        returnList = True
        if type(id) in SequenceTypes:
            idList = id
        else:
            idList = [id]
            returnList = False
            pass

        objList = []
        res = sfTool.retrieve(idList, klass.obj, fields)
        if res not in BAD_INFO_LIST:
            objList = klass.resultToObject(sfTool, res)
            pass

        if returnList is True:
            return objList
        else:
            if len(objList) > 0:
                return objList[0]
            else:
                return None
    retrieve = classmethod(retrieve)

    def create(klass, sfTool, data):
        dataMap = copy.deepcopy(data)
        if type(dataMap) != types.DictType:
            msg = "Parameter type mismatch: dataMap Expected %s, recieved %s" \
                  %(types.DictType, type(dataMap))
            raise TypeError(msg)
        
        if dataMap.has_key('Id'):
            # Clear Id field if it should be provided
            del(dataMap['Id'])
            pass
        
        if len(dataMap) == 0:
            msg = "Can't create object with no data!"
            raise ValueError(msg)

        res = sfTool.create(klass.obj, dataMap)
        newObj = None
        if res not in BAD_INFO_LIST:
            newObjId = res[0]
            newObj = klass.retrieve(sfTool, newObjId)

        return newObj
    create = classmethod(create)
    ## END create

    def getRecordTypes(klass, sfTool):
        """ Return a map of record types by record type ID for the current
        class"""
        where = [['TableEnumOrId','=',klass.obj]]
        fields = ('Id','Name')
        res = sfTool.query('RecordType', where, sc=fields)

        recTypeMap = {}
        if res not in BAD_INFO_LIST:
            for recType in res:
                recTypeMap[recType.get('Id')] = recType.get('Name')
                continue
            pass
        return recTypeMap
    getRecordTypes = classmethod(getRecordTypes)
    ## END getRecordTypes
        
    ###################
    ## Instance Methods
    ###################
    
    def refresh(self, allFields=True):
        """ Refresh this object by re-retrieving it.
        Default will fetch all fields, allFields=False will fetch only the
        fields we currently have """
        success = False
        data = self.getData(self.obj)
        Id = data.get('Id',None)
        if Id is None:
            msg = "Instance of %s cannot be refreshed because it has no Id attribute!" %self.obj
            raise AttributeError(msg)

        fields = 'fields'
        if allFields is False:
            fields = data.keys()

        res = self.sfb.retrieve([Id], self.obj, fields)
        if res not in BAD_INFO_LIST:
            info = res[0]
            data = { self.obj: info }
            self.setData(data)
            success = True
            pass
        
        return success
    ## END refresh
        

    def update(self):
        """ Improve this to check against meta data and require ID"""
        updData = {}

        sourceData = self.getData(self.obj)
        updData['Id'] = self.dataCopy['Id']
        for key in sourceData.keys():
            if sourceData.get(key) != self.dataCopy.get(key):
                updData[key] = sourceData.get(key)
                pass
            continue

        res = self.sfb.update(self.obj, updData)
        
        if res[0] == updData['Id']:
            return True
        else:
            return False
    ## END update


    def delete(self):
        """ Delete this object from salesforce.com """
        objData = self.getDataMap()
        success = False
        res = self.sfb.delete(objData.get('Id'))

        # find a way to "deactivate" this object now that it's been deleted
        if res[0] == objData['Id']:
            del objData['Id']
            success = True

        return success
    ## END delete


    def relink(self, newParentObjId, linkFieldName):
        """ a shortcut to perform a relinking operation to the provided
        newParentObjId by modifying the field specified by linkFieldName """

        objData = self.getDataMap()
        oldParentObjId = objData.get(linkFieldName)

        objData[linkFieldName] = newParentObjId

        print "Updating %s %s from %s to %s" %(self.obj, objData.get('Id'),
                                               oldParentObjId,
                                               newParentObjId)
        self.update()
        return
    ## END relink
        

    def getDataMap(self):
        """ Returns a map of the object's data by wrapping getData and
        providing the object's type.
        """
        return self.getData(self.obj)
    ## END getDataMap
## END class SFCrudObject

class DetailRecordMixin:
    """
    Mixin for methods specific to detail records in a master-detail
    relationship
    """
    def queryParent(klass, sfTool, parentId, fields='fields'):
        where = [['ParentId','=',parentId]]

        return klass.queryWhere(sfTool, where, fields)
    queryParent = classmethod(queryParent)
    ## END queryParent
## END class DetailRecordMixin

class ObjectNotFoundError(LookupError):

    def __init__(self, msg=None):
        self.args = (msg)
        return
    pass
## END class ObjectNotFoundError
        
    
