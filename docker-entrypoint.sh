#!/bin/bash -x

while ! python3 manage.py migrate  2>&1; do
   echo "Migration is in progress status"
   sleep 3
done

echo "Django docker is fully configured successfully."

#python3 manage.py migrate --noinput || exit 1
CONTAINER_ALREADY_STARTED="CONTAINER_ALREADY_STARTED_PLACEHOLDER"
if [ ! -e $CONTAINER_ALREADY_STARTED ]; then
    touch $CONTAINER_ALREADY_STARTED
    echo "-- First container startup --"
#    python3 manage.py loaddata fixture1.json
else
    echo "-- Not first container startup --"
fi

exec "$@"