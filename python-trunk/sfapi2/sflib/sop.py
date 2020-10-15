""" Simple Object persistance using pickle and file locking
    ConfigParser wrapper for text viewable user preferences
    
    ToDo: text encryption handling for any field, notably passwords & entry points
    
    Chip Vanek June 1st, 2004
"""

from threading import Lock
import StringIO
import cPickle, marshal
import os, time, sys
import types, string
import ConfigParser
marshalMod = marshal
pickleMod = cPickle
import pprint
import tempfile
True, False = 1==1, 0==1    # python < 2.3 support

def filePath():
    if (os.environ.has_key('TEMP')):
        common = os.environ['TEMP']
    elif (os.environ.has_key('TMP')):
        common = os.environ['TMP']
    else:
        f = tempfile.TemporaryFile()
        common = os.path.abspath(os.sep.join(foo.name.split(os.sep)[0:-1]))
        f.close()
    return common

class Private:
    """ simple data cloaking class that can be extended with encryption
    """
    def __init__(self, data, key=None, digest=False):
        """ must have data, use preconfigured key if not provided """
        self.setKey(key)
        if not digest:
            self.setData(data)
        else:
            self._data = data
    
    def setData(self, data):
        """ this can be a public method """
        key = self.getKey()
        import base64
        self._data = base64.encodestring(data)
        
    def setKey(self, key):
        """ This needs to be private to be of any use """
        if key is not None:  self.key = key
        else:                self.key = ''

    def getKey(self, priv=False):
        if not priv: return self.key
        # this is were we need some trickery to control access to private key
        return self.key

    def getDigest(self):
        """ return public digest of this information """
        return self._data
    
    def getData(self, dkey=None):
        """ This needs to be private to be of any use """
        if dkey is None: dkey = self.getKey(True)
        import base64
        return base64.decodestring(self._data)

class SFConfig(ConfigParser.ConfigParser):
    """ Simple subclass of ConfigParser to add:
         - default location of configuration file
         - parameter list handling 
        Typical usage is:
         - create object with default dictionary if known
           - sfc = SFConfig({'username':'chip', 'port':80, 'output':'console'})
               ( passed defaults will overwrite defaults in files)
         - sfc.load() config from all possible config file
         - sfc.get(section, option)
         - sfc.set(section, option, value)
         - sfc.writeMy()
    """
    def __init__(self):
        ConfigParser.ConfigParser.__init__(self)
    
    def load(self, scope='all'):
        """  Load a series of available configuration files from preset locations
        """
        paths = []
        if (sys.platform == 'win32'):
            common = filePath()
        else:
            common = os.path.join('/','home','sfscript','data','sfapi')
        here = os.path.split(sys.argv[0])[0]
        dirs = [here,self.getHome(),common]
        for dir in dirs:
            if dir is None:
                continue
            for file in ['.sfConfig','sfConfig.ini','sForce.cfg']:
                fpath = os.path.join(dir,file)
                if os.path.isfile(fpath):
                    paths.append(fpath)
        if paths == []:
            self.loadMy()
        else:
            self.read(paths)
    
    def set(self, section, option, value):
        """  Create section if it does not exist """
        if not self.has_section(section):
            self.add_section(section)
        ConfigParser.ConfigParser.set(self, section, option, value)
    
    def get(self, section, option, raw=False, vars=None):
        """  Create section if it does not exist """
        if not self.has_section(section):
            self.add_section(section)
        if not self.has_option(section, option):
            return ''
        #print 'Looking for %s in %s' %(option, section)
        try: 
            val = ConfigParser.ConfigParser.get(self, section, option, raw=raw, vars=vars)
            return val
        except ConfigParser.NoOptionError:
            return 'unknown'
        except Exception, e:
            return 'error: %s'%e
        return 'unknown'

    def setPrivate(self, section, option, value):
        """ wrap set call with use of the Private class """
        key = self.get(section, 'PublicKey')
        pobj = Private(value, key=key)
        pvalue = pobj.getDigest()
        self.set(section, option, pvalue)
        
    def getPrivate(self, section, option, raw=False, key=None):
        """ wrap get call with use of the Private class """
        if not self.has_section(section):
            self.add_section(section)
        try: 
            val = ConfigParser.ConfigParser.get(self, section, option, vars=None)
            pobj = Private(val, digest=True)
            value = pobj.getData()
            return value
        except ConfigParser.NoOptionError:
            return 'unknown'
        except Exception, e:
            return 'error: %s'%e


    def loadMy(self):
        """ Load or create the signed on users home sfConfig file
        """
        fpath = os.path.join(self.getHome(),'.sfConfig')
        if not os.path.isfile(fpath):
            try: 
                fp = open(fpath,  'w')
                self.add_section('sForce3')
                self.set('sForce3', 'initialized', True)     
                self.write(fp)
                fp.close()
                os.chown(fpath, os.getuid(), 101)
                os.chmod(fpath, 0664)
            except Exception,e: 
                print 'Could not write your initial sForce configuration file in %s' %fpath
                print '%s err:%s' %(Exception,e)
        self.read(fpath)
        return fpath
        
    def writeMy(self):
        """
        Write the sfConfig file for the signed on user
        """
        fpath = os.path.join(self.getHome(),'.sfConfig')
        try: 
            fp = open(fpath, 'w')
            self.write(fp)
            fp.close()
            #os.chown(fpath, os.getuid(), 101)
            #os.chmod(fpath, 0664)
        except Exception,e: 
            print 'Could not write your sForce configuration file in %s' %fpath
            print '%s err:%s' %(Exception,e)

                        
    def getHome(self):
        """  Get the os specific home directory """
        if os.name in ['posix','mac']:
            home = os.environ.get('HOME')
        else: home = '\\'
        return home

    
    def getList(self, section, option, raw=False, vars=None):
        """ Get the values from the config file and return as a list
        """
        val = self.get(section, option, raw=raw, vars=vars)
        if type(val) != type(''): 
            print 'Unknown value type stored'
            return val
        l = val.split(' ')
        return l


