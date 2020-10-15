from vyperlogix.misc import ObjectTypeName
from vyperlogix.misc.ObjectTypeName import __typeName as ObjectTypeName__typeName

class SfStats:
    def __init__(self):
        self.__query_count__ = 0
        pass
    
    def __str__(self):
        return '(%s) Query Count=%s' % (ObjectTypeName__typeName(self.__class__),self.query_count)
    
    def count_query(self):
        self.__query_count__ += 1
    
    def query_count():
        doc = "query_count"
        def fget(self):
            return self.__query_count__
        return locals()    
    query_count = property(**query_count())
