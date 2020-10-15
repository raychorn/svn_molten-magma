from vyperlogix.hash import lists

def dummy():
    pass

def soql_query(soql,d_args=lists.HashedLists2(),callback_before=dummy,callback_after=dummy):
    import types, logging
    from vyperlogix.misc import _utils
    from pyax_code import sf_query
    from vyperlogix.misc import LazyImport
    sfConstant = LazyImport.LazyImport('sfConstant',locals={},globals={})
    
    def getObjFromSOQL(_soql):
	sf_obj = None
	toks = _soql.split()
	i = _utils.findInListSafely(toks,'from')
	if (i > -1):
	    try:
		sf_obj = [toks[i+1]]
	    except:
		pass
	    try:
		sf_obj.append(toks[i+2])
	    except:
		sf_obj.append(sf_obj[0][0].lower())
	return tuple(sf_obj)
    
    def whereClause(dargs,t_objName):
	'''dargs is the dict that contains the field specs and t_objName is the name of the object tuple (objName,prefix).'''
	isQuotable = lambda soap_type: any([soap_type.find(t) > -1 for t in [':ID',':string']])
	l_where = []
	if (lists.isDict(dargs)):
	    d_meta = sfdc.describeSObject(t_objName[0])
	    for k,v in dargs.iteritems():
		if (k != 'sfdc'):
		    soap_type = d_meta.getFieldSoapType(k)
		    if (soap_type):
			_isQuotable = isQuotable(soap_type)
			_quote = '' if (not _isQuotable) else "'"
			l_where.append("%s.%s = %s%s%s" % (t_objName[-1],k,_quote,v,_quote))
	return '' if (len(l_where) == 0) else ' where %s' % ('and'.join(l_where))
    
    sfdc = d_args['sfdc']
    if (soql is not None) and (len(soql) > 0):
	t_objName = getObjFromSOQL(soql)
	_where = whereClause(d_args,t_objName)
	soql="%s%s" % (soql,_where)
	ret = sf_query._sf_query(sfdc,soql,callback_before,callback_after)
	if ret in sfConstant.BAD_INFO_LIST:
	    logging.info("(%s) :: Could not find any %s Object(s) for %s." % (_utils.funcName(),t_objName[0],''.join(['%s.%s of %s' % (t_objName[-1],k,v) for k,v in d_args.iteritems()])))
	else: 
	    logging.info('(%s) soql=%s' % (_utils.funcName(),soql))
	    return ret
    else:
	logging.error('(%s) SOQL cannot not be missing or None however now it is "%s" and this is unacceptable.' % (_utils.funcName(),soql))
    return None

if (__name__ == '__main__'):
    from pyax.connection import Connection
    from pyax.exceptions import ApiFault
    from pyax_code.context import getSalesForceContext
    
    _isStaging = True
    _ctx = getSalesForceContext()
    if (_isStaging):
	_srvs = _ctx.get__login_servers()
	print '_srvs=%s' % str(_srvs)
	if (_srvs.has_key('production')) and (_srvs.has_key('sandbox')):
	    _ctx.login_endpoint = _ctx.login_endpoint.replace(_srvs['production'],_srvs['sandbox'])
	print '_ctx.login_endpoint=%s' % str(_ctx.login_endpoint)
    sfdc = Connection.connect('rhorn@molten-magma.com', 'Peekab00', context=_ctx)
    print 'sfdc=%s' % str(sfdc)
    print 'sfdc.endpoint=%s' % str(sfdc.endpoint)

    d = lists.HashedLists2({'sfdc':sfdc, 'CaseId__c':'50030000000BmvrAAC'})
    soql = "Select c.CaseId__c, c.ChangedFieldName__c, c.Id, c.IsDeleted, c.LastModifiedById, c.LastModifiedDate, c.Name, c.OldFieldValue__c from CaseWatcherChangedField__c c"
    ret = soql_query(d_args=d,soql=soql)
