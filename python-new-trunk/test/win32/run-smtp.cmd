@echo off
set PYTHONPATH=C:\Python25\lib;Z:\@myMagma\python-local-new-trunk;Z:\python projects\@lib;
for /f %%i in ('cd') do set cwd=%%i
if not exist %cwd%\pop mkdir %cwd%\pop

REM BEGIN: Don't do this for production deployment
if exist %cwd%\pop\mailboxes rmdir /S /Q %cwd%\pop\mailboxes
REM END!   Don't do this for production deployment

if 0%1. == 0. goto help
if %1. == 1. python "Z:\@myMagma\python-local-new-trunk\sfapi2\sflib\smtpMailsink.py" --cwd=%cwd%\pop --host=127.0.0.1:8025
if %1. == 2. python "Z:\@myMagma\python-local-new-trunk\sfapi2\sflib\smtpMailsink.py" --cwd=%cwd%\pop --host=127.0.0.1:8025 --redirect=mailhost.moltenmagma.com:25 --bcc=rhorn@molten-magma.com
if %1. == 3. python "Z:\@myMagma\python-local-new-trunk\sfapi2\sflib\smtpMailsink.py" --cwd=%cwd%\pop --host=127.0.0.1:8025 --redirect=mailhost.moltenmagma.com:25 --bcc=raychorn@hotmail.com

:help
echo Begin: --------------------------------------------------------------------------------------------
echo "1" means run SMTP server with normal debugging behaviors (no emails get sent)
echo "2" means run SMTP server with redirect behaviors (emails do get sent via mailhost.moltenmagma.com:25, Bcc to rhorn@molten-magma.com)
echo "3" means run SMTP server with redirect behaviors (emails do get sent via mailhost.moltenmagma.com:25, Bcc to raychorn@hotmail.com)
echo END! ----------------------------------------------------------------------------------------------

:end

