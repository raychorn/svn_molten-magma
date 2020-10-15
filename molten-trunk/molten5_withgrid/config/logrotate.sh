#!/bin/bash

day=`date +%Y%m%d`
cd /var/www/apps/molten/shared/log

for log in `ls *log`; do
    mv $log $log.$day
done

find . -name "*log.*" -mtime +7 -exec rm -f '{}' \;

/etc/init.d/mongrel_cluster restart
#sleep 5
#/etc/init.d/monit restart
exit
