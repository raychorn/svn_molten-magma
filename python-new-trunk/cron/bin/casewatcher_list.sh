#!/usr/bin/env bash
#
# if 'bash' gives us bash v1, try to relaunch script bash v2 by name
BASHVER=`echo $BASH_VERSION | cut -b 1 -`
if [ $BASHVER = "1" ]; then
    exec bash2 $0 $*
fi

/home/sfscript/src/sfapi2/sfcron/bin/casewatcher_list2 -l >> /home/sfscript/log/CaseWatcher.log
/home/sfscript/src/sfapi2/sfcron/bin/custom_notify -l >> /home/sfscript/log/CaseWatcher.log
/home/sfscript/src/sfapi2/sfcron/bin/custom_sendnotif -l >> /home/sfscript/log/CaseWatcher.log