osFlags = os.O_RDWR | os.O_CREAT #| os.O_DSYNC 
##########################################################################################
#  These are simple object persistence (thus SOP) classes to allow scripts to remember things
#   The SFEntitiesSOP class is tailored to store sForce entity metadata and refresh if stale
#
#   sfEntities is the entry point to access this structure, called from sfBase.py
##########################################################################################
class LockAndLoadMixin:
    
    def getPath(self):
        """ get the configured path for cache """
        self.sfc = SFConfig()
        self.sfc.load()       # load all possible configuration file and create initial file for user
        dpath = self.sfc.get('sForce', 'cache_dir')    
        if dpath in [None,'']:
            dpath = './cache' 
        if not os.path.isdir(dpath):
            try: 
                os.mkdir(dpath)
                print 'Created directory %s'%dpath
            except: 
                print 'Cannot make directory %s' %dpath
        self.path = dpath
        return dpath
        
    def load(self, default=None, marshal=False):
        """ Must be called from init of object """
        self._commitLock = Lock()
        self._needCommit = False
        if marshal:
            self._commitLoad = marshalMod.load
            self._commitDump = marshalMod.dump
        else:
            self._commitLoad = pickleMod.load
            self._commitDump = pickleMod.dump
        fpath = self.filename()
        if os.path.exists(fpath):
            try:  
                f = open(fpath)
                value = self._commitLoad(f)
                f.close()
            except Exception,e:
                print '%s err:%s'%(Exception,e)
                print 'Corrupt Pickle file %s' %fpath
                print ' Trying to delete this temporary file'
                try:  os.remove(fpath)
                except: 
                    print 'Could not delete Cache file please send this text to'
                    print '  salesforce-support@molten-magma.com'
                    #print 'Please avoid using ctr-D to stop the script'
                sys.exit(1)
        else:
            value = default
        return value

    def changed(self):
        self._needCommit = True

    def commit(self):
        #print "Committing self to: %s" % self.filename()
        fpath = self.filename()
        if self._needCommit:
            createFlag = False
            if os.path.exists(fpath) is False:
                createFlag = True

            f = None
            try:
                self._commitLock.acquire()
                f = open(fpath, 'w')
                self._commitDump(self.data(), f)

                self.lastUpdate = time.time()
                self._needCommit = False

                #print "done committing %s in %s to %s" % (self.lastEntity, self.__class__.__name__, self.filename())
            except Exception,e: 
                print '%s err:%s'%(Exception,e)
                print 'Problem committing to the SOP cache'
                pass

            try:
                if hasattr(f, 'close'):
                    f.close()
                self._commitLock.release()
                
                if createFlag is True:
                    if (sys.platform != 'win32'):
                        os.chown(fpath, os.getuid(), 101)
                        os.chmod(fpath, 0664)
            except Exception, e:
                print '%s err:%s'%(Exception,e)
                print 'Problem closing the SOP cache'
                pass

    def __del__(self):
        #self.commit()
        pass


