# =============================================================================
# ABOUT THIS DEPLOYMENT RECIPE FILE
# =============================================================================
# This set of recipes is customized for a mongrel_cluster setup with
# an apache2 frontend using mod_proxy_balancer
#
# latest version is located here:
#  http://www.slingshothosting.com/files/apache2_2_mongrel_deploy.rb
#
# =============================================================================
# PREREQUISITES
# =============================================================================
# Apache2 must be configured to load files in /etc/rails, you can do that
# by putting this line in httpd.conf:
#
#  Include /etc/rails/*.conf
#
# You'll also want to turn on Named Virtual hosting, with:
#
# NameVirtualHost *:80
#
# Also, please be sure to setup mongrel_cluster to start on boot, here is one
# way to do this:
#
# ln -s /usr/lib/ruby/gems/1.8/gems/mongrel_cluster-x.x.x/resources/mongrel_cluster /etc/init.d/mongrel_cluster
# ln -s /usr/local/lib/ruby/gems/1.8/gems/mongrel_cluster-0.2.0/resources/mongrel_cluster /etc/init.d/mongrel_cluster
# ln -s /var/www/apps/molten/shared/system/acts_as_ferret /etc/init.d/acts_as_ferret
# chmod +x /etc/init.d/mongrel_cluster
# chmod +x /etc/init.d/acts_as_ferret
#
# redhat/centos/fedora:
# /sbin/chkconfig --level 345 mongrel_cluster on
#
# debian:
# /usr/sbin/update-rc.d mongrel_cluster defaults
#
# TODO:
#  - add ability to specify whether or not to relink tmp shared session/cache data
#  - add in default ferret_index, rails_cron, backgrounDRb, etc. tasks
#  - make restart_web task a little less svs-v specific
#  - create some pre-pre setup tasks:
#      - creating users in subversion, etc.
#      - creating databases
#  - tell mkdirs to use -m 775 and -m 777 where appropriate
#  - external mongrels (uncomment 127.0.0.1 and change in proxy balancer script)
# mongrel has some replacements for restart and spinner:
require 'mongrel_cluster/recipes'
# ferret server start/stop scripts
require 'vendor/plugins/acts_as_ferret/lib/ferret_cap_tasks'
set :use_sudo, false

# =============================================================================
# REQUIRED VARIABLES
# =============================================================================
# You must always specify the application and repository for every recipe. The
# repository must be the URL of the repository you want this recipe to
# correspond to. The deploy_to path must be the path on each machine that will
# form the root of the application path.

set :application, "molten"
#set :repository, "https://bristol.highgroove.com:8443/#{application}/trunk/molten5"
#set :repository, "https://bristol.highgroove.com:8443/molten/tags/1.0"
#set :repository, "https://bristol.highgroove.com:8443/molten/tags/#{ENV['DEPLOY_VERSION']}"
set :repository, "svn+ssh://admin@64.106.247.200/home/svnrepo/tags/molten5/#{ENV['DEPLOY_VERSION']}"
set :user, "admin"
set :group, "admin"
set :password, "2deploy$"

set :svn_username, "molten_deploy"
set :svn_password, "33uGudra"

set :production_db_server, "64.106.247.195"

# =============================================================================
# ROLES
# =============================================================================
# You can define any number of roles, each of which contains any number of
# machines. Roles might include such things as :web, or :app, or :db, defining
# what the purpose of each machine is. You can also specify options that can
# be used to single out a specific subset of boxes in a particular role, like
# :primary => true.

#Staging server, tide.moltenmagma.com
role :web, "10.30.180.225"						#tide
role :app, "10.30.180.225"						#tide
role :db,  "10.30.180.225", :primary => true	#tide

#role :web, "64.106.247.200"
#role :app, "64.106.247.200"
#role :db,  "64.106.247.200", :primary => true

#role :web, "64.106.247.195"
#role :app, "64.106.247.195"
#role :db,  "64.106.247.195", :primary => true

