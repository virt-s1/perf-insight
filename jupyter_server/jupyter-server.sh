#!/bin/bash

#==============================================================================
#         FILE: jupyter-server.sh
#
#        USAGE: ./jupyter-server.sh
#
#  DESCRIPTION: Foreground the JupyterLab service.
#
#      OPTIONS: ---
# REQUIREMENTS: ---
#         BUGS: ---
#        NOTES: ---
#       AUTHOR: Charles Shih (schrht@gmail.com)
# ORGANIZATION: ---
#      CREATED: Fri Sep 24 11:37:17 AM CST 2021
#     REVISION: ---
#==============================================================================

trap cleanup SIGINT SIGTERM ERR EXIT

cleanup() {
    trap - SIGINT SIGTERM ERR EXIT
    exit 0
}

# Start JupyterLab
mkdir -p /app/workspace
jupyter-lab -y --allow-root --no-browser --ip 0.0.0.0 --port 8888 \
    --notebook-dir=/app/workspace --collaborative
