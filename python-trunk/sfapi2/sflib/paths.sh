#
# Setup the path to include Python2.3..
#
PATH=/home/sfscript/python/bin:$PATH
#
# Setup the LD_LIBRARY_PATH so that the libraries for Python2.3 are found.
#
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/sfscript/python/lib
#
# export the ENV variables
#
export PATH LD_LIBRARY_PATH SFORCE_HOME
