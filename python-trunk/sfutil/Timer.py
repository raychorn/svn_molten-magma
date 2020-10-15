#!/usr/bin/env python2.3

'''
Provides a simple timing class

Constructor creates a timer instance with the clock running.  
'''

import time

class Timer:
    '''
    Class represents a timer with whatever resolution the system grants
    to time.time()
    '''

    def __init__(self):
        '''
        Constructs a Timer instance with the clock running
        '''

        self.__elapsedTime = None
        self.__startTime = time.time()
    ## END def __init__


    def stop(self):
        '''
        Stops the Timer instance and returns the elapsed time since the
        Timer was created/started.
        '''
        self.__elapsedTime = self.getElapsedTime()
        return self.__elapsedTime
    ## END def stop(self)

    def getStartTime(self):
        return self.__startTime
    ## END def getStartTime(self)

    def getElapsedTime(self):
        '''
        Returns the elapsed time between when the Timer was created/started
        and when the Timer was stopped. Returns None if the timer has not
        yet been stopped
        '''
        if self.__elapsedTime is None:
            return time.time() - self.__startTime 
        else:
            return self.__elapsedTime
    ## END def getTime(self)
