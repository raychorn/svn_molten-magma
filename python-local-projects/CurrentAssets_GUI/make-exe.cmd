@echo off
set PYTHONPATH=c:\python25;Z:\python projects\@lib

for /f %%i in ('cd') do set cwd=%%i
if exist %cwd%\dist rmdir /S /Q %cwd%\dist
if exist %cwd%\build rmdir /S /Q %cwd%\build

python -O setup.py py2exe --packages=xml.sax.drivers,xml.sax.drivers2,encodings > report-py2exe.txt