#role :web, "202.168.211.98"
#role :app, "202.168.211.98"
#role :db,  "202.168.211.98", :primary => true

# =============================================================================
# OPTIONAL VARIABLES
# =============================================================================
# set :deploy_to, "/path/to/app" # defaults to "/u/apps/#{application}"
# set :user, "flippy"            # defaults to the currently logged in user
# set :scm, :darcs               # defaults to :subversion
set :svn, "/usr/local/bin/svn"       # defaults to searching the PATH
# set :darcs, "/path/to/darcs"   # defaults to searching the PATH
# set :cvs, "/path/to/cvs"       # defaults to searching the PATH
# set :gateway, "gate.host.com"  # default to no gateway

# we put it here because SELINUX has some context that doesn't like you
# serving docs out anywhere other than /var/www/
set :deploy_to, "/var/www/apps/#{application}"

# your web server's address, i.e. http://sample.com/
set :server_name, "molten.moltenmagma.com"

# set this to the correct web start script, i.e. /etc/init.d/#{web_server}
set :web_server, "apache2"
set :path_to_web_server, "/usr/local/apache2/"

# set this to the correct db adapter
set :database, "mysql"

# saves space by only keeping last 3 when running cleanup
set :keep_releases, 3

# issues svn export instead of checkout
set :checkout, "export"

# mongrel configuration:
#set :mongrel_conf, "#{current_path}/config/mongrel_cluster.yml"
set :mongrel_conf, "#{deploy_to}/#{shared_dir}/config/mongrel_cluster.yml"
set :mongrel_prefix, "/usr/local/bin/"

# number of mongrel servers to start
set :mongrel_servers, 3

# mongrel starting port
set :mongrel_start_port, 8100

# salesforce db load
set :mysql_user, "molten2"
set :mysql_password, "2molten"
set :mysql_db, "#{application}_production"
set :mysql_file, "db/salesforce.sql"

# salesforce database / integration
#set :salesforce_url, "https://www.salesforce.com/services/Soap/u/7.0"
set :salesforce_url, "https://www.salesforce.com/services/Soap/u/9.0"
#set :salesforce_username, "derek.haynes@highgroove.com"
set :salesforce_username, "molten_admin@molten-magma.com"
set :salesforce_password, "u2cansleeprWI2X9JakDlxjcuAofhggFbaf"

# =============================================================================
# SSH OPTIONS
# =============================================================================
# ssh_options[:keys] = %w(/path/to/my/key /path/to/another/key)
# ssh_options[:port] = 25

# =============================================================================
# TASKS
# =============================================================================
# Define tasks that run on all (or only some) of the machines. You can specify
# a role (or set of roles) that each task should be executed on. You can also
# narrow the set of servers to a subset of a role by specifying options, which
# must match the options given for the servers to select (like :primary => true)

# Tasks may take advantage of several different helper methods to interact
# with the remote server(s). These are:
#
# * run(command, options={}, &block): execute the given command on all servers
#   associated with the current task, in parallel. The block, if given, should
#   accept three parameters: the communication channel, a symbol identifying the
#   type of stream (:err or :out), and the data. The block is invoked for all
#   output from the command, allowing you to inspect output and act
#   accordingly.
# * sudo(command, options={}, &block): same as run, but it executes the command
#   via sudo.
# * delete(path, options={}): deletes the given file or directory from all
#   associated servers. If :recursive => true is given in the options, the
#   delete uses "rm -rf" instead of "rm -f".
# * put(buffer, path, options={}): creates or overwrites a file at "path" on
#   all associated servers, populating it with the contents of "buffer". You
#   can specify :mode as an integer value, which will be used to set the mode
#   on the file.
# * render(template, options={}) or render(options={}): renders the given
#   template and returns a string. Alternatively, if the :template key is given,
#   it will be treated as the contents of the template to render. Any other keys
#   are treated as local variables, which are made available to the (ERb)
#   template.

