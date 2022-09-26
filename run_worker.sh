#!/bin/bash -x

echo "Starting celery worker"
celery -A tackapp worker --loglevel=info --logfile=celery.log