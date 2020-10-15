@echo off
cls
echo BEGIN:

set CSVPATH="not_in_salesforce.csv"

ContactsWalker.exe --csv="not_in_salesforce.csv" --folder="." --colname=eMail --logging=logging.INFO --verbose --demo --staging --username= --password=

:end
echo END!
