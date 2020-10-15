"""
Run this from the gendoc shell script in the bin directory

Author:		Kevin Shuk <surf@surfous.com>
Date:		Sep 17, 2005
Copyright: 	(c) 2005, Kevin Shuk
                All Rights Reserved
"""
ident = "$ID: $"

import sys
from pydoc import writedocs

writedocs(sys.argv[1])
