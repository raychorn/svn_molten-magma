def dummy():
    pass

def _getCaseWatcherById(d_args,callback_before=dummy,callback_after=dummy):
    '''d_args is a dict that contains the field names and values'''
    from pyax_code import soql_query
    from vyperlogix.misc import LazyImport
    sfConstant = LazyImport.LazyImport('sfConstant',locals={},globals={})
    
    soql="Select c.Account__c, c.Case_Fields__c, c.Case_Fields_Deferred__c, c.Case_Number__c, c.Case_Scope__c, c.Component__c, c.Id, c.Name, c.Tech_Campaign__c, c.User__c, c.CreatedDate, c.LastModifiedDate from Case_Watcher__c c"
    return soql_query.soql_query(soql,d_args=d_args,callback_before=callback_before,callback_after=callback_after)
