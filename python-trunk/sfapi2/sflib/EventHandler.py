from sfUtil import *

class EventHandler:
    """
    Interface for modelling event handlers using scan->filter->action.
    """

    # event code will be set in actual event implementations
    eventcode = None

    def __init__(self, sfTool, opts=None):

        # store a local copy.
        self.sfb = sfTool

        self.opts = opts

        self.rawEventList = []
        self.actionList = []
        
        return

    def poll(self):
        """ Query for objects meeting the event's basic condition(s)
        and store them in rawEventList
        """
        raise NotImplementedError

    def filter(self):
        """ Filter rawEventList against exclusion criteria and store
        passing events in the actionList
        """
        raise NotImplementedError

    def action(self):
        """ Act upon each element of actionList, performing the prescribed
        action(s) AND setting the event exclusion criteria so that the same
        event is not triggered again.
        """
        raise NotImplementedError

    def flow(self):
        """ Very basic flow - scan for events, filter events against
        exclusion criteria, and act on the surviving events
        """
        self.poll()
        # log the detected events
        msg = "%d raw events detected for event code %s" %(len(self.rawEventList), self.eventcode)
        self.sfb.setLog(msg, 'info')
        print msg

        self.filter()
        # log the filtered events
        msg = "%d new events detected for event code %s" %(len(self.actionList), self.eventcode)
        self.sfb.setLog(msg, 'info')
        print msg

        self.action()
        return
    
    
