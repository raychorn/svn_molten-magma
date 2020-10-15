from sfCrudObject import SFCrudObject
from sfMagma import SFMagmaTool


class SFSolution(SFCrudObject):
    obj = "Solution"

    def findMaxSolutionNumber(klass, sfTool):
        "kind of a hacky way to determine the highest soution number"
        testVal = 5000 # bump this higher after we have more solutions
        testInc = 2000

        prevQueryResult = []

        while True:
            testMinStr = "%08d" %testVal
            testVal += testInc
            soql = "Select Id, SolutionNumber from Solution where SolutionNumber > '%s'" %(testMinStr)
            solutions = klass.querySoql(sfTool, soql)

            if solutions == []:
                break

            prevQueryResult = solutions
            continue

        solNumList = []
        for solution in prevQueryResult:
            solData = solution.getDataMap()
            solNumList.append(solData.get('SolutionNumber','00000000'))
            continue
        solNumList.sort()

        return solNumList[-1]
    
    findMaxSolutionNumber = classmethod(findMaxSolutionNumber)
    ## END findMaxSolutionNumber
   
if __name__ == "__main__":
    sfTool = SFMagmaTool()

    solutionNumber = SFSolution.findMaxSolutionNumber(sfTool)

    print solutionNumber
