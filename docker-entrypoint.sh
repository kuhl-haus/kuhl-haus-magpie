#!/bin/sh
# docker-entrypoint.sh

set -exu

# Run bootstrap command
echo "Bootstrapping application..."
python -m kuhl_haus.magpie.manage bootstrap

# Execute the command passed to the script
exec "$@"