# File Server

## Container usage

```bash
# Build container image
podman build ./file_server/ -t perf-insight-file-server

# Prepare environment
HOST_PERF_INSIGHT_REPO=$HOME/mirror/codespace/perf-insight
HOST_PERF_INSIGHT_ROOT=/nfs/perf-insight
HOST_PERF_INSIGHT_DATA=
HOST_PERF_INSIGHT_STAG=
HOST_PERF_INSIGHT_TEMP=
HOST_PERF_INSIGHT_SBIN=

# Correct SELinux context for container
chcon -R -u system_u -t svirt_sandbox_file_t $HOST_PERF_INSIGHT_REPO
chcon -R -u system_u -t svirt_sandbox_file_t $HOST_PERF_INSIGHT_ROOT

# Run as deamon
podman run --rm -itd --name perf-insight-file-server \
    --volume $HOST_PERF_INSIGHT_REPO:/opt/perf-insight:ro \
    --volume $HOST_PERF_INSIGHT_ROOT:/mnt/perf-insight:ro \
    --publish 8081:80 \
    perf-insight-file-server

# DEBUG: Run as debug container
podman run --rm -it --name perf-insight-file-server \
    --volume $HOST_PERF_INSIGHT_REPO:/opt/perf-insight:ro \
    --volume $HOST_PERF_INSIGHT_ROOT:/mnt/perf-insight:ro \
    --publish 8081:80 \
    perf-insight-file-server /bin/bash

# DEBUG: Start apache server (inside container)
/app/httpd-foreground.sh

```