class SFEntitiesSOP(LockAndLoadMixin):
    """  Maintain a file based copy of the sForce API metadata information
         The file path should be to a path available to all API users.
         The information will be refreashed from SF every X days or on demand
    """
    #maxObjAge = 60*5  # every 5 min
    maxObjAge = 60*60*24  # every day in seconds
    #maxObjAge = 60*60*24*5  # every 5 days in seconds
    lastUpdate = 0
    lastEntity = ''
    resetStale = False
    
    def filename(self):
        ## this is where the data will be pickled to
        common = os.path.join('/','home','sfscript','data','sfapi')
        if (sys.platform == 'win32'):
            common = filePath()
        return os.sep.join([common,'sForce30Entity%s.pickle' % self.scopeID])

    def __init__(self, scope='All'):
        self.scopeID = scope
        self._entities = self.load({}) # start with an empty dictionary
        #self._updateTS = self.load({}) 
        
    def setEntity(self, entity, value):
        self._entities[entity] = value
        self.setAge(entity)
        self.lastEntity = entity
        self.changed()                 # commit the update
        
    def reset(self, state=False):
        """ rest age to refresh on next access """
        self.resetStale = state

    def getAge(self, entity):
        """ return age of sop info in secs """
        uMap = self.getEntity('updateTimeStamps',{})
        eAge = uMap.get(entity,0)
        #print 'uAge for %s is %s' %(entity, eAge)
        return time.time() - eAge
    
    def setAge(self, entity):
        """ return age of sop info in secs """
        uMap = self.getEntity('updateTimeStamps',{})
        uMap[entity] = time.time()
        self._entities['updateTimeStamps'] = uMap
        #print 'set age for %s ' %(entity)

    def isStale(self, entity):
        """ Should we load fresh data from remote server """
        isit =  int(self.getAge(entity)) > self.maxObjAge
        if self.resetStale: 
            isit = True
        #print 'Checking if %s > %s as %s' %(int(self.getAge(entity)), self.maxObjAge, isit)
        return isit
        
    def getEntity(self, entity, default=''):
        return self._entities.get(entity, default)

    def __len__(self):
        return len(self._entities)
        
    def __str__(self):
        return pprint.pformat(self._entities)

    def __repr__(self):
        return pprint.pformat(self._entities)

    def data(self):
        ## this is what will get pickled -- it goes with self.load() in __init__
        return self._entities
        

