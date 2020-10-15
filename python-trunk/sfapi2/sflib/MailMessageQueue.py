"""
Provides both the enqueuing, storage and dequeueing of mail messages
"""
import time

from ZEO import ClientStorage
from ZODB import DB
from ZODB.POSException import ConflictError

msgQueueDbAddr = 'ebb.moltenmagma.com', 5840
msgQueueDbStor = 'msgq'

class MailMessageQueue:

    def __init__(self, test=True):
        # check for existence of shelf file
        # have a class-wide lock handle
        self.DataBase = None

        self.hasCnxInfoPrinted = False
        if test in [True, False]:
            self.testFlag = test
        else:
            self.testFlag = False
            pass
        return

    def open(self):
        "Open ZODB."
        """
        Returns a tuple consisting of:(root,connection,db,storage)
        The same tuple must be passed to close() in order to close the DB.
        """
               
        global msgQueueDbAddr
        global msgQueueDbStor
        global msgQueueDbStorTest
        
        DbAddr = msgQueueDbAddr
        DbStor = msgQueueDbStor
        if self.testFlag is True:
            DbStor = "test%s" %msgQueueDbStor
            pass
        
        if self.DataBase is None:
            # Connect to DB
            if self.hasCnxInfoPrinted is False:
                print "connecting to %s, %s" %(DbAddr, DbStor)
                self.hasCnxInfoPrinted = True
                pass
            
            storage     = ClientStorage.ClientStorage(DbAddr, storage=DbStor)
            db          = DB(storage)
            connection  = db.open()
            root        = connection.root()
            self.DataBase = (root,connection,db,storage)
            
        return self.DataBase
    ## END open
        
    def close(self):
        "Closes the ZODB."
        """
        This function MUST be called at the end of each program !!!
        See open() for a description of the argument.
        """
        if self.DataBase is not None:
            get_transaction().abort()
            self.DataBase[1].close()
            self.DataBase[2].close()
            self.DataBase[3].close()
            self.DataBase = None
            pass
        return True
    ## END close

    def commit(self, msg=None, user=None):
        "Makes all changes permanent."
        """
        DataBase, is the normal database descriptor as returned by open().
        """
        self.DataBase[0]._p_changed = 1
        if msg is not None:
            get_transaction().note(msg)
            pass
        if user is not None:
            get_transaction().setUser(user)
            pass
        
        ctr = 0
        while ctr < 3:
            try:
                get_transaction().commit()     # normal case.
                break
            except ConflictError:              # in case there are several
                time.sleep( 1 )                # commits at the same time
                ctr += 1                       # wait a second and try again.
                continue
            except KeyError:
                get_transaction().abort()
                print 'KeyError'
                return False
            except:
                get_transaction().abort()      # clean up before raising errors
                raise

        if ctr > 0:
            return False

        return True
    ## END commit


    def readUserQueue(self, queueId):
        """ Returns contents of queue with given ID. Returns empty list if no
        such queue exists """
        return self.DataBase[0].get(queueId, [])
    ## END readUserQueue


    def writeUserQueue(self, queueId, value=None):
        """ Writes (or removes) user queue from the database. Changes are
        not permanant until comitted. """
        if value is None or len(value) == 0:
            if self.DataBase[0].has_key(queueId):
                del(self.DataBase[0][queueId])
                pass
        else:
            self.DataBase[0][queueId] = value
            pass
        return
    ## END writeUserQueue

        
    ### These are some canned flows which open, operate on and close the
    ### database atomically.
    def enqueue(self, msgMap):
        """ Read the queue, Add value to the queue and write the queue
        msgList is a map of queueId:msgMap pairs"""
        
        success = False
        queue = self.open()
        if queue is False:
            self.close()
            pass

        try:
            itemCt = len(msgMap)
            for queueId, value in msgMap.items():
                userQueue = self.DataBase[0].get(queueId, [])
                
                userQueue.append(value)
                self.DataBase[0][queueId] = userQueue
                continue
            success = self.commit('%d messages' %itemCt, 'enqueue')
        finally:
            self.close()
            pass
        
        return success

    
    def clear(self):
        """ Only for the rare admin usage... clears the entire mesage queue """
        success = False
        queue = self.open()
        if queue is False:
            self.close()
            pass
       
        try:
            for queueId in queue[0].keys():
                del(queue[0][queueId])
            success = self.commit('queue cleared', 'clear')
        finally:
            self.close()
            pass
        
        return success

    def pack(self):
        """ pack the database - clear out all journaled transactions """
        success = False
        queue = self.open()
        if queue is False:
            self.close()
            pass
       
        try:
            queue[3].pack()
            success = True
        finally:
            self.close()
            return success
        

    def getQueueIds(self):
        queueIdList = []

        queue = self.open()
        if queue is False:
            self.close()
            pass
       
        try:
            queueIdList = queue[0].keys()
        finally:
            self.close()
            pass
        
        return queueIdList




