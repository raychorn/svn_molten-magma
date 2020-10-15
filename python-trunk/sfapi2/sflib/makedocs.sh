#!/bin/sh
# 2004, June 14th
###################################################
version="3.01"
doc_path=`pwd`
latest_path=${doc_path}/${version}
lib_path='/home/sfscript/src/sfapi2/sflib'
python_path="/usr/lib/python2.3"  
python_bin="/usr/bin/python2.3"
pydoc_bin=`whereis pydoc | cut -d" " -f2`
    
# ---------------script run as root--------------------------------------------
#if [ "$USER" != "root" ];then
#    echo "Please run me as user \"root\"!"
#    exit 1
#fi
echo -n "Should I go on? [default: yes]"
read
if [ "$REPLY" = "N" -o "$REPLY" = "n" -o "$REPLY" = "No" -o "$REPLY" = "no" ]; then
   echo "Cancel Creation of new API doc files! "
   exit 1
fi
# -----------------------------------------------------------------------------
# check if path is writable
# -----------------------------------------------------------------------------
if [ -d $doc_path -a -w $doc_path ]; then

    echo "--------Checking files directories------------------------------"
    cmd=`mkdir -p ${latest_path}`
    
    sflib_files=`ls ${lib_path}/*.py`
    for lfile in ${sflib_files}
    do
       ${pydoc_bin} -w $lfile
       echo " created pydoc for $lfile"
       
    done
    mv *.html ${latest_path}
    echo "------------------------------------------------------------------------------"
    echo " Moved all html files to ${latest_path}"
    echo "------------------------------------------------------------------------------"
    echo "Created Python Docs for version ${version} in ${latest_path}"
    echo "------------------------------------------------------------------------------"
    
else
    echo "$install_path does not exist or is not writable for this user [user:\"$USER\"]"
    exit 1
fi
