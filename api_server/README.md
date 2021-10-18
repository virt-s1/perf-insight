# API Server

## Container usage

```bash
# Build container image
podman build ./api_server/ -t perf-insight-api-server

# Prepare environment
HOST_PERF_INSIGHT_REPO=$HOME/mirror/codespace/perf-insight
HOST_PERF_INSIGHT_ROOT=/nfs/perf-insight
HOST_PERF_INSIGHT_DATA=/nfs/perf-insight-data
HOST_PERF_INSIGHT_STAG=
HOST_PERF_INSIGHT_TEMP=
HOST_PERF_INSIGHT_SBIN=

# Correct SELinux context for container
chcon -R -u system_u -t svirt_sandbox_file_t $HOST_PERF_INSIGHT_REPO
chcon -R -u system_u -t svirt_sandbox_file_t $HOST_PERF_INSIGHT_ROOT
chcon -R -u system_u -t svirt_sandbox_file_t $HOST_PERF_INSIGHT_DATA

# Run as deamon
podman run --rm -itd --name perf-insight-api-server \
    --volume $HOST_PERF_INSIGHT_REPO:/opt/perf-insight:rw \
    --volume $HOST_PERF_INSIGHT_ROOT:/mnt/perf-insight:rw \
    --volume $HOST_PERF_INSIGHT_DATA:/data:rw \
    --publish 5000:5000 \
    perf-insight-api-server

# DEBUG: Run as debug container
podman run --rm -it --name perf-insight-api-server \
    --volume $HOST_PERF_INSIGHT_REPO:/opt/perf-insight:rw \
    --volume $HOST_PERF_INSIGHT_ROOT:/mnt/perf-insight:rw \
    --volume $HOST_PERF_INSIGHT_DATA:/data:rw \
    --publish 5000:5000 \
    perf-insight-api-server /bin/bash

# DEBUG: Start Flask server (inside container)
cd /opt/perf-insight/api_server
FLASK_APP=app.py
FLASK_ENV=development
flask run --host 0.0.0.0 --port 5000

```
