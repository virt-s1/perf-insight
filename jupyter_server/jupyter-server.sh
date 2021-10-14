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
#     REVISION: Thu Oct 14 12:16:52 PM CST 2021
#==============================================================================

trap cleanup SIGINT SIGTERM ERR EXIT

cleanup() {
    trap - SIGINT SIGTERM ERR EXIT
    exit 0
}

# Setup environment
if [ ! -e /root/.perf-insight.yaml ] && [ -f /data/config.yaml ]; then
    ln -s /data/config.yaml /root/.perf-insight.yaml
fi
mkdir -p /app/workspace

# Start Flask as API server
cd /opt/perf-insight/jupyter_server/
flask run --host 0.0.0.0 --port 8880
