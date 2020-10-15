@echo off
cls
echo BEGIN:

set PYTHONPATH=C:\Python25\lib;Z:\@myMagma\python-local-new-trunk;Z:\python projects\@lib;Z:\@myMagma\python-local-new-trunk\sfapi2\sflib;

for /f %%i in ('cd') do set cwd=%%i

python -m cProfile -s cumulative "Z:\@myMagma\python-local-new-trunk\sfapi2\sflib\dbtest.py" %1 > report-dbtest.txt

goto end

:error
echo 

:end

echo END!