desc "Tasks to execute before initial setup"
task :before_setup do
  sudo "mkdir -p /var/www/apps/"
  sudo "chown -R #{user}:#{group} /var/www/apps/"

  sudo "mkdir -p /etc/mongrel_cluster"
  sudo "chown -R #{user}:#{group} /etc/mongrel_cluster"
  sudo "mkdir -p /etc/rails"
  sudo "chown -R #{user}:#{group} /etc/rails"
end

desc "Tasks to execute after initial setup"
task :after_setup do

  mongrel_configuration = render :template => <<-EOF
---
cwd: #{deploy_to}/current
port: "#{mongrel_start_port}"
environment: production
address: 127.0.0.1
pid_file: #{deploy_to}/current/log/mongrel.pid
log_file: #{deploy_to}/current/log/mongrel.log
servers: #{mongrel_servers}
#prefix: #{mongrel_prefix}
user: #user
group: #group

EOF

  database_configuration = render :template => <<-EOF
# Deployment database.yml
login: &login
  adapter: #{database}
  host: localhost
  username: <%= "#{mysql_user}" %>
  password: <%= "#{mysql_password}" %>

development:
  database: <%= "#{application}_development" %>
  <<: *login

test:
  database: <%= "#{application}_production" %>
  <<: *login

production:
  database: <%= "#{application}_production" %>
  <<: *login

## SalesForce ##

salesforce:
  adapter: activesalesforce
  url: #{salesforce_url}
  username: #{salesforce_username}
  password: #{salesforce_password}

EOF

  # ferret server configuration
  ferret_server_configuration = <<-EOF
production:
  host: localhost
  port: 9010
  pid_file: log/ferret.pid
development:
  host: localhost
  port: 9010
  pid_file: log/ferret.pid
test:
  host: localhost
  port: 9009
  pid_file: log/ferret.pid

EOF

 # script to start/stop ferret server
  ferret_server_control = <<-EOF

#!/bin/bash
#
# This script starts and stops the ferret DRb server
# chkconfig: 2345 89 36
# description: Ferret search engine for ruby apps.
#
# save the current directory
CURDIR=`pwd`
PATH=/usr/local/bin:$PATH

RORPATH="/var/www/apps/molten/current"

case "$1" in
  start)
     cd $RORPATH
     echo "Starting ferret DRb server."
     FERRET_USE_LOCAL_INDEX=1 \
                RAILS_ENV=production \
                script/ferret_start
     ;;
  stop)
     cd $RORPATH
     echo "Stopping ferret DRb server."
     FERRET_USE_LOCAL_INDEX=1 \
                RAILS_ENV=production \
                script/ferret_stop
     ;;
  *)
     echo $"Usage: $0 {start, stop}"
     exit 1
     ;;
esac
cd $CURDIR

EOF

  # web server configuration (apache specific)
  apache2_rails_conf = <<-EOF
  
  Listen 443

  <VirtualHost *:80>
    Include /etc/rails/#{application}.common
    RewriteEngine on
    RewriteOptions inherit

    ErrorLog #{path_to_web_server}logs/#{application}_errors_log
    CustomLog #{path_to_web_server}logs/#{application}_log combined
  </VirtualHost>

  <VirtualHost *:443>
    Include /etc/rails/#{application}.common
    RewriteEngine on
    RewriteOptions inherit

    ErrorLog /usr/local/apache2/logs/#{application}_errors_log
    CustomLog /usr/local/apache2/logs/#{application}_log combined

    # This is required to convince Rails (via mod_proxy_balancer) that we're actually using HTTPS.
    RequestHeader set X_FORWARDED_PROTO 'https'

    SSLEngine On
    SSLCertificateChainFile /usr/local/apache2/conf/X509/intermediate.crt
    SSLCertificateFile /usr/local/apache2/conf/X509/#{application}.moltenmagma.com.crt
    SSLCertificateKeyFile /usr/local/apache2/conf/X509/#{application}.moltenmagma.com.key
  </VirtualHost>

  <Proxy balancer://#{application}_mongrel_cluster>
