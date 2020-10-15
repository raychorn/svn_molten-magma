@echo off

set old_path = %Path%
set Path=c:\python23;c:\python23\scripts;%Path%

set old_PYTHONPATH=%PYTHONPATH%
set _PYTHONPATH=C:\Python23
set PYTHONPATH=%_PYTHONPATH%\lib;sfapi2\sflib;etc;sfapi3\src

SET PYSFDC_HOME='.'

%_PYTHONPATH%\pythonw.exe %_PYTHONPATH%\Scripts\epydoc.pyw

set path=%old_path%
set PYTHONPATH=%old_PYTHONPATH%
set _PYTHONPATH=

echo Run done.

