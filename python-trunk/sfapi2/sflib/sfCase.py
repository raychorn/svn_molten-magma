"""
Partial re-implementation of sfCr.py based on the CrudObject base class.
The chief difference is that sfCr.py is a composite object in that it loads
auxiliary objects linked to the selected CR. This implementation is intended to
be the CR object alone. The desired pattern for the composite object under the CrudObject model would be another class which would contain both the CR and
auxiliary objects.
"""

from sfCrudObject import SFCrudObject, DetailRecordMixin

class SFCase(SFCrudObject):
    obj = "Case"

    def queryCaseNumber(klass, caseNumber, fields='all'):
        """
        return a single case having the specified number
        """
        caseObj = None
        # format CR num into 8 digit zero padded string
        caseNumber = '%08d' %int(caseNumber)

        where = [['CaseNumber','=', caseNumber]]
        objList = klass.queryWhere(where, fields)
        if len(objList) > 0:
            caseObj = objList[0]
            pass

        return caseObj
    queryCaseNumber = classmethod(queryCaseNumber)
    ## END queryCaseNumber

    def findMaxCaseNumber(klass, sfTool):
        "kind of a hacky way to determine the highest case number"
        testVal = 39900 # bump this higher after we have more cases
        testInc = 2000

        prevQueryResult = []

        while True:
            testMinStr = "%08d" %testVal
            testVal += testInc
            soql = "Select Id, CaseNumber from Case where CaseNumber > '%s'" %(testMinStr)
            cases = klass.querySoql(sfTool, soql)

            if cases == []:
                break

            prevQueryResult = cases
            continue

        caseNumList = []
        for case in prevQueryResult:
            caseData = case.getDataMap()
            caseNumList.append(caseData.get('CaseNumber','00000000'))
            continue
        caseNumList.sort()

        return caseNumList[-1]
    
    findMaxCaseNumber = classmethod(findMaxCaseNumber)
    ## END findMaxCaseNumber    

## END class SFCase

        
class SFCaseComment(SFCrudObject, DetailRecordMixin):
    obj = "CaseComment"
## END class SFCaseComment
   