EOF

  # builds the following as an example with start port 8000 and servers = 3:
  # <Proxy balancer://mongrel_cluster>
  #  BalancerMember http://127.0.0.1:8000
  #  BalancerMember http://127.0.0.1:8001
  #  BalancerMember http://127.0.0.1:8002
  # </Proxy>
  (0..mongrel_servers-1).each { |server|
    apache2_rails_conf += "    BalancerMember http://127.0.0.1:#{mongrel_start_port + server}\n"
  }

  apache2_rails_conf +=<<-EOF
  </Proxy>

  Listen #{mongrel_start_port + 81}
  <VirtualHost *:#{mongrel_start_port + 81}>
    <Location />
      SetHandler balancer-manager
#      Deny from all
        Allow from all
#      Allow from localhost
    </Location>
  </VirtualHost>

# webalizer reports
  Listen #{mongrel_start_port + 82}
  <VirtualHost *:#{mongrel_start_port + 82}>
    DocumentRoot /var/www/apps/molten/shared/usage
    <Directory /var/www/apps/molten/shared/usage>
#      Deny from all
        Allow from all
    </Directory>
  </VirtualHost>
EOF

  apache2_rails_configuration = render :template => apache2_rails_conf

  apache2_rails_common = render :template => <<-EOF
  ServerName #{server_name}
  ServerAlias www.#{server_name}
  DocumentRoot #{deploy_to}/current/public
  UseCanonicalName Off
  
  <Directory "#{deploy_to}/current/public">
    Options FollowSymLinks
    AllowOverride None
    Order allow,deny
    Allow from all
  </Directory>

  RewriteEngine On

  # Uncomment for rewrite debugging
  #RewriteLog logs/#{application}_rewrite_log
  #RewriteLogLevel 9

  # Check for maintenance file and redirect all requests
  RewriteCond %{DOCUMENT_ROOT}/system/maintenance.html -f
  RewriteCond %{SCRIPT_FILENAME} !maintenance.html
  RewriteRule ^.*$ /system/maintenance.html [L]

  # Rewrite index to check for static
  # RewriteRule ^/$ /index.html [QSA]

  # Rewrite to check for Rails cached page
  # RewriteRule ^([^.]+)$ $1.html [QSA]

  # Redirect everything to HTTPS
  RewriteCond %{SERVER_PORT} !^443$
  RewriteRule ^/(.*) https://%{SERVER_NAME}/$1 [L,R]

  # Redirect all non-static requests to cluster
  RewriteCond %{DOCUMENT_ROOT}/%{REQUEST_FILENAME} !-f
  RewriteRule ^/(.*)$ balancer://#{application}_mongrel_cluster%{REQUEST_URI} [P,QSA,L]

  # Deflate
  AddOutputFilterByType DEFLATE text/html text/plain text/xml application/xml application/xhtml+xml text/javascript text/css
  BrowserMatch ^Mozilla/4 gzip-only-text/html
  BrowserMatch ^Mozilla/4.0[678] no-gzip
  BrowserMatch bMSIE !no-gzip !gzip-only-text/html

  # Uncomment for deflate debugging
  #DeflateFilterNote Input input_info
  #DeflateFilterNote Output output_info
  #DeflateFilterNote Ratio ratio_info
  #LogFormat '"%r" %{output_info}n/%{input_info}n (%{ratio_info}n%%)' deflate
  #CustomLog logs/#{application}_deflate_log deflate