class SFSOP(LockAndLoadMixin):
    """  Maintain a local file based copy of sForce entity info
         The file path should be to a path available to all API users.
         A pair of get/set methods should be added to your tool class to 
         access this class.  Examples are getEntitySOP, setEntitySOP in sfBase3
    """
    #maxObjAge = 60*60*24  # every day in seconds
    maxObjAge = 60*60*24*5  # every 5 days in seconds
    lastUpdate = 0
    lastEntity = ''
    resetStale = False
    
    def filename(self):
        ## this is where the data will be pickled to
        common = os.path.join('/','home','sfscript','data','sfapi')
        if (sys.platform == 'win32'):
            common = filePath()
        return os.sep.join([common,'sForce30%s.pickle' % self.scopeID])

    def __init__(self, scope='All'):
        self.scopeID = scope
        self._data = self.load({}) # start with an empty dictionary
        #self._updateTS = self.load({}) 
        
    def setData(self, key, value):
        self._data[key] = value
        self.setAge(key)
        self.lastEntity = key
        self.changed()                 # commit the update
        
    def getData(self, key, default=''):
        return self._data.get(key, default)

    def reset(self, state=False):
        """ rest age to refresh on next access """
        self.resetStale = state

    def delData(self, key):
        """ delete value from the cache """
        if hasattr(self._data, key):
            del self._data[key]
        
    def getAge(self, key):
        """ return age of sop info in secs """
        uMap = self.getData('updateTimeStamps',{})
        eAge = uMap.get(key,0)
        #print 'uAge for %s is %s' %(key, eAge)
        return time.time() - eAge
    
    def setAge(self, key):
        """ return age of sop info in secs """
        uMap = self.getData('updateTimeStamps',{})
        uMap[key] = time.time()
        self._data['updateTimeStamps'] = uMap
        #print 'set age for %s ' %(key)

    def isStale(self, key):
        """ Should we load fresh data from remote server """
        isit =  int(self.getAge(key)) > self.maxObjAge
        if self.resetStale: 
            isit = True
        #print 'Checking if %s > %s as %s' %(int(self.getAge(key)), self.maxObjAge, isit)
        return isit
        
    def __len__(self):
        return len(self._data)
        
    def __str__(self):
        return pprint.pformat(self._data)

    def __repr__(self):
        return pprint.pformat(self._data)

    def data(self):
        ## this is what will get pickled -- it goes with self.load() in __init__
        return self._data
        


class AccessFactory:
    def __init__(self, klass):
        self.lock = Lock()
        self.cache = {}
        self.klass = klass
    def __call__(self, *args):
        self.lock.acquire()
        if not self.cache.has_key(args):
            value = self.klass(*args)
            self.cache[args] = value
            self.lock.release()
            return value
        else:
            self.lock.release()
            return self.cache[args]
    
class CcBranchSOP(SFSOP):
    """
    Local cache of branch data gathered from ClearCase.
    """
    maxObjAge = 60*60*24*1000 # 1000 days in seconds
    lastUpdate = 0
    lastEntity = ''
    resetStale = False

    def filename(self):
        # this is where the data will be pickled to
        common = os.path.join('/','home','sfscript','data','ccbranch')
        if (sys.platform == 'win32'):
            common = filePath()
        return os.sep.join([common,'ccbranch.pickle'])

    def __init__(self):
        SFSOP.__init__(self)

    
class OpBranchSOP(SFSOP):
    """
    Local cache of operations branch data.
    """
    maxObjAge = 60*60*24*10 # 10 days in seconds
    lastUpdate = 0
    lastEntity = ''
    resetStale = False

    def filename(self):
        # this is where the data will be pickled to
        common = os.path.join('/','home','sfscript','data','sfapi')
        if (sys.platform == 'win32'):
            common = filePath()
        return os.sep.join([common,'opBranch.pickle'])

    def __init__(self):
        SFSOP.__init__(self)

class SFBranchesSOP(SFSOP):
    """  Maintain a local file based copy of the branches loaded into sForce
         The file path should be to a path available to all API users.
         The information will be updated as load scripts are run from the 
         modMigration, walkSF, and walkSCM scripts
    """
    #maxObjAge = 60*5  # every 5 min in seconds
    maxObjAge = 60*60*24*366  # a (leap) year in seconds
    lastUpdate = 0
    lastEntity = ''
    resetStale = False
    
    def filename(self):
        ## this is where the data will be pickled to
        common = os.path.join('/','home','sfscript','data','sfapi')
        if (sys.platform == 'win32'):
            common = filePath()
        return os.sep.join([common,'sForce30Branches%s.pickle' % self.scopeID])

class SFCacheSOP(SFSOP):
    """  Maintain a local file based cache of frequently accessed entities in sForce
         The file path should be to a path available to all API users.
         The information will be updated and used from load scripts are run from the 
         modMigration, walkSF, and walkSCM scripts
    """
    maxObjAge = 60*60*24  # every day in seconds
    #maxObjAge = 60*60*24  # every day in seconds
    #maxObjAge = 60*60*24*5  # every 5 days in seconds
    lastUpdate = 0
    lastEntity = ''
    resetStale = False
    
    def filename(self):
        ## this is where the data will be pickled to
        common = os.path.join('/','home','sfscript','data','sfapi')
        if (sys.platform == 'win32'):
            common = filePath()
        return os.sep.join([common,'sForce30Cache%s.pickle' % self.scopeID])

