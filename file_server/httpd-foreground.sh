#!/bin/bash

#==============================================================================
#         FILE: httpd-foreground.sh
#
#        USAGE: ./httpd-foreground.sh
#
#  DESCRIPTION: Foreground the httpd service.
#
#      OPTIONS: ---
# REQUIREMENTS: ---
#         BUGS: ---
#        NOTES: ---
#       AUTHOR: Charles Shih (schrht@gmail.com)
# ORGANIZATION: ---
#      CREATED: Thu Sep 23 03:29:07 PM CST 2021
#     REVISION: ---
#==============================================================================

trap cleanup SIGINT SIGTERM ERR EXIT

cleanup() {
    trap - SIGINT SIGTERM ERR EXIT
    httpd -k stop
    killall tail
    exit 0
}

# Start Apache server
httpd -k start

# Print logs
touch /var/log/httpd/error_log /var/log/httpd/access_log
tail -f /var/log/httpd/error_log &
tail -f /var/log/httpd/access_log &

# Preserve the process inside contianer
sleep infinity
