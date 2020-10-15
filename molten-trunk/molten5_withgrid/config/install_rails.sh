#!/bin/bash
#
# Script to install all necessary software for MOLTEN application to run
# run this only once, as root, check manually
#
HOME="/usr/local/src"
#APACHE2=http://apache.mirrors.pair.com/httpd/httpd-2.2.3.tar.gz
APACHE2=http://www.apache.org/dist/httpd/httpd-2.2.3.tar.gz
READLINE=ftp://ftp.gnu.org/gnu/readline/readline-5.1.tar.gz
RUBY=ftp://ftp.ruby-lang.org/pub/ruby/1.8/ruby-1.8.4.tar.gz
RUBYGEMS=http://rubyforge.iasi.roedu.net/files/rubygems/rubygems-0.9.0.tgz
FERRET_VERSION="0.9.4"
MYSQLGEM_VERSION="2.7"
MONGREL_VERSION="0.3.13.4"
MONGREL_CLUSTER_VERSION="0.2.0"
DBI_VERSION="1.32-5"
MYSQL_VERSION="5.0.24a-0"
MYSQL_RPM_PARMS="-ivh"  #to install new, from the scratch
#MYSQL_RPM_PARMS="-U"  #to upgrade existing

cd $HOME
sudo wget $APACHE2
sudo tar xzvf httpd-*.tar.gz
cd httpd-2.2.3
sudo ./configure  --prefix=/usr/local/molten-apache2 --enable-deflate --enable-proxy --enable-proxy-html --enable-proxy-balancer --enable-rewrite --enable-cache  --enable-mem-cache --enable-ssl --enable-headers
#sudo ./configure  --prefix=/usr/local/apache2 --enable-deflate --enable-proxy --enable-proxy-html --enable-proxy-balancer --enable-rewrite --enable-cache  --enable-mem-cache --enable-ssl --enable-headers --with-apr=/usr/local/apr-httpd/ --with-apr-util=/usr/local/apr-util-httpd/sudo make
sudo make install

cd $HOME
sudo wget $READLINE
sudo tar xzvf readline-*.tar.gz
cd readline-*
sudo ./configure --prefix=/usr/local
sudo make
sudo make install

cd $HOME
sudo wget $RUBY
sudo tar xzvf ruby-1.8.4.tar.gz
cd ruby-1.8.4
sudo ./configure --prefix=/usr/local --enable-pthread --with-readline-dir=/usr/local
sudo make
sudo make install
sudo make install-doc

cd $HOME
sudo wget $RUBYGEMS
sudo tar xzvf rubygems-0.9.0.tgz
cd rubygems-0.9.0
sudo /usr/local/bin/ruby setup.rb

cd $HOME
sudo gem install rails --include-dependencies
sudo gem install daemons
sudo gem install mysql --version $MYSQLGEM_VERSION -- --with-mysql-config
sudo gem install mongrel --source=http://mongrel.rubyforge.org/releases/ --include-dependencies --version $MONGREL_VERSION
sudo gem install mongrel_cluster --version $MONGREL_CLUSTER_VERSION
sudo gem install ferret --version $FERRET_VERSION
sudo gem install activesalesforce
sudo gem install net-ssh
sudo gem install capistrano
sudo gem install termios

#

# Install SVN client, Misha
cd $HOME
sudo wget http://the.earth.li/pub/subversion/summersoft.fay.ar.us/pub/subversion/latest/rhel-3/bin/neon-0.24.7-1.i386.rpm
sudo wget http://the.earth.li/pub/subversion/summersoft.fay.ar.us/pub/subversion/latest/rhel-3/bin/subversion-1.3.0-1.rhel3.i386.rpm
#
sudo rpm -ivh neon-0.24.7-1.i386.rpm
sudo rpm -ivh subversion-1.3.0-1.rhel3.i386.rpm
#
# Install mySQL server, client, shared libs and headers, Misha
cd $HOME
# get and install Perl DBI
sudo wget ftp://rpmfind.net/linux/redhat/9/en/os/i386/RedHat/RPMS/perl-DBI-1.32-5.i386.rpm
sudo rpm -ivh perl-DBI-$DBI_VERSION.i386.rpm
# get server, client, shared libs and hearders
wget http://dev.mysql.com/get/Downloads/MySQL-5.0/MySQL-server-standard-$MYSQL_VERSION.rhel4.i386.rpm/from/http://mysql.mirrors.pair.com/
wget http://dev.mysql.com/get/Downloads/MySQL-5.0/MySQL-client-standard-$MYSQL_VERSION.rhel4.i386.rpm/from/http://mysql.mirrors.pair.com/
wget http://dev.mysql.com/get/Downloads/MySQL-5.0/MySQL-shared-standard-$MYSQL_VERSION.rhel4.i386.rpm/from/http://mysql.mirrors.pair.com/
wget http://dev.mysql.com/get/Downloads/MySQL-5.0/MySQL-devel-standard-$MYSQL_VERSION.rhel4.i386.rpm/from/http://mysql.mirrors.pair.com/
#
sudo sudo rpm $MYSQL_RPM_PARMS MySQL-server-standard-$MYSQL_VERSION.rhel4.i386.rpm
sudo sudo rpm $MYSQL_RPM_PARMS MySQL-client-standard-$MYSQL_VERSION.rhel4.i386.rpm
sudo rpm $MYSQL_RPM_PARMS MySQL-shared-standard-$MYSQL_VERSION.rhel4.i386.rpm
sudo rpm $MYSQL_RPM_PARMS MySQL-devel-standard-$MYSQL_VERSION.rhel4.i386.rpm
#
exit