sfEntities = AccessFactory(SFEntitiesSOP)
## sfEntities is then the way to get a SFEntities object
sfBranches = AccessFactory(SFBranchesSOP)
sfCache = AccessFactory(SFCacheSOP)
ccBranches = AccessFactory(CcBranchSOP)
opBranches = AccessFactory(OpBranchSOP)

import SforceService_services as sfsv
from SforceService_services_types import urn_partner_soap_sforce_com as ns2
from SforceService_services_types import urn_sobject_partner_soap_sforce_com as ns1

class SFEntitiesMixin:
    """  Part of the base sForce class that is focused on 
         querying and storing entity metadata in the above SOP class
         
    """

    def describeGlobal(self):
        """ describe global and set available entity list on object describeGlobal
        """
        if (time.time() - self.entityTS) < 600:   # if less then 5 min then used cached copy of entitiy list
            if len(self.entityList) > 10:
                return self.entityList
        req = sfsv.describeGlobalRequestWrapper()
        result = self.sfdc.describeGlobal(req, auth_header=self.getSessionHeader())
        if hasattr(result, '_result'):
            res = result._result
            self.entityList = res._types
            #print 'Gdesc _result:%s _types:%s' %(res, self.entityList)
            return self.entityList
        return None

    def describeSObject(self, sObjectType):
        """ describe objects """
        req = sfsv.describeSObjectRequestWrapper()
        req._sObjectType = sObjectType
        result = self.sfdc.describeSObject(req, auth_header=self.getSessionHeader())
        if hasattr(result, '_result'):
            return result._result
        return None


    def setEntityMap(self, entity):
        """ load the latest metadata for entity into a simple object persitence dictionary
        """
        st = time.time()
        emap = self.getEntityMapFromSF(entity)
        fl = len(emap['fields'])
        if self.debug > 3: 
            print '%2d sec Got %s keys and %s fields in %s' %(time.time()-self.startTime, len(emap.keys()), fl, entity)
            print " As %s"%emap
        self.em.setEntity(entity, emap)
        self.em.commit()
            
    def setEntitiesMap(self):
        """ load the latest metadata into a simple object persitence dictionary
        """
        if len(self.entityList) < 10: self.describeGlobal()
        for ent in self.getEntities():
            self.setEntityMap(ent)
        
            
    def getEntityMapFromSF(self, ent):
        """ query sForce on metasdata on entity and return as a dictionary
              _activateable: boolean
              _createable: boolean
              _custom: boolean
              _deletable: boolean
              _fields: ns2.Field_Def, optional
                _label: str
                _name: str
                _nameField: boolean
                _custom: boolean
                _filterable: boolean          -  us in where clause
                _nillable: boolean
                _createable: boolean
                _updateable: boolean
                _referenceTo: str, optional

                _restrictedPicklist: boolean
                _picklistValues: ns2.PicklistEntry_Def, optional
                  _active: boolean
                  _defaultValue: boolean
                  _label: str, optional
                  _value: str
                _byteLength: int
                _length: int
                _digits: int
                _precision: int
                _scale: int
                _soapType: ns2.soapType_Def
                  _soapType: str, optional
                _type: ns2.fieldType_Def
                  _fieldType: str, optional
              _label: str
              _name: str
              _queryable: boolean
              _replicateable: boolean
              _retrieveable: boolean
              _searchable: boolean
              _undeletable: boolean
              _updateable: boolean
        """
        eObj = self.describeSObject(ent)
        eDict = {'custom':eObj._custom}
        eDict['createable'] = eObj._createable
        eDict['deletable'] = eObj._deletable
        eDict['updateable'] = eObj._updateable
        eDict['searchable'] = eObj._searchable
        eDict['retrieveable'] = eObj._retrieveable
        eDict['queryable'] = eObj._queryable
        eDict['replicateable'] = eObj._replicateable
        eDict['undeletable'] = eObj._undeletable
        eDict['label'] = eObj._label
        eDict['name'] = eObj._name
        fDict = {}
        fields = []
        filters = []
        required = []
        for f in eObj._fields:
            name = f._name
            if f._filterable:
                filters.append(name)
            if not f._nillable and f._createable:
                required.append(name)
            fields.append(name)
            fInfo = {'name': name}
            fInfo['label'] = f._label
            fInfo['createable'] = f._createable
            fInfo['updateable'] = f._updateable
            fInfo['filterable'] = f._filterable
            fInfo['nillable'] = f._nillable
            fInfo['nameField'] = f._nameField
            fInfo['custom'] = f._custom
            fInfo['referenceTo'] = f._referenceTo  # list of referenced object IDs
            type = f._type
            fInfo['type'] = type

            if type == 'picklist':
                picklistMap = {}
                for pv in f._picklistValues:
                    picklistMap[pv._label] = pv._value
                    continue
                fInfo['picklistValues'] = picklistMap
                pass
                
            fInfo['digits'] = f._digits   # if type integer then integer
            fInfo['precision'] = f._precision   # total number of bytes left and right of decimal point
            fInfo['scale'] = f._scale   # bytes right of decimal point, will return fault if too many to left of decimal, coordinate with above
            fInfo['length'] = f._length     # if type string then char count
            fInfo['byteLength'] = f._byteLength     # size for binary type fields
            if f._restrictedPicklist:       # this may be the wrong logic
                pl = []
                for plo in f._picklistValues:
                    pl.append([plo._label, plo._value, plo._defaultValue, plo._active])
                fInfo['pickList'] = pl
            fDict[name] = fInfo
            
        eDict['fieldInfo'] = fDict
        eDict['fields'] = fields
        eDict['filters'] = filters
        eDict['required'] = required
        return eDict
            
            
