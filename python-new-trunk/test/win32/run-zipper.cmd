@echo off
cls
echo BEGIN:

set PYTHONPATH=C:\Python25\lib;Z:\@myMagma\python-local-new-trunk;Z:\python projects\@lib;Z:\@myMagma\python-local-new-trunk\sfapi2\sflib;

for /f %%i in ('cd') do set cwd=%%i

python "Z:\@myMagma\python-local-new-trunk\test\win32\makeZip.py"

python "Z:\@myMagma\python-local-new-trunk\test\win32\sftp.py" --server=tide2 --source=Z:\@myMagma\python-local-new-trunk\CaseWatcher_1_0.zip --dest=/home/rhorn/@4/CaseWatcher_1_0.zip

python "Z:\@myMagma\python-local-new-trunk\test\win32\sftp.py" --server=tide2 --source=Z:\@myMagma\python-local-new-trunk\CaseWatcher_1_0.egg --dest=/home/rhorn/@2/CaseWatcher_1_0.egg

echo END!
