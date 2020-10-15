@echo off
set PYTHONPATH=C:\Python25\lib;Z:\@myMagma\python-local-new-trunk;Z:\python projects\@lib;
for /f %%i in ('cd') do set cwd=%%i
if not exist %cwd%\pop mkdir %cwd%\pop
python "Z:\python projects\@lib\lib\sockets\pop3.py" 127.0.0.1:110 %cwd%\pop\pop3_mailbox.txt