EOF

  run "mkdir -p #{deploy_to}/#{shared_dir}/config"

  # BEGIN: The config is under the control of those who configure such things rather than Capistrano. Anyway, the configuration of the Molten server for Ruby is just way too complex for Capistrano.  When you need 600 Mongrels on 2 servers it is time to cease using Capistrano.
  #put mongrel_configuration, "#{deploy_to}/#{shared_dir}/config/mongrel_cluster.yml"
  put database_configuration, "#{deploy_to}/#{shared_dir}/config/database.yml"
  put ferret_server_configuration, "#{deploy_to}/#{shared_dir}/config/ferret_server.yml"
  put ferret_server_control, "#{deploy_to}/#{shared_dir}/config/acts_as_ferret"
  #put apache2_rails_configuration, "#{deploy_to}/#{shared_dir}/system/#{application}.conf"
  #put apache2_rails_common, "#{deploy_to}/#{shared_dir}/system/#{application}.common"
  # END!  The config is under the control of those who configure such things rather than Capistrano.

  run "mkdir -p #{deploy_to}/#{shared_dir}/tmp"
  run "mkdir -p #{deploy_to}/#{shared_dir}/tmp/cache"
  run "mkdir -p #{deploy_to}/#{shared_dir}/tmp/sessions"
  run "mkdir -p #{deploy_to}/#{shared_dir}/tmp/sockets"
  run "mkdir -p #{deploy_to}/#{shared_dir}/locks"

  sudo "ln -nfs #{deploy_to}/#{shared_dir}/config/mongrel_cluster.yml /etc/mongrel_cluster/#{application}.yml"
  sudo "ln -nfs #{deploy_to}/#{shared_dir}/system/#{application}.conf /etc/rails/#{application}.conf"
  sudo "ln -nfs #{deploy_to}/#{shared_dir}/system/#{application}.common /etc/rails/#{application}.common"

  # setup crontab file
  crontab_file = render :template => <<-EOF
# WARNING: this file has been automatically setup by the Capistrano script
#  Please make changes there, not here, as they will be overwritten....
#
# Global variables
SHELL=/bin/bash
PATH=/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/bin
MAILTO=molten-support@molten-magma.com
HOME=/
#
# MOLTEN specific jobs, uncomment when ready
#
#1 * * * * ruby -I /var/www/apps/molten/current/lib /var/www/apps/molten/current/jobs/run_job.rb 'SalesforceSync.update_records(Account)'
#2,17,32,47 * * * * ruby -I /var/www/apps/molten/current/lib /var/www/apps/molten/current/jobs/run_job.rb 'SalesforceSync.update_records(User)'
#3,18,33,48 * * * * ruby -I /var/www/apps/molten/current/lib /var/www/apps/molten/current/jobs/run_job.rb 'SalesforceSync.update_records(SelfServiceUser)'
#4,9,14,19,24,29,34,39,44,49,54,59 * * * * ruby -I /var/www/apps/molten/current/lib /var/www/apps/molten/current/jobs/run_job.rb 'SalesforceSync.update_records(Case)'
#5,12,19,26,33,40,47,54 * * * * ruby -I /var/www/apps/molten/current/lib /var/www/apps/molten/current/jobs/run_job.rb 'SalesforceSync.update_records(Contact)'
#6,16,26,36,46,56 * * * * ruby -I /var/www/apps/molten/current/lib /var/www/apps/molten/current/jobs/run_job.rb 'SalesforceSync.update_records(Solution)'
#7,17,27,37,47,57 * * * * ruby -I /var/www/apps/molten/current/lib /var/www/apps/molten/current/jobs/run_job.rb 'SalesforceSync.update_records(Attachment)'
#3,8,13,18,23,28,33,38,43,48,53,58 * * * * ruby -I /var/www/apps/molten/current/lib /var/www/apps/molten/current/jobs/run_job.rb 'SalesforceSync.update_records(CaseComment)'
#9 * * * * ruby -I /var/www/apps/molten/current/lib /var/www/apps/molten/current/jobs/run_job.rb 'SalesforceSync.update_records(MoltenPost)'
#53 * * * * ruby -I /var/www/apps/molten/current/lib /var/www/apps/molten/current/jobs/run_job.rb 'SalesforceSync.update_records(CategoryData)'
#51 * * * * ruby -I /var/www/apps/molten/current/lib /var/www/apps/molten/current/jobs/run_job.rb 'SalesforceSync.update_records(CategoryNode)'
#10 * * * * ruby -I /var/www/apps/molten/current/lib /var/www/apps/molten/current/jobs/run_job.rb 'SalesforceSync.update_records(Group)'
#11 * * * * ruby -I /var/www/apps/molten/current/lib /var/www/apps/molten/current/jobs/run_job.rb 'SalesforceSync.update_records(Case_Watcher)'
#12 * * * * ruby -I /var/www/apps/molten/current/lib /var/www/apps/molten/current/jobs/run_job.rb 'SalesforceSync.update_records(Case_Watcher_List)'
#13 * * * * ruby -I /var/www/apps/molten/current/lib /var/www/apps/molten/current/jobs/run_job.rb 'SalesforceSync.update_records(Component)'
#14 * * * * ruby -I /var/www/apps/molten/current/lib /var/www/apps/molten/current/jobs/run_job.rb 'SalesforceSync.update_records(Product_Team)'
##0 4 * * * ruby -I /var/www/apps/molten/current/lib /var/www/apps/molten/current/jobs/run_job.rb 'Sfcontact.send_confirmations'
#
#Mongrel log rotation, mongrel restart, monit restart, twice/day
3 3 * * * /var/www/apps/molten/shared/system/logrotate.sh
#Clear user sessions daily
24 19 * * * /var/www/apps/molten/shared/system/clear_sessions.sh

