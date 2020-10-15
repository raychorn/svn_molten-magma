echo "Stopping Ferret..."
./stop_ferret.sh

echo "Stopping Molten Mongrels..."
monit stop all

echo "Sleeping 60 secs..."
sleep 60

echo "Starting Ferret..."
./start_ferret.sh

echo "Starting Molten Mongrels..."
monit start all

