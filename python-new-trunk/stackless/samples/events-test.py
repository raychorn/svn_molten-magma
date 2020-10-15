import stackless
from vyperlogix.stackless.framework.events.Reporter import Reporter
from vyperlogix.stackless.framework.events.Switch import Switch

reporter = Reporter()
switch = Switch(0,reporter) #create switch and attach reporter as output.

switch(1)

switch(0)

switch(1)
