@echo off
cls
echo BEGIN:
set PYTHONPATH=C:\Python25\lib;Z:\@myMagma\python-local-new-trunk;Z:\python projects\@lib;
for /f %%i in ('cd') do set cwd=%%i
if not exist %cwd%\logs mkdir %cwd%\logs

set CSVPATH="Z:\@myMagma\!Contacts Walker Analysis\!Research DAC leads combined\ContactsWalker Analysis\not_in_salesforce.csv"

if %1. == 1. python "Z:\@myMagma\python-local-new-trunk\sfapi2\sflib\ContactsWalker.py" --csv=%CSVPATH% --folder=%cwd% --colname=eMail --logging=logging.INFO --verbose --headers --demo --staging

if %1. == . goto error

profiler-stats.cmd %cwd%\logs\profiler_report.txt

goto end

:error
echo You forgot to use "1" so try "1" !

:end
echo END!
