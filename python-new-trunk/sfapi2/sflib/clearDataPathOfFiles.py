def clearDataPathOfFiles(p,ext='.dbx'):
    import os, sys
    
    for fname in [fname for fname in os.listdir(p) if (fname.endswith(ext) > -1)]:
	_fname = os.sep.join([p, fname])
	if (os.path.exists(_fname)):
	    try:
		os.remove(_fname)
	    except:
		pass
	    
