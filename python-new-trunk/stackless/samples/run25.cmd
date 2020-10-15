@echo off

set PYTHONPATH=c:\python25\lib;Z:\@myMagma\python-local-new-trunk;Z:\python projects\@lib;
c:\python25\python25.exe c:\python25\lib\timeit.py -s"import hackysacker_threaded" hackysacker_threaded.runit(10,1000,0)
