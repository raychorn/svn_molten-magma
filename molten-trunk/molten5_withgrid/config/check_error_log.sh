#!/bin/bash
# Check error log file for errors
#
grep -i error /var/www/apps/molten/shared/log/salesforce.log | cut -b -100
#
exit
