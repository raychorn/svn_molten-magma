FERRET_USE_LOCAL_INDEX=1
RAILS_ENV=production 
chmod 0755 /var/www/apps/molten/current/script/*
cd /var/www/apps/molten/current
ruby script/ferret_stop
