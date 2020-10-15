import pprint, sys
import types
import sets

from Properties import Properties
from Util import booleanize

from Cache import Cache

import PysfdcLogger, logging
log = logging.getLogger('pysfdc.metadata')

class SObjectMetadata:
    """
    Represents a metadata structure

    """
    props = Properties()


    def __init__(self, describeSObjectResult):
        metadata = self.__parse(describeSObjectResult,
                                self.props.describeSObjectStruct)

        self.metadata = metadata
        return

    def __getattr__(self, key):
        if self.__dict__['metadata'].has_key(key):
            return self.__dict__['metadata'][key]
        elif self.__dict__.has_key(key):
            return self.__dict__[key]
        
        raise AttributeError
    ## END __getattr__

    def __str__(self):
        buf = "Object: %s\n" %self.name
        buf += "-"*20 + "\n"
        buf += self.__format(self.metadata,
                             self.props.describeSObjectStruct)
        return buf
    ## END __str__
    

    def __format(self, metadata, propStructData, level=0):
        order = ('string', 'int', 'boolean', 'list', 'contains')
        indent = '\t'*level
        buf = ''
        for part in order:
            fields = propStructData.get(part, [])
            if part == 'contains':
                for contained in fields:
                    partStructData = propStructData[contained]
                    field = propStructData[contained]['parentfield']
                    partMetadata = metadata.get(field)

                    if partMetadata is not None:
                        buf += "%s%s:\n" %(indent, field)
                        #buf += "%s\n" %partMetadata
                        pass
                    
                    
                    if type(partMetadata) == types.DictType:
                        plusIndent = "\t"*(level + 1)
                        for name, partMetadataMember in partMetadata.items():
                            buf += "%s%s\n" %(plusIndent, name)
                            buf += plusIndent + "-"*20 + "\n"
                            buf += self.__format(partMetadataMember,
                                                 partStructData,
                                                 level + 1)
                            buf += '\n'
                            continue
                            
                        pass
                    continue
                pass
            else:
                for field in fields:
                    if metadata.get(field) is not None:
                        buf += "%s%s: %s\n" %(indent, field, metadata.get(field))
                        continue
                    continue
                pass
        return buf

    def __parse(self, sourceData, propStructData):
        metaStruct = {}

        if sourceData is None:
            pass
        elif type(sourceData) == types.ListType:
            metaStruct = self.__parseMulti(sourceData, propStructData)
        else:
            metaStruct = self.__parseSingle(sourceData, propStructData)
            pass

        return metaStruct
    ## END __parse


    def __parseSingle(self, resultStruct, fieldDict):
        """
        field types we currently recognize:
        boolean: list of boolean fields
        string: list of string fields
        int: list of integer fields
        list: list of...
        """
        parseDict = {}
        dataDict = resultStruct
        
        for fieldType, fieldNames in fieldDict.items():
            if fieldType in ['boolean']:
                for fieldName in fieldNames:
                    parseDict[fieldName] = booleanize(dataDict.get(fieldName,
                                                                   False))
                    continue
                pass
        
            if fieldType in ['string','list']:
                for fieldName in fieldNames:
                    parseDict[fieldName] = dataDict.get(fieldName)
                    continue
                pass
        
            if fieldType in ['int']:
                for fieldName in fieldNames:
                    value = dataDict.get(fieldName)
                    if value is not None:
                        value = int(value)
                        pass
                    parseDict[fieldName] = value
                    continue
                pass
            
            if fieldType in ['contains']:
                for contained in fieldNames:
                    fieldName = fieldDict[contained]['parentfield']
                    parseDict[fieldName] = \
                                         self.__parse(dataDict.get(fieldName),
                                                      fieldDict[contained])
                    continue
            continue
        
        return parseDict
    ## END __parseMetadata


    def __parseMulti(self, structList, fieldDict):
        name = fieldDict['key']
        structDict = None
        if structList is not None:
            structDict = {}

            for struct in structList:
                #print struct
                structMeta = self.__parseSingle(struct, fieldDict)
                structDict[structMeta[name]] = structMeta
                continue
            pass
        return structDict
    ## END __parseList
        
    def __brewFieldData(self):
        """
        iterate over the fields metadata element and build lookups for various attributes
        
        Note that only a couple attrs are currently summarized
        
        """
        self.fieldnameMap = {}
        self.updateableFields = []
        self.nillableFields = []
        
        for fieldname, fielddata in self.metadata.fields.items():
            self.fieldnameMap[fieldname.lower] = fieldname

            if fielddata.get('updateable', False) is True:
                self.updateableFields.append(fieldname)
                pass
            
            if fielddata.get('nillable', False) is True:
                self.nillableFields.append(fieldname)
                pass
            
            continue

    pass
## END class SObjectMetadata


class MetadataHelperMixin:
    """
    Methods for a SfdcCrudBase-descended object to provide for easy access
    to metadata
    """

    def getFieldnames(klass):
        """
        Return a list of fieldnames from the metadata, sorted with Id as the
        first fieldname
        """
        fieldnames = klass._metadata.fields.keys()
        fieldnames.sort()

        if fieldnames[0] != 'Id':
            try:
                fieldnames.remove('Id')
                fieldnames.insert(0, 'Id')
            except:
                pass
            pass
        
        return fieldnames
    getFieldnames = classmethod(getFieldnames)
    ## END getFieldnames


class SObjectMetadataCache(Cache):
    def __init__(self, cxn, maxTimedelta):
        """
        cxn -  connected AppforceConnection object
        maxTimeDelta - datetime.timedelta object of the maximum age an entry may be before it is considered to be expired.
        
        """
        self.cxn = cxn
        self.maxTimedelta = maxTimedelta
        
        max_size = 0
        Cache.__init__(self, max_size)
        return
    ## END __init__


    def check(self, name, entry):
        nowTstamp = datetime.datetime.utcnow()

        try:
            entryAge = nowTstamp - entry._tstamp
            if entryAge < self.maxTimedelta:
                return None
            pass
        except AttributeError:
            pass

        opened = self.cnx.describeSObject()

