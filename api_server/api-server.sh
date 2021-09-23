#!/bin/bash

#==============================================================================
#         FILE: api-server.sh
#
#        USAGE: ./api-server.sh
#
#  DESCRIPTION: Start the RESTful API server.
#
#      OPTIONS: ---
# REQUIREMENTS: ---
#         BUGS: ---
#        NOTES: ---
#       AUTHOR: Charles Shih (schrht@gmail.com)
# ORGANIZATION: ---
#      CREATED: Thu Sep 23 05:16:12 PM CST 2021
#     REVISION: ---
#==============================================================================

trap cleanup SIGINT SIGTERM ERR EXIT

cleanup() {
    trap - SIGINT SIGTERM ERR EXIT
    httpd -k stop
    killall tail
    exit 0
}

# Start Flask server
cd /opt/perf-insight/api_server
flask run --host 0.0.0.0 --port 5000
