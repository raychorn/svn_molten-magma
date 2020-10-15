@echo off

set PYTHONPATH=c:\StacklessPython25\lib;Z:\@myMagma\python-local-new-trunk;Z:\python projects\@lib;
c:\StacklessPython25\python25.exe c:\StacklessPython25\lib\timeit.py -s"import hackysacker" hackysacker.runit(10,1000,0)
