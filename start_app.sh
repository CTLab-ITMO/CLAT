#!/bin/sh
python image_assessment_service/cli.py --config /app/config.yaml

## Capture the exit code of the Python script
#EXIT_CODE=$?
## If the script fails, sleep for a while to keep the container running
#if [ $EXIT_CODE -ne 0 ]; then
#  echo "Python script failed with exit code $EXIT_CODE. Sleeping to keep the container running..."
#  sleep 3600  # Sleep for 1 hour (3600 seconds)
#fi