class SFUtilityMixin:
    """  Placeholder for utility methods
         Field data transform, output formatters, etc.
    """                      
    TRANSLATION_TABLE = string.ascii_uppercase + string.digits[:6]

    def convertId15ToId18(id15):
        """ Convert sForce 15 character IDs to 18 char IDs """
        validLen = 15
        chunkSize = 5
        caseSafeExt = ''
        if len(id15) != validLen:
            msg = "Parameter id15 must be exactly %s characters long" %validLen
            raise ValueError, msg
        idStr = id15
        while len(idStr) > 0:
            chunk = idStr[:chunkSize]
            idStr = idStr[chunkSize:]
            caseSafeExt += convertChunk(chunk)
        return "%s%s" %(id15, caseSafeExt)

    def convertChunk(chunk):
        """ Used by convertId15ToId18    """
        global BINARY, DECIMAL
        global TRANSLATION_TABLE
        chunkBinList = []

        # for each character in chunk, give that position a 1 if uppercase,
        # 0 otherwise (lowercase or number)
        for character in chunk:
            if character in string.ascii_uppercase:
                chunkBinList.append('1')
            else:
                chunkBinList.append('0')

        chunkBinList.reverse() # flip it around so rightmost bit is most significant
        chunkBin = "".join(chunkBinList) # compress list into a string of the binary num
        chunkCharIdx = baseconvert(chunkBin, BINARY, DECIMAL) # convert binary to decimal
        return TRANSLATION_TABLE[int(chunkCharIdx)] # look it up in our table

    ########################################################################
    # base converter utility function - may go to live with other utility
    # classes someday...
    ########################################################################
    BASE2  = string.digits[:2]
    BINARY = BASE2
    
    BASE8  = string.octdigits
    OCTAL = BASE8

    BASE10 = string.digits
    DECIMAL = BASE10

    BASE16 = string.digits + string.ascii_uppercase[:6]
    HEX = BASE16

    def baseconvert(number,fromdigits,todigits):
        if str(number)[0]=='-':
            number = str(number)[1:]
            neg = True
        else:
            neg = False

        # make an integer out of the number
        x=long(0)
        for digit in str(number):
            x = x*len(fromdigits) + fromdigits.index(digit)
    
        # create the result in base 'len(todigits)'
        res=''
        while x>0:
            digit = x % len(todigits)
            res = todigits[digit] + res
            x /= len(todigits)
        if len(res) == 0:
            res = 0
        if neg:
            res = "-%s" %res

        return res

