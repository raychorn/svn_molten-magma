echo "Stopping Molten Mongrels..."
monit stop all

echo "Sleeping 60 secs..."
sleep 180

echo "Starting Molten Mongrels..."
monit start all

