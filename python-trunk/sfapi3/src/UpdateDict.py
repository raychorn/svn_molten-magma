import copy

FTNKEY = 'fieldsToNull'

class UpdateDict(object):
    """
    Tracked dictionary - keeps track of which fields were changed or deleted since
    the dictionary was initialized
    
    """
    def __init__(self, initDict={}):
        self._initialize(initDict)
        return
    
    def _initialize(self, initDict):
        """
        A super-update that discards any pending updates and replaces the 
        __origDataMap member with the new data
        
        """
        self.__origDataMap = {}
        self.__origDataMap.update(dict(initDict))

        self.clear()
        return
    ## END _initialize
    
    def _mergeView(self):
        """
        return a copy dictionary that is the union of the original dictionary
        and any updates
        """
        mergeDataMap = copy.deepcopy(self.__origDataMap)
        updateCopy = copy.deepcopy(self.__updateMap)
        fieldsToNull = updateCopy.get(FTNKEY)
        if fieldsToNull is not None:
            del updateCopy[FTNKEY]

            for field in fieldsToNull:
                updateCopy[field] = None
                continue
            pass
            
        mergeDataMap.update(updateCopy)
        
        return mergeDataMap
    ## END _mergeView
    
    def clear(self, key=None):
        """
        Clear any stored updates leaving only the original data
        
        Parameters:
        key - If provided, clear will clear any pending updates to the listed
            field. If there are no pending updates to the listed field, the method
            will exit quietly

        """
        if key is None:
            # clear all updates
            self.__fieldsToNull = []
            self.__updateMap = {FTNKEY: self.__fieldsToNull}

        else:
            # clear change to just a single field
            if key in self.__fieldsToNull:
                self.__fieldsToNull.remove(key)
                pass
            
            if self.__updateMap.has_key(key):
                del self.__updateMap[key]
                pass
        return
    
    def getUpdates(self):
        """
        Returns a copy of the pending updates dictionary
        
        """
        return copy.deepcopy(self.__updateMap)
    ## END getUpdates
    
    def commit(self):
        """
        Incorporate all pending updates into the original data
        
        """
        self._initialize(self._mergeView())
        return
    ## END commit
    
    def __str__(self):
        return str(self._mergeView())
    ## END __str__
    
    def __repr__(self):
        return str(self)
    ## END __repr__
    
    def __len__(self):
        return len(self.keys())
    ## END __len__
    
    def __getitem__(self, key):
        if key in self.__updateMap[FTNKEY]:
            return None
        elif self.__updateMap.has_key(key):
            return self.__updateMap[key]
        elif self.__origDataMap.has_key(key):
            return self.__origDataMap[key]
        else:
            raise KeyError
        
        return None # should never reach here
    ## END __getitem__
    
    def __setitem__(self, key, value):
        # don't allow external manipulation of fieldsToNull
        if key == FTNKEY:
            # FIXME - is this the right exception?
            raise KeyError
        
        # if we had set this field to null previously, unset it
        if key in self.__fieldsToNull:
            self.__fieldsToNull.remove(key)
            pass

        self.__updateMap[key] = value
        return
    ## END __setitem__
        
    def __delitem__(self, key):
        """
        Mark a field to be nulled. Unlike a regular dictionary, if the key doesn't exist
        in the UpdateDict instance anywhere, it is still added to the __fieldsToNull member
        and KeyError will not be raised.
        
        Parameters:
        key - field name to clear when update is issued
        """
        # don't allow deletion of fieldsToNull
        if key == FTNKEY:
            # FIXME - is this the right exception?
            raise KeyError

        if self.__updateMap.has_key(key):
            del self.__updateMap[key]
            pass
        
        if key not in self.__fieldsToNull:
            self.__fieldsToNull.append(key)
            pass
        
        return
    ## END __delitem__
        
    def __contains__(self, key):
        return key in self.keys()
    ## END contains
        
    def update(self, updateSrcDict):
        self.__updateMap.update(updateSrcDict)
        return
    ## END update
    
    def setdefault(self, key, defaultvalue=None):
        if not self.has_key(key):
            self[key] = defaultvalue
            pass
        
        return self.get(key)
    ## END setdefault
    
    def get(self, key, defaultvalue=None):
        retval = defaultvalue
        if self.has_key(key):
            retval = self[key]
            pass
        return retval
    ## END get
        
    # pop & popitem don't make sense for this dictionary-like mapping object
    
    def keys(self):
        return self._mergeView().keys()
    ## END keys
    
    def __iter__(self):
        return iter(self.keys())
    ## END __iter__
    
    # also make __iter__ available as iterkeys
    iterkeys = __iter__
    
    def values(self):
        return self._mergeView().values()
    ## END values
        
    def itervalues(self):
        return iter(self.values())
    ## END itervalues

    def items(self):
        return self._mergeView().items()
    ## END items
    
    def iteritems(self):
        return iter(self.items())
    ## END iteritems

    def copy(self):
        raise NotImplementedError
    ## END copy
    
    def has_key(self, key):
        return key in self
    ## END has_key
