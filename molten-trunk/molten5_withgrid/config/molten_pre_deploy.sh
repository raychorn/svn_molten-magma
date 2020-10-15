#!/bin/bash
#
# Pre-deploy script, run to prepare server for MOLTEN2 application deployment.
# This script needs to be run only once, as root
#
# Misha, 9/29/2006
#
# Step 1: Create directories, links, startup files
#
#mkdir -p /etc/mongrel_cluster
#chown -R admin:admin /etc/mongrel_cluster
#
#mkdir -p /etc/rails
#chown admin:admin -R /etc/rails
#
#mkdir -p /var/www/apps/
#chown -R admin:admin /var/www/apps/
#
# Step 2: Prepare Mongrel cluster
# setup an mongrel_cluster start script in /etc/init.d
#ln -s /usr/local/lib/ruby/gems/1.8/gems/mongrel_cluster-0.2.0/resources/mongrel_cluster /etc/init.d/mongrel_cluster
#chmod +x /etc/init.d/mongrel_cluster
# set mongrel to start at boot
#/sbin/chkconfig --level 345 mongrel_cluster on
#
# Step 3: Prepare Appache web server
#echo "#" > dummy.file
#echo "# Added to support MOLTEN application, Misha" >> dummy.file
#echo "Include /etc/rails/*.conf" >> dummy.file
#echo "NameVirtualHost *:80" >> dummy.file
#echo "# end of change" >> dummy.file
#
#cat /usr/local/apache2/conf/httpd.conf dummy.file > new.httpd.conf
#cp new.httpd.conf /usr/local/apache2/conf/httpd.conf
#
# setup an apache2 start script in /etc/init.d/ (symlink /usr/local/apache2/bin/apachectl)
#ln -s /usr/local/apache2/bin/apachectl /etc/init.d/httpd2
# start Apache
#/etc/init.d/httd2 start
#
exit
