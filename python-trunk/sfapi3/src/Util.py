"""
Various utility functions used throughout the package.
"""
import types

def booleanize(data):
    if data in (True, 1, '1', 'true'):
        return True
    elif data in (False, 0, '0', 'false', ''):
        return False
    
    raise ValueError, "invalid boolean value %s" %data
## END booleanize

def listify(maybeList):
    """
    Ensure that input is a list, even if only a list of one item
    """
    definitelyList = []
    if type(maybeList) == types.TupleType:
        definitelyList = list(maybeList)
    elif type(maybeList) != types.ListType:
        definitelyList = list([maybeList,])
    else:
        definitelyList = maybeList
        pass

    return definitelyList
## END listify

def uniq(inList):
    uniqMap = {}
    for item in inList:
        uniqMap[item] = None
        continue
    return uniqMap.keys()
## END uniq
    
