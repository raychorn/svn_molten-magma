@echo on

set old_path = %Path%
set Path=c:\python23;c:\python23\scripts;%Path%

set old_PYTHONPATH=%PYTHONPATH%
set _PYTHONPATH=C:\Python23
set PYTHONPATH=%_PYTHONPATH%\lib;sfapi2\sflib;etc;sfapi3\src

SET PYSFDC_HOME='.'

del Z:\@myMagma\python-docs\sfapi2\sflib\*.* < y
del Z:\@myMagma\python-docs\sfapi2\sfutil\*.* < y
del Z:\@myMagma\python-docs\sfapi2\wsdl\*.* < y
del Z:\@myMagma\python-docs\sfapi3\src\*.* < y
del Z:\@myMagma\python-docs\sfapi3\wsdl\*.* < y

%_PYTHONPATH%\pythonw.exe %_PYTHONPATH%\Scripts\epydoc.pyw sfapi2_sflib.prj -prj_url=http://localhost/magma/python-docs/sfapi2/sflib -modules=Z:\@myMagma\python-trunk\sfapi2\sflib\*.py+
%_PYTHONPATH%\pythonw.exe %_PYTHONPATH%\Scripts\epydoc.pyw sfapi2_sfutil.prj -prj_url=http://localhost/magma/python-docs/sfapi2/sfutil -modules=Z:\@myMagma\python-trunk\sfapi2\sfutil\*.py+
%_PYTHONPATH%\pythonw.exe %_PYTHONPATH%\Scripts\epydoc.pyw sfapi2_wsdll.prj -prj_url=http://localhost/magma/python-docs/sfapi2/wsdl -modules=Z:\@myMagma\python-trunk\sfapi2\wsdl\*.py+
%_PYTHONPATH%\pythonw.exe %_PYTHONPATH%\Scripts\epydoc.pyw sfapi3_src.prj -prj_url=http://localhost/magma/python-docs/sfapi3/src -modules=Z:\@myMagma\python-trunk\sfapi3\src\*.py+
%_PYTHONPATH%\pythonw.exe %_PYTHONPATH%\Scripts\epydoc.pyw sfapi3_wsdl.prj -prj_url=http://localhost/magma/python-docs/sfapi3/wsdl -modules=Z:\@myMagma\python-trunk\sfapi3\wsdl\*.py+

set path=%old_path%
set PYTHONPATH=%old_PYTHONPATH%
set _PYTHONPATH=

echo Run done.