EOF

  put crontab_file, "#{deploy_to}/#{shared_dir}/system/crontab"
#  sudo "cp #{deploy_to}/#{shared_dir}/system/crontab /etc/crontab"
  run "crontab -r"
  run "crontab #{shared_path}/system/crontab"
#  sudo "chown root:root /etc/crontab"
  
  # setup logrotate file
  logrotate_file = render :template => <<-EOF
#! /bin/bash

day=`date +%Y%m%d`
cd /var/www/apps/molten/shared/log

for log in `ls *log`; do
    mv $log $log.$day
done

find . -name "*log.*" -mtime +7 -exec rm -f '{}' \;

/etc/init.d/molten restart
#sleep 5
#/etc/init.d/monit restart
exit

EOF

  put logrotate_file, "#{deploy_to}/#{shared_dir}/system/logrotate.sh"
  sudo "chown #{user}:#{group} #{deploy_to}/#{shared_dir}/system/logrotate.sh"
  sudo "chmod 700 #{deploy_to}/#{shared_dir}/system/logrotate.sh"

end

desc "Tasks to execute after code update"
task :after_update_code, :roles => [:app, :db] do
  # relink shared deployment database configuration
  run "ln -nfs #{deploy_to}/#{shared_dir}/config/database.yml #{release_path}/config/database.yml"
  
  # relink shared ferret server configuration
  run "ln -nfs #{deploy_to}/#{shared_dir}/config/ferret_server.yml #{release_path}/config/ferret_server.yml"

  # relink shared tmp dir (for session and cache data
  sudo "rm -rf #{release_path}/tmp"  # technically shouldn't be in svn
  run "ln -nfs #{deploy_to}/#{shared_dir}/tmp #{release_path}/tmp"


  # rebuild ferret index
  # run "ln -nfs #{deploy_to}/#{shared_dir}/ferret_index #{release_path}/db/ferret_index"
  # run "cd #{release_path} && RAILS_ENV=production rake search:build_index"
  
  # relink ferret index
  run "mkdir -p #{deploy_to}/#{shared_dir}/index" # if it doesn't already exist
  sudo "rm -rf #{release_path}/index"  
  run "ln -nfs #{deploy_to}/#{shared_dir}/index #{release_path}/index"
end

