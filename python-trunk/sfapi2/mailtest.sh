#!/usr/bin/env bash
#
# if 'bash' gives us bash v1, try to relaunch script bash v2 by name
BASHVER=`echo $BASH_VERSION | cut -b 1 -`
if [ $BASHVER = "1" ]; then
    exec bash2 $0 $*
fi

PATH=/home/sfscript/python/bin:$PATH
export PATH

PYTHONPATH=${PATH}:/home/sfscript/src/sfapi2/sflib
export PYTHONPATH

python /home/sfscript/src/sfapi2/mail-test.py