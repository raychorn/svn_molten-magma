@echo off
cls
echo BEGIN:

set PYTHONPATH=C:\Python25\lib;Z:\@myMagma\python-local-new-trunk;Z:\python projects\@lib;

REM set SMTPSERVER="Z:\@myMagma\python-local-new-trunk\test\win32\run-smtp.cmd"
REM set SMTPSERVER="127.0.0.1:2525"

set SMTPSERVER="127.0.0.1:8025"
set SMTPSERVER2="tide2.moltenmagma.com:8025"

for /f %%i in ('cd') do set cwd=%%i
if not exist %cwd%\logs-old mkdir %cwd%\logs

if 0%1. == 0. goto help
if %1. == 1. python "Z:\@myMagma\python-local-new-trunk\sfapi2\sflib\CaseWatcherList2.py" --notverbose --smtpserver=%SMTPSERVER% --cwd=%cwd% --logging=logging.WARNING --console_logging=logging.INFO --debug
if %1. == 2. python "Z:\@myMagma\python-local-new-trunk\sfapi2\sflib\CaseWatcherList2.py" --notverbose --smtpserver=%SMTPSERVER% --cwd=%cwd% --logging=logging.WARNING --console_logging=logging.INFO --debug --staging --username=rhorn@molten-magma.com --password=Peekab00
if %1. == 3. python "Z:\@myMagma\python-local-new-trunk\sfapi2\sflib\CaseWatcherList2.py" --verbose --smtpserver=%SMTPSERVER% --cwd=%cwd% --logging=logging.WARNING --console_logging=logging.INFO --staging --username=rhorn@molten-magma.com.stag --password=sisko7660boo
if %1. == 4. python "Z:\@myMagma\python-local-new-trunk\sfapi2\sflib\CaseWatcherList2.py" --notverbose --smtpserver=%SMTPSERVER% --cwd=%cwd% --logging=logging.WARNING --console_logging=logging.INFO --username=rhorn@molten-magma.com --password=sisko7660boo --date=2008-08-01T00:00:00
if %1. == 5. python "Z:\@myMagma\python-local-new-trunk\sfapi2\sflib\CaseWatcherList2.py" --notverbose --smtpserver=%SMTPSERVER% --cwd=%cwd% --logging=logging.WARNING --console_logging=logging.INFO 
if %1. == 6. python "Z:\@myMagma\python-local-new-trunk\sfapi2\sflib\CaseWatcherList2.py" --verbose --smtpserver=%SMTPSERVER% --cwd=%cwd% --logging=logging.WARNING --console_logging=logging.INFO --staging --initialize --username=rhorn@molten-magma.com.stag --password=sisko7660boo
REM ======== The following all use tide2.moltenmagma.com for SMTP Proxy and molten SalesForce user account. =====
if %1. == 7. python "Z:\@myMagma\python-local-new-trunk\sfapi2\sflib\CaseWatcherList2.py" --verbose --smtpserver=%SMTPSERVER2% --cwd=%cwd% --logging=logging.WARNING --console_logging=logging.INFO --staging --username=molten_admin@molten-magma.com --password=u2cansleeprWI2X9JakDlxjcuAofhggFbaf
if %1. == 8. python "Z:\@myMagma\python-local-new-trunk\sfapi2\sflib\CaseWatcherList2.py" --verbose --smtpserver=%SMTPSERVER2% --cwd=%cwd% --logging=logging.WARNING --console_logging=logging.INFO --initialize --username=molten_admin@molten-magma.com --password=u2cansleeprWI2X9JakDlxjcuAofhggFbaf


profiler-stats.cmd %cwd%\logs\profiler_report.txt

goto end

:help
echo Begin: ---------------------------------------------------------------------------------------------------
echo "1" means --debug or simulate changes for production.
echo "2" means --debug or simulate changes for staging.
echo "3" means run live code to detect changes for staging.
echo "4" means run "3" using an arbitrary start date.
echo "5" means run live code to detect changes for production.
echo "6" means run CaseWatcher Init code to clear-out old CaseWatchers and send emails for Staging.
echo ======== The following all use tide2.moltenmagma.com for SMTP Proxy and molten SalesForce user account. =====
echo "7" means run live code to detect changes for staging.  Using tide2.moltenmagma.com as the SMTP Proxy Server.
echo "8" means run CaseWatcher Init code to clear-out old CaseWatchers and send emails for Production.
echo END! -----------------------------------------------------------------------------------------------------

:end

echo END!
