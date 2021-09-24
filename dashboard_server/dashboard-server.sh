#!/bin/bash

#==============================================================================
#         FILE: dashboard-server.sh
#
#        USAGE: ./dashboard-server.sh
#
#  DESCRIPTION: Foreground the dashboard service.
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

# Init the database (first time only)
if [ ! -e /data/app.db ]; then
    echo "File /data/app.db doesn't exist, init database..." &>2
    flask fab create-admin
fi

# Start Flask server
cd /opt/perf-insight/dashboard_server/
flask run --host 0.0.0.0 --port 5000
