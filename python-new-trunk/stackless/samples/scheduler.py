import stackless

def print_three_times(x):
    print "1:", x
    stackless.schedule()
    print "2:", x
    stackless.schedule()
    print "3:", x
    stackless.schedule()

stackless.tasklet(print_three_times)('first')
stackless.tasklet(print_three_times)('second')
stackless.tasklet(print_three_times)('third')

stackless.run()
