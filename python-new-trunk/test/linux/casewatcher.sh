#!/bin/bash
#
# if 'bash' gives us bash v1, try to relaunch script bash v2 by name
BASHVER=`echo $BASH_VERSION | cut -b 1 -`
if [ $BASHVER = "1" ]; then
    exec bash2 $0 $*
fi

PYTHON25=/home/sfscript/@misc/python25
PATH=$PYTHON25/bin:$PATH
export PATH

TOP="/home/sfscript"
#
HOME=$TOP/@misc/script_deployments
CURRENT_FILE=$HOME/CURRENT
OLD_DEST=`cat $CURRENT_FILE`

PYTHONPATH=$PYTHON25:$HOME/$OLD_DEST
export PYTHONPATH

echo PATH=$PATH
echo PYTHONPATH=$PYTHONPATH
python $HOME/$OLD_DEST/sfapi2/sflib/CaseWatcherList2.py
