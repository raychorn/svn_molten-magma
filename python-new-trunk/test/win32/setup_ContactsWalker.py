from distutils.core import setup
import py2exe

if (0):
    packages=['lib']
    includes=[]
    excludes=[]

    setup(
        options = {"py2exe": {"compressed": 1,
                              "optimize": 2,
                              "ascii": 1,
                              "bundle_files": 1,
                              "packages": packages,
                              "includes": includes,
                              "excludes": excludes}},

        console=['Z:\\@myMagma\\python-local-new-trunk\\sfapi2\\sflib\\ContactsWalker.py'],
        )
else:
    includes = []
    setup(
            console=['Z:\\@myMagma\\python-local-new-trunk\\sfapi2\\sflib\\ContactsWalker.py'],
            packages=['Z:\\python projects\\@lib\\lib'],
            options = {"py2exe": {"compressed": 1,
                                  "optimize": 2,
                                  "ascii": 1,
                                  "bundle_files": 1,
                                  "includes": includes,
                                  }
                       },
            zipfile = None,
        )