class SFTestMixin:
    """  Placeholder for methods from prior test
         plus active test case data
    """                      

    def updateTest1(self, entity='Task', data={}, nullEmpty=False, seed='on seed'):
        """  Some test data around the update call
        """
        if self.debug > 1:print '-----------------------Test with seed %s -----------------------------------------------------\n'%seed
        ISO_8601_DATETIME = '%Y-%m-%dT%H:%M:%S'

        if data == {}:
            dtup = time.strptime('2004-03-24T12:30:59', ISO_8601_DATETIME)
            adate = time.mktime(dtup)
            data={'Status':'updated from api3 %s' %seed
                 ,'Subject':'This is the new subject %s' %seed
                 ,'Description':'This is the Description update %s' %seed
                 ,'Developer__c':'chip@molten-magma.com'
                 ,'ActivityDate':adate
                 ,'id': '00T30000002z4MA'
                 }
        return self.updateBase(entity, data=data, nullEmpty=nullEmpty)
        

    def createTest1(self, entity='Task', data={}, nullEmpty=False, seed='on seed'):
        """  Some test data around the create call
        """
        if self.debug > 1:print '-----------------------Test with seed %s -----------------------------------------------------\n'%seed
        ISO_8601_DATETIME = '%Y-%m-%dT%H:%M:%S'

        if data == {}:
            dtup = time.strptime('2004-03-24T12:30:59', ISO_8601_DATETIME)
            adate = time.mktime(dtup)
            data={'Status':'updated from api3 %s' %seed
                 ,'Subject':'This is the new subject %s' %seed
                 ,'Description':'This is the Description update %s' %seed
                 ,'Developer__c':'chip@molten-magma.com'
                 ,'ActivityDate':adate
                 }
        return self.createBase(entity, data=data, nullEmpty=nullEmpty)
        
        

    ##################################################################################################
    #   Trash from wsdl2python oriented attempt
    # 
    #   .............Delete me.................
    #
    ##################################################################################################
    def getBySOQLBad(self, soql=None, limit=200):
        """ search sForce using SOQL, return objects using retrieve call
            CV May 25, 2004, another dead end with the state of the proxy objects
        """
        req = sfsv.queryRequestWrapper()
        req._queryString = '%s' %soql
        print 'getBySOQL: Querying using the SOQL %s\n' %(soql)
        try: resp = self.sfdc.query(req, auth_header=self.getSessionHeader())
        except Exception,e:
            print 'getBySOQL:Error %s %s' %(Exception,e)
            import traceback
            traceback.print_exc ()
            return
        result = resp._result
        done = result._done
        size = result._size
        queryLocator = result._queryLocator
        records = result._records
        returnList = []
        print 'Using ZSI Proxy calls found the following information:\n'
        print ' done:%s  size:%s  queryCursor:%s '%(done,size,queryLocator)
        for record in records:
            print ' id:%s as type:%s nulls:%s' %(record._Id, record._type, record._fieldsToNull)
            returnList.append(record._Id)
            
        print 'Is that right?\n' 
        self.retrieveByIds(returnList)
        return returnList   
        

    def retrieveByIds(self, ids=[], entity='Contact'):
        """ try the ZSI Proxy type objects, 
            CV May 25, 2004, another dead end with the state of the proxy objects
        """
        req = sfsv.retrieveRequestWrapper()
        req._sObjectType = entity
        filter = self.getEntityMap(entity)['filters']
        req._fieldList = filter
        idObj = ns2.ID_Def()
        for id in ids:
            idObj._ID = id
            req._ids = idObj
            print 'retrieveByIds: getting %s as %s\n' %(id, entity)
            try: resp = self.sfdc.retrieve(req, auth_header=self.getSessionHeader())
            except Exception,e:
                print 'retrieveByIds:Error %s %s' %(Exception,e)
                import traceback
                traceback.print_exc ()
                return

            result = resp._result
            print 'Using ZSI Proxy calls found the following information:\n'
            print '  %s' %result
            print ' id:%s as type:%s nulls:%s\n' %(result._Id, result._type, result._fieldsToNull)
        print 'all done, Daddy'
        
        
    def getZSIProxyClass(self, records):
        """ Not used now, was a thread towards using the proxy objects build by wsdl2python
            New way is to use the sellf.getEntityMap('entity') dictionary cached in file pickle
            CV May 25, 2004, another dead end with the state of the proxy objects
        """
        getTypeClass = False                 # could use the generated classes to indicate the expected attributes.
        if getTypeClass:                     #   The kwDict above is only the non None values
            className,ns = self.getRecType(records[0])
            klassName = '%s_Dec'%className
            tc = getattr(ns1, klassName)                    # need a better class getter
            print 'FOUND TC for %s AS %s' %(klassName, tc )
            if tc is not None:
                try: 
                    tcObj = tc()
                    print 'Created the Instance!!'
                    if hasattr(tcObj, 'typecode'):
                        typeClass = tcObj.typecode
                        #typeClass.parse(recNode, self.binding.ps)
                        rresult.append( typeClass )
                        #rresult.append( self.binding.ps.Parse(typeClass) ) # this would parse the whole subtree, right?  not what we want.
                except Exception,e:
                    print 'TypeObj call error %s  %s' %(Exception,e)
                    print ' FOUND TC for %s AS %s' %(klassName, tc )
                    print ' dir TC %s' %dir(tc)
                    print ' kwDict %s' %kwDict
                    import traceback
                    traceback.print_exc ()
                    return

    def getRecType(self, node):
        """ this assumes a DOM node object, Just used in getZSIProxyClass, so trash during cleanup """
        av = ':'
        ns = None
        for a in _attrs(node):
            #print 'records attr:%s\n' %a
            if a.localName.find('type') >= 0:
                av = a.nodeValue
            if a.localName.find('sf') >= 0:
                ns = a.nodeValue
        
        className = av.split(':')[1]
        print 'This record is type:%s in ns:%s' %(className,ns)     
        print '^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^'
        return className, ns
        

