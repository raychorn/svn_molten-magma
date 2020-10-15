@echo off
cls
echo BEGIN:

set PYTHONPATH=C:\Python25\lib;Z:\@myMagma\python-local-new-trunk;Z:\python projects\@lib;

for /f %%i in ('cd') do set cwd=%%i
if not exist %cwd%\logs-old mkdir %cwd%\logs

python "Z:\@myMagma\python-local-new-trunk\sfapi2\sflib\ContactsWalker.py" --logging=logging.INFO --verbose --unix

goto end

:error
echo Begin: -------------------------------------------------------
echo END! ---------------------------------------------------------

:end

echo END!
