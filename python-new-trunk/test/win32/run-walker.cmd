@echo off
cls
echo BEGIN:
set PYTHONPATH=C:\Python25\lib;Z:\@myMagma\python-local-new-trunk;Z:\python projects\@lib;
for /f %%i in ('cd') do set cwd=%%i
if not exist %cwd%\logs mkdir %cwd%\logs

set TOKENSPATH=Z:\@myMagma\python-local-new-trunk\test\tokens
REM set ANALYSISPATH="Z:\@myMagma\!Research WalkSCMTalus1.0\branches in set33 24jun2008 IST for TAT estimate.csv"
set ANALYSISPATH="Z:\@myMagma\!Research WalkSCMTalus1.0\set33_branches (07-10-2008-15-45).csv"

if %1. == 1.  python "Z:\@myMagma\python-local-new-trunk\sfapi2\sflib\SCM_Walker.py" --branch=talus1.0 --reload --folder=%cwd%
if %1. == 2.  python "Z:\@myMagma\python-local-new-trunk\sfapi2\sflib\SCM_Walker.py" --branch=talus1.0 --analysis --folder=%cwd%
if %1. == 2a. python "Z:\@myMagma\python-local-new-trunk\sfapi2\sflib\SCM_Walker.py" --branch=talus1.0 --reload --analysis=%ANALYSISPATH% --folder=%cwd% --logging=logging.INFO --verbose
if %1. == 3.  python "Z:\@myMagma\python-local-new-trunk\sfapi2\sflib\SCM_Walker.py" --branch=talus1.0 --analysis=%TOKENSPATH% --folder=%cwd%
if %1. == 3a. python "Z:\@myMagma\python-local-new-trunk\sfapi2\sflib\SCM_Walker.py" --branch=talus1.0 --analysis=%ANALYSISPATH% --folder=%cwd% --logging=logging.INFO --verbose
if %1. == 3b. python "Z:\@myMagma\python-local-new-trunk\sfapi2\sflib\SCM_Walker.py" --branch= --analysis=%ANALYSISPATH% --folder=%cwd%
if %1. == 4.  python "Z:\@myMagma\python-local-new-trunk\sfapi2\sflib\SCM_Walker.py" --task_branch__c=xxx --folder=%cwd%

profiler-stats.cmd %cwd%\logs\profiler_report.txt

echo END!