class BasicCacheMixin:
    cache = None
    debug = 0

    #####################################################################
    #  Basic local caching of entity information for quick access,
    #  Non volitile info like User/Contact info
    #####################################################################
    def __init__(self, cache):
        """
        Pass in an SOP-based object
        Provides generic set/get functionality
        """
        self.cache = cache
        return
    ## END __init__
    
    def __get__(self, key):
        """ link get method to getCache """
        return self.getCache(key)

    def getCache(self, key, data={}, reset=False):
        """
        main accessor for getting cache information
        """
        if self.debug > 2: print 'Load status for %s loaded %3d secs ago' %(key, self.cache.getAge(key))
        if reset: self.cache.reset(True)
        if self.cache.isStale(key):
            if self.debug > 2: print 'Updating SOP %s for %s' %(key, self.__name__)
            self.setCache(key, data)
            if reset: self.cache.reset(False)
        return self.cache.getData(key)
    ## END getCache
    
    def setCache(self, key, data={}, commit=True):
        """ load the latest data for the key into a simple object
        persitence dictionary
        """
        st = time.time()
        if data in [None,{},[],'']:
            data = {'loadStatus':'new'}
        
        if self.debug > 2: print '%2d sec Got %s keys and in %s' %(time.time()-st, len(data.keys()), key)
        self.cache.setData(key, data)
        #print 'SetCache set key %s with %s'%(key, data)
        if commit is True:
            self.commitCache()
        return
    ## END setCache

    def commitCache(self):
        self.cache.commit()
        return
    ## END commitCache
    
    def getKeys(self, sortField='createDateTime'):
        """
        return sorted (newest to oldest) list of all keys of items
        in the pickle
        """
        keys = self.cache._data.keys()
        cleankeys = []
        try:
            keys.remove('updateTimeStamps')
        except Exception, e:
            pass

        for key in keys:
            if self.getCache(key).get(sortField, None) is not None:
                cleankeys.append(key)
        
        cleankeys.sort(lambda a, b: cmp(self.getCache(a)[sortField],
                                   self.getCache(b)[sortField]))
        cleankeys.reverse()
        return cleankeys
    ## END getKeys
## END BasicCacheMixin

        
