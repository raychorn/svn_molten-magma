def getSalesForceContext():
    from vyperlogix.decorators import addto
    from pyax.context import Context

    _ctx = Context()

    @addto.addto(_ctx)
    def get__login_servers(self):
	try:
	    return self.__dict__['_Context__login_servers']
	except:
	    pass
	return []
    
    return _ctx
