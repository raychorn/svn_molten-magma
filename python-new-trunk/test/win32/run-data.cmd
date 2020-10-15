@echo off
cls
echo BEGIN:

set PYTHONPATH=C:\Python25\lib;Z:\@myMagma\python-local-new-trunk;Z:\python projects\@lib;

for /f %%i in ('cd') do set cwd=%%i

if %1. == 1. python "Z:\@myMagma\python-local-new-trunk\sfapi2\sflib\DataWalker.py" --csv="Z:\@myMagma\!data\Pyramid 7.0.0 MCL2 (08-05-2008)\report1217960198803.csv" --folder="Z:\@myMagma\python-local-new-trunk\test\win32" --colname="Case Number" --logging=logging.INFO --notverbose --col2rename=Name --old="Pyramid 7.0.0 MCL2" --new="Pyramid 7.0.0"
if %1. == 2. python "Z:\@myMagma\python-local-new-trunk\sfapi2\sflib\DataWalker.py" --csv="Z:\@myMagma\!data\Pyramid 7.0.0 MCL2 (08-05-2008)\report1217960198803.csv" --folder="Z:\@myMagma\python-local-new-trunk\test\win32" --colname="Case Number" --logging=logging.INFO --notverbose --col2rename=Name --old="Pyramid 7.0.0 MCL2" --new="Pyramid 7.0.0" --commit

if %1. == . goto error

profiler-stats.cmd %cwd%\logs\profiler_report.txt

goto end

:error
echo Begin: -------------------------------------------------------
echo "1" means Pyramid 7.0.0 MCL2 (08-05-2008)
echo "2" means Pyramid 7.0.0 MCL2 (08-05-2008) with commit
echo END! ---------------------------------------------------------

:end

echo END!
