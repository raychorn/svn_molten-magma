@echo off
set PYTHONPATH=C:\Python25\lib;Z:\@myMagma\python-local-new-trunk;Z:\python projects\@lib;Z:\@myMagma\python-local-new-trunk\sfapi2\sflib;

 python -O setup_ContactsWalker.py py2exe --packages=xml.sax.drivers,xml.sax.drivers2
