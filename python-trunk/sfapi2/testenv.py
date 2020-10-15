#!/usr/bin/env python2.3

import sys, os
from smtplib import *

def sendMail(msg, to='sf_ops@molten-magma.COM'):
    """ Send email to someone """
    mailServer = SMTP('mail.moltenmagma.com')
    mstat = mailServer.sendmail(to,[to],msg)
    return mstat
    

def main_CL():
    args = sys.argv
    print 'sys.argv %s'%args
    sub = 'Test subject'
    if len(args) >1 and args[1] != '':
        sub = args[1]
    msg = 'Subject: %s\r\n'%sub
    msg += 'sys.path is %s\n'%sys.path
    stat = sendMail(msg)
    print stat
        

if __name__ == "__main__":
    main_CL()
