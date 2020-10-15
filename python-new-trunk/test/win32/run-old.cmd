@echo off
set PYTHONPATH=C:\Python25\lib;Z:\@myMagma\python-local-new-trunk;Z:\python projects\@lib;
for /f %%i in ('cd') do set cwd=%%i
if not exist %cwd%\logs-old mkdir %cwd%\logs-old
python "Z:\@myMagma\python-local-new-trunk\sfapi2\sflib\CaseWatcherList.py" %cwd% > %cwd%\logs-old\_stdout.txt

profiler-stats.cmd %cwd%\logs-old\_stdout.txt
