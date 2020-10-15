"""
Helpers for gathering login information

Author:		Kevin Shuk <surf@surfous.com>
Date:		Sep 16, 2005
Copyright: 	(c) 2005, Kevin Shuk
                All Rights Reserved
"""
ident = "$ID: $"

import base64

def getinput(prompt="Input"):
    input = raw_input(prompt+': ')
    return input

def getpass(prompt = 'Password'):
    """ password = getpass(prompt = 'Password')
    
    Get a password with echo turned off
    - restore terminal settings at end.
    """
    
    import sys
    
    if not sys.stdin.isatty():
        passwd = sys.stdin.read()
        while len(passwd) > 0 and passwd[-1] in ('\r', '\n'):
            passwd = passwd[:-1]
            return passwd
        pass
    
    import termios
    if not hasattr(termios, 'ECHO'):
        import TERMIOS		# Old module for termios constants
    else:
        TERMIOS = termios	# Now included
        pass
    
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)	# a copy to save
    new = old[:]			# a copy to modify
    
    new[3] = new[3] & ~TERMIOS.ECHO	# 3 == 'lflags'
    try:
        termios.tcsetattr(fd, TERMIOS.TCSADRAIN, new)
        try: passwd = getinput(prompt)
        except (KeyboardInterrupt, EOFError): passwd = None
        pass
    finally:
        termios.tcsetattr(fd, TERMIOS.TCSADRAIN, old)
        pass

    sys.stdout.write('\n')
    sys.stdout.flush()
    return passwd


if __name__ == "__main__":
    print
    print "Encode a password in base64\n"
    print "  NOTE - this is NOT heavy security. It merely provides an alternative"
    print "  store storing a password as plaintext in a config file."
    print "    You have been warned.\n"

    pw = getpass("Password to encode")
    encpw = base64.encodestring(pw)

    print "Encoded password is:\n"
    print encpw
