import os, sys

class RuntimeContext:
    def __init__(self):
        self.__homeDir__ = ''
        self.__isProduction__ = False

        toks = os.path.abspath(os.path.curdir).split(os.sep)
        if (sys.platform == 'win32'):
            t = toks[0:2]
        else:
            t = toks[0:3]
        self.homeDir = os.sep.join(t)
        
        self.isProduction = os.path.abspath(os.path.curdir).find('/src/') > -1
        if (not os.environ.has_key('PYTHONPATH')):
            os.environ['PYTHONPATH'] = '%s/python/lib;' % (self.homeDir)
            p = ''
            if (_isProduction):
                p = '/src'
            else:
                p = '/staging'
            pp = '%s%s/sfapi2/sflib' % (self.homeDir,p)
            sys.path.insert(0,pp)
            os.environ['PYTHONPATH'] += pp
            
    def __get_homeDir(self):
        return self.__homeDir__

    def __set_homeDir(self, val):
        self.__homeDir__ = val

    def __get_isProduction(self):
        return self.__isProduction__

    def __set_isProduction(self, val):
        self.__isProduction__ = val

    homeDir = property(__get_homeDir, __set_homeDir)
    isProduction = property(__get_isProduction, __set_isProduction)
