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
#     REVISION: Wed Sep 29 08:59:54 PM CST 2021
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
mkdir -p /app/workspace /app/log

# Prepare test environment
ln -s /mnt/perf-insight/reports/* /app/workspace/

users="cheshi yuxisun xiliang ldu"
for user in $users; do
    mkdir -p /mnt/perf-insight/reports/$user
    [ ! -e /app/workspace/$user ] && ln -s /mnt/perf-insight/reports/$user /app/workspace/

    jupyter-lab -y --allow-root --no-browser --ip 0.0.0.0 --port 8888 \
        --ServerApp.password_required=True \
        --ServerApp.password='argon2:$argon2id$v=19$m=10240,t=10,p=8$CitYS3BPMSBPtBVrfKRxLg$Oao8niNXff1Ai5SxJHeQvA' \
        --notebook-dir=/app/workspace/$user --collaborative &>>/app/log/jupyter_lab_$user.log &
done

# Start Flask as API server
cd /opt/perf-insight/jupyter_server/
flask run --host 0.0.0.0 --port 8880

# Start JupyterLab
# mkdir -p /app/workspace
# jupyter-lab -y --allow-root --no-browser --ip 0.0.0.0 --port 8888 \
#     --notebook-dir=/app/workspace --collaborative
