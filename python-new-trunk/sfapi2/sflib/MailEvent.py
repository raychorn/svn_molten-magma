from vyperlogix.misc import ObjectTypeName
from vyperlogix.misc import _utils
from vyperlogix.hash import lists
from vyperlogix.classes.CooperativeClass import Cooperative
from vyperlogix.misc.decodeUnicode import decodeUnicode

import time
import logging

class SmartKeyedObject(Cooperative):
    def __init__(self,args,useSubKeys=False):
	from vyperlogix.hash import lists
	
	self.__useSubKeys__ = useSubKeys
	
	self.__use_subkeys_test__ = lambda a:(all([isinstance(item,dict) for item in a.values()]))
	self.__use_compositekeys_test__ = lambda a:(all([(lists.isDict(item)) for item in a.values()]))
	
        if (isinstance(args,dict)):
	    is_loading_special_keys = self.__use_subkeys_test__(args) if (self.useSubKeys) else self.__use_compositekeys_test__(args)
	    if (is_loading_special_keys):
		for ak,av in args.iteritems():
		    for k,v in av.iteritems():
			self.__dict__['%s_%s' % (ak,k)] = v
	    else:
		self.fromDict(args)
        else:
            logging.warning('(%s.%s) :: Illegal args variable, expected type "dict" but got type "%s".' % (ObjectTypeName.typeName(self),_utils.funcName(),ObjectTypeName.typeName(args)))
    
    def useSubKeys():
        doc = "useSubKeys or not"
        def fget(self):
            return self.__useSubKeys__
        return locals()
    useSubKeys = property(**useSubKeys())

    def asDict(self,insideOut=False):
        return lists.asDict(self.__dict__,insideOut=insideOut)
    
    def asSubDict(self,prefix):
	d = {}
	for k in [k for k in self.__dict__.keys() if (k.startswith(prefix))]:
	    d[k.replace(prefix,'')] = self.__dict__[k]
        return lists.HashedLists2(d)
    
    def fromDict(self,d):
	if (isinstance(d,dict)):
	    for k,v in d.iteritems():
		self.__dict__[k] = v
    
    def keys(self):
        return _utils.sortCopy(self.__dict__.keys())

    def iteritems(self):
        return ((k,self.__getattr__(k)) for k in self.keys())
    
    def __len__(self):
        return len(self.keys())

    def __getattr__(self, name):
        if (self.__dict__.has_key(name)):
            return self.__dict__[name]
        else:
	    toks = name.split('_')
	    key = toks[0]
	    subkey = '_'.join(toks[1:])
	    if (self.__dict__.has_key(key)) and (self.__dict__[key].has_key(subkey)):
		return self.__dict__[key][subkey]
	    else:
		raise KeyError('Cannot determine value of "%s" from %s because there was a problem with overlaying the original data onto this %s object.' % (name,self.__dict__.keys(),ObjectTypeName.typeName(self)))

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        
    def __getitem__(self, key):
        return self.__getattr__(key)

    def __setitem__(self, key, value):
        self.__setattr__(key, value)

class MailEvent(SmartKeyedObject):
    def __init__(self,args,useSubKeys=False):
        '''args must be of type dict and must specify the name of each object {'cw':cw,'item':item}'''
        super(MailEvent, self).__init__(args,useSubKeys=useSubKeys)
        
        _utc_delta = _utils.utcDelta()
        _baseTime = _utils.getFromDateTimeStr(_utils.timeStamp(),format=_utils._formatTimeStr()) - _utc_delta
        self.__timestamp__ = time.strftime(_utils.formatTimeStr(), _baseTime.timetuple())
        
    def __str__(self):
        vars = []
        real_k = lambda foo:foo[0 if not foo.startswith('__') else 2:len(foo) if not foo.endswith('__') else len(foo)-2]
        #for k,v in self.__dict__.iteritems():
	    #try:
		#vars.append('%s="%s"' % (real_k(k),v))
	    #except:
		#vars.append('%s' % (real_k(k)))
	vars = [real_k(k) for k in self.__dict__.keys()]
        return '(%s) (%s) %s' % (str(self.__class__),self.timestamp_formatted(),', '.join(vars))
    
    def timestamp():
        doc = "timestamp"
        def fget(self):
            return self.__timestamp__
        def fset(self,ts):
            self.__timestamp__ = ts
        return locals()    
    timestamp = property(**timestamp())

    def timestamp_formatted(self):
        try:
            return self.timestamp.strftime('%b %d %H:%M')
        except:
            try:
                return _utils.getFromDateTimeStr(self.timestamp).strftime('%b %d %H:%M')
            except:
                return None
        return None
    
    def sendEmail(self):
        import sys
        print >>sys.stdout, '(%s) :: %s' % (_utils.funcName(),self)
    
if (__name__ == '__main__'):
    cw = {u'Component__c': None, u'Case_Fields__c': 'Status;Priority;Comments;Code Streams & Priority;Case Owner;Component;Customer Priority;End Date;Estimated Finish Date;PE Checkpoint;PE Owner;R&D Submission;Requested End Date;Schedule Status;Status 1st Stream;Target Analysis Done;Target Fast Track Build;Target Fix Available;Target Fix Merged;Target Release;Time Stamp / Build', u'Account__c': '00130000005wuB1AAI', u'Name': 'Watcher 00170', u'Case_Scope__c': 'Account Only', u'Case_Fields_Deferred__c': None, u'User__c': None, u'Case_Number__c': None, u'Tech_Campaign__c': None, u'Id': 'a0t30000000CgsYAAS'}
    item = {u'Alias_Email__c': 'No', u'Email__c': 'sergi@molten-magma.com', u'LastModifiedDate': -1, u'Id': 'a16300000008Px6AAE', u'Case_Watcher__c': 'a0t30000000CgsYAAS', u'Name': 'a16300000008Px6'}
    evt = MailEvent({'cw':cw,'item':item})
    print str(evt)
    print ''
    print '='*80
    print ''

    for k,v in cw.iteritems():
        evt_v = eval('evt.cw_%s' % k)
        _isPassed = False
        try:
            assert evt_v == v, '(cw_%s) :: Invalid value of "%s" but expected "%s".' % (k,evt_v,v)
            _isPassed = True
        except:
            pass
        if (_isPassed):
            print 'Passed (cw_%s) !' % (k)
    
    for k,v in item.iteritems():
        evt_v = eval('evt.item_%s' % k)
        try:
            assert evt_v == v, '(item_%s) :: Invalid value of "%s" but expected "%s".' % (k,evt_v,v)
            _isPassed = True
        except:
            pass
        if (_isPassed):
            print 'Passed (item_%s) !' % (k)
