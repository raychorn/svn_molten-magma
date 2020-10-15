TOP="/home/sfscript"
#
HOME=$TOP/@misc/script_deployments
CURRENT_FILE=$HOME/CURRENT
#
cd $HOME
OLD_DEST=`cat $CURRENT_FILE`

flip -u $OLD_DEST/test/linux/casewatcher.sh
