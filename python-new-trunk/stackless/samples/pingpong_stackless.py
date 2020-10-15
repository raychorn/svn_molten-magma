#
# pingpong_stackless.py
#
import stackless

from vyperlogix.misc import _utils

ping_channel = stackless.channel()
pong_channel = stackless.channel()

def debug_wrapper(val):
    print '%s --> %s :: val=%s' % (_utils.callersName(),_utils.funcName(),val)
    return val

def ping():
    while debug_wrapper(ping_channel.receive()): #blocks here
        print "PING"
        pong_channel.send("from ping")

def pong():
    while debug_wrapper(pong_channel.receive()):
        print "PONG"
        ping_channel.send("from pong")

stackless.tasklet(ping)()
stackless.tasklet(pong)()

# we need to 'prime' the game by sending a start message
# if not, both tasklets will block
stackless.tasklet(ping_channel.send)('startup')

stackless.run()