desc "Rebuilds the Ferret Index"
task :rebuild_index, :roles => [:app, :db] do
  run "cd #{deploy_to}/current && RAILS_ENV=production rake search:build_index"
end

desc "Start the Ferret Server"
task :ferret_start do
  ferret.start
end

desc "Restart the Ferret Server"
task :ferret_restart do
  ferret.restart
end

desc "Stop the Ferret Server"
task :ferret_stop do
  ferret.stop
end

desc "Tasks to execute after a deploy"
task :after_deploy, :roles => [:app, :db] do
 # some examples could be:
 # restart rails_cron, backgrounDRb
 # relink shared user/file dirs
 # relink shared ferret_index
 # restart_rails_cron
# restart ferret server
  ferret_restart
# make script/* executable
  sudo "chmod +x #{release_path}/script/*"
end

# =============================================================================
# OVERRIDE TASKS
# =============================================================================
desc "Restart the web server"
task :restart_web, :roles => [:web] do
  sudo "/etc/init.d/#{web_server} restart"
end

# =============================================================================
# APPLICATION SPECIFIC TASKS
# =============================================================================
desc "Load in the SalesForce SQL tables."
task :database_load, :roles => [:app, :db] do
  run("mysql --user=#{mysql_user} --password=#{mysql_password} #{mysql_db} < #{current_path}/#{mysql_file}")
end

#### Tasks for working with the production DB #####

desc 'Grab a dump of the production database on the server and places it in db/production.sql.'
task :get_production_db, :roles => [:db] do
  `rm -f db/molten_production.sql.gz`
  # `scp #{user}@#{production_db_server}:/home/admin/molten_production.sql.gz db/molten_production.sql.gz`
  `cd db/ && tar -xvzf molten_production.sql.gz && cd ..`
end

desc 'Imports the database dump of file db/production.sql into development.'
task :import_db, :roles => [:db] do
  `mysql -u root molten_development < db/molten_production.sql`
end

desc 'Downloads and imports the production db into the develeopment environment.'
task :get_import_db, :roles => [:db] do
  dump_production_db
  get_production_db
  import_db
end

#### End tasks for production DB ####


desc "Rebuild Ferret search index"
# rake remote:exec ACTION=ferret_index
task :ferret_index, :roles => [:app, :db] do
  run("cd #{current_path} && RAILS_ENV=production rake search:build_index")
  run("chmod -R ugo+w #{current_path}/index")
  run("chmod -R ugo+r #{current_path}/index")
end

desc "Stop Rails Cron"
#rake remote:exec ACTION=stop_rails_cron
task :stop_rails_cron, :roles => :web do
#  run "cd #{current_path} && rake cron_stop"
#  run "sleep 3"
	run "crontab -r"
end

desc "Start Rails Cron"
#rake remote:exec ACTION=start_rails_cron
task :start_rails_cron, :roles => :web do
#  run "cd #{current_path} && rake RAILS_ENV=production cron_start"
	run "crontab #{shared_path}/system/crontab"
end

desc "Restart Rails Cron"
#rake remote:exec ACTION=restart_rails_cron
task :restart_rails_cron, :roles => :web do
  stop_rails_cron
  start_rails_cron
end

desc <<-DESC
Disable the web server by writing a "maintenance.html" file to the web
servers. The servers must be configured to detect the presence of this file,
and if it is present, always display it instead of performing the request.
DESC
task :disable_web, :roles => :web do
  on_rollback { delete "#{shared_path}/system/maintenance.html" }

  maintenance = render("#{shared_path}/system/maintenance.rhtml", :deadline => ENV['UNTIL'],
    :reason => 'scheduled maintenance')
  put maintenance, "#{shared_path}/system/maintenance.html", :mode => 0644
  run "crontab -r"
end

desc %(Re-enable the web server by deleting any "maintenance.html" file.)
task :enable_web, :roles => :web do
  delete "#{shared_path}/system/maintenance.html"
  run "crontab #{shared_path}/system/crontab"
end