"""
Mixin class which provides methods to assist in the building, checking and
management of queries
"""
import types


class SoqlHelperMixin:

    def checkFieldnames(fieldnames):
        """ Make sure that Id is in the list of fieldnames """

        if fieldnames == types.TupleType:
            fieldnames = list(fieldnames)
        elif fieldnames != types.ListType:
            fieldnames = list([fieldnames])
            pass
            
        idStr = None
        if 'Id' in fieldnames:
            idStr = 'Id'
        elif 'ID' in fieldnames:
            idStr = 'ID'
        elif 'id' in fieldnames:
            idStr = 'id'
            pass

        if idStr is not None:
            fieldnames.remove(idStr)
            pass

        fieldnames.inster(0, 'Id')
        return fieldnames
    checkFieldnames = staticmethod(checkFieldnames)
