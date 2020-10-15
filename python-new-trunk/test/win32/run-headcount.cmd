@echo off
cls
echo BEGIN:
set PYTHONPATH=C:\Python25\lib;Z:\@myMagma\python-local-new-trunk;Z:\python projects\@lib;
for /f %%i in ('cd') do set cwd=%%i
if not exist %cwd%\logs mkdir %cwd%\logs

set CSVPATH="Z:\@myMagma\!Headcount Data\11-2008\Headcount Report - November 2008 120108 LA.csv"

if %1. == 1. python "Z:\@myMagma\python-local-new-trunk\sfapi2\sflib\MagmaUsersWalker.py" --input=%CSVPATH% --folder=%cwd% --logging=logging.INFO --verbose --customlog --username=rhorn@molten-magma.com -password=Peek@b99FPAXKbB6DuwqfvHaROgprrUe --_staging > %cwd%\report_headcount.txt

if %1. == . goto error

profiler-stats.cmd %cwd%\logs\profiler_report.txt

goto end

:error
echo You forgot to use "1" but try "1" !

:end
echo END!
