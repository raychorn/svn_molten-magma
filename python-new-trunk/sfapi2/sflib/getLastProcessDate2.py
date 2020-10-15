from stat import *

def getLastProcessDate2(*args,**kw): 
    import datetime, time, os, sys
    from vyperlogix.misc import _utils
    import socket
    
    _hostname = socket.gethostname()
    #_time_bias = 48 if (_hostname.lower() == 'Misha-Lap'.lower()) else 0
    _time_bias = 0
    
    #print >>sys.stdout, '(%s) :: _time_bias is "%s" when running on "%s".' % (_utils.funcName(),_time_bias,_hostname)

    update = True
    isTime = False
    _isTime = False # this is the return value whenever isTime is True
    filename = 'LastCheckedCRNotificationDate'   
    diff_hours = 0
    diff_minutes = 0
    if (len(kw) == 0):
        kw = args[-1]
    try:
        update = kw['update']
        isTime = kw['isTime']
        filename = kw['filename']
        try:
            diff_hours = int(kw['diff_hours'])
        except:
            pass
        try:
            diff_minutes = int(kw['diff_minutes'])
        except:
            pass
    except:
        pass

    print >>sys.stdout, '(%s) :: diff_hours is "%s" and diff_minutes is "%s" when using file "%s".' % (_utils.funcName(),diff_hours,diff_minutes,filename)
    
    checksince = None 

    data_path = kw['data_path']
    if (data_path is None):
        data_path = 'dbx'
    _dbx_name = data_path.split(os.sep)[-1]
    
    log_path = kw['log_path']
    try:
        if (os.path.exists(log_path)):
            import latestFolder
	    last_run_time = latestFolder.latestFolder(top=log_path,logs=log_path.split(os.sep)[-1],dbx=data_path.split(os.sep)[-1])
	    time_sources = kw['time_source']
            time_sources = _utils.reverse(time_sources if (isinstance(time_sources,list)) else [time_sources])
            _isTimeSourceAcceptable = False
            for time_source in time_sources:
                f_time_source = os.sep.join([last_run_time,time_source])
                if (time_source is not None) and (os.path.exists(f_time_source)):
                    t_checksince = _utils.dateFromSeconds(os.stat(f_time_source)[ST_MTIME],useLocalTime=_utils.isUsingLocalTimeConversions)
                    checksince = _utils.getAsSimpleDateStr(t_checksince,fmt=_utils._formatTimeStr())
                    _isTimeSourceAcceptable = True
                    break
                else:
                    continue
            if (not _isTimeSourceAcceptable):
                toks = last_run_time.split(os.sep)
                _toks = toks[-1].split('_')
                checksince = _toks[0]+'T'+':'.join(_toks[1:])
            print >>sys.stdout, '(%s) :: log_path method produced checksince of "%s" from time_source of "%s".' % (_utils.funcName(),checksince,time_source)
            pass
    except:
        print >>sys.stderr, '%s :: Cannot determine the last time this process was run so we are using the default method and hoping for the best.' % (_utils.funcName())
        checksince = None # signal an error condition and allow the default to take-over...

    if (checksince is None):
        tmp_root = kw['cwd']
        tmpPath = os.path.join(tmp_root,filename) 
        if os.path.isfile(tmpPath): 
            curFile=open(tmpPath, "rb", 0) 
            lines = [l for l in curFile.readlines() if len(l.strip()) > 0] 
            checksince = None 
            if (sys.platform != 'win32'): 
                if (len(lines) > 0): 
                    checksince = lines[-1] 
            curFile.close() 
            os.remove(tmpPath)             
    
        if (update) or (isTime):
            try: 
                newfilename=os.path.join(tmp_root,filename) 
                file = open(newfilename, 'a') 
                if (not isTime):
                    file.write(timeStamp()) 
                    file.close() 
            except IOError: 
                msg= "There was an error writing to %s" %filename 
                print >>sys.stderr, '%s :: %s.' % (_utils.funcName(),msg)
                pass 
        
        if (isTime):
            now = datetime.date.today()            
         
        if checksince in [None,'',""]: 
            if (isTime):
                lastTime=time.mktime(time.strptime(checksince,"%Y-%m-%d"))                
                epc = datetime.date.fromtimestamp(lastTime)                
                parseEpc = epc.strftime("%Y-%m-%d")                
                dif = (epc - now)                
                if dif.days < 0:                    
                    _isTime = True             
                    dateStr = now.strftime("%Y-%m-%d")                                
                    file.write(dateStr)            
                    file.close()
                else:
                    file.write(checksince)  
                    file.close()                    
            else:
                fromSecs = time.time() 
                fromSecs = datetime.datetime.fromtimestamp(fromSecs) 
                print >>sys.stdout, '%s :: _time_bias is %s.' % (_utils.funcName(),_time_bias)
                if (diff_hours != 0):
                    if (sys.platform == 'win32') and (_time_bias > 0): 
                        diff = datetime.timedelta(hours=-_time_bias)
                    else:
                        diff = datetime.timedelta(hours=diff_hours) 
                if (diff_minutes != 0):
                    if (sys.platform == 'win32') and (_time_bias > 0): 
                        diff = datetime.timedelta(minutes=-_time_bias)
                    else:
                        diff = datetime.timedelta(minutes=diff_minutes) 
                t_delta = _utils.utcDelta()
                print >>sys.stdout, '%s :: diff is %s, t_delta is %s.' % (_utils.funcName(),diff,t_delta)
                previousHour=(fromSecs + diff) - t_delta
                previousHour=time.mktime(previousHour.timetuple())
                preHourStr = _utils.getAsDateTimeStr(previousHour,fmt=_utils.formatTimeStr())             
                checksince=preHourStr 
            if (isTime):
                dateStr = now.strftime("%Y-%m-%d")                            
                file.write(dateStr)
                file.close() 
    
        if (isTime):
            return _isTime
                   
    return checksince
    
