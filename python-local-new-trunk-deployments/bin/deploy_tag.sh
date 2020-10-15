# Subversion properties
#
# $LastChangedDate: 2006-06-01 22:32:49 -0700 (Thu, 01 Jun 2006) $
# $Author: misha $
# $Revision: 232 $
# $HeadURL: http://capps.moltenmagma.com/svn/infrastructure/sfscripts/deploy_tag.sh $
# $Id: deploy_tag.sh 232 2006-06-02 05:32:49Z misha $
#
# Script to deploy sfscript(s) from SVN tag to production location (/home/sfscript)
#
TOP="/home/sfscript"
#
HOME=$TOP/@misc/script_deployments
CURRENT_FILE=$HOME/CURRENT
DEPLOYMENT_HISTORY_FILE=$HOME/DEPLOYMENT_HISTORY_FILE
SVN_HOME="https://svn.dyn-o-saur.com:8443/svn/repo1/tags/molten-magma.com/python-new-trunk/production"
#
cd $HOME
OLD_DEST=`cat $CURRENT_FILE`
#
echo "Current deployment is in: $OLD_DEST"
echo '========== The following SVN ROOT repository will be used ======================='
svn info $SVN_HOME
echo 'The following TAGS are available:'
svn list $SVN_HOME
TAG1=`svn list $SVN_HOME | tail -n 1`
echo '================================================================================='
#
echo -n "Please enter TAG (see above) to deploy, last selected by default [$TAG1]: "
read -t 60 TAG
if [ -z $TAG ]; then
	TAG=$TAG1
fi
#
CURRENT=$TAG
DEST=$HOME/$CURRENT
#
echo '========== The following directories / files will be deployed ==================='
svn info $SVN_HOME/$TAG
svn list -v $SVN_HOME/$TAG
REVISION=`svn info $SVN_HOME/$TAG | grep "Last Changed Rev:"`
echo "Files will be deployed to: $DEST"
echo '================================================================================='
read -p 'Please type yes to continue with deployment: ' -t 60 CONFIRM
if [ "$CONFIRM" != "yes" ]; then
  echo "You typed '$CONFIRM'. Exiting"
  exit
fi
#
echo "You typed 'yes'. OK, deployment will be performed."
#
if [ -d $DEST ]; then
	rm -rf $DEST
fi
mkdir $DEST
svn export --force -q $SVN_HOME/$TAG $DEST/
#
echo $CURRENT > $CURRENT_FILE
echo "$CURRENT	$SVN_HOME/$TAG	$REVISION	`date`" >> $DEPLOYMENT_HISTORY_FILE
#
echo "$HOME/bin/flip -u $DEST/test/linux/casewatcher.sh"
$HOME/bin/flip -u $DEST/test/linux/casewatcher.sh
$HOME/bin/flip -u $DEST/cron/bin/casewatcher_list.sh
chmod -R 700 $DEST/cron/
chmod -R 700 $DEST/test/linux/
chmod -R 700 $DEST/sfapi2/
#
unzip $HOME/eggs/VyperLogixLib-1.0-py2.5.egg -d $DEST
#
cd $TOP
#rm src2
#ln -s $DEST src2
#
echo "Files deployed."
#
$DEST/test/linux/casewatcher.sh
exit
