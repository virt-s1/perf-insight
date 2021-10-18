# Jupyter Server

## Container usage

```bash
# Build container image
podman build ./jupyter_server/ -t perf-insight-jupyter-server

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
podman run --rm -itd --name perf-insight-jupyter-server \
    --volume $HOST_PERF_INSIGHT_REPO:/opt/perf-insight:ro \
    --volume $HOST_PERF_INSIGHT_ROOT:/mnt/perf-insight:rw \
    --volume $HOST_PERF_INSIGHT_DATA:/data:ro \
    --publish 8880-8899:8880-8899 \
    perf-insight-jupyter-server /app/jupyter-server.sh

# DEBUG: Run as debug container
podman run --rm -it --name perf-insight-jupyter-server \
    --volume $HOST_PERF_INSIGHT_REPO:/opt/perf-insight:ro \
    --volume $HOST_PERF_INSIGHT_ROOT:/mnt/perf-insight:rw \
    --volume $HOST_PERF_INSIGHT_DATA:/data:ro \
    --publish 8880-8899:8880-8899 \
    perf-insight-jupyter-server /bin/bash

# DEBUG: Start apache server (inside container)
/app/jupyter-server.sh

# DEBUG: Start Jupyter server (inside container)
mkdir -p /app/workspace
jupyter-lab -y --allow-root --no-browser --ip 0.0.0.0 --port 8888 \
    --ServerApp.password_required=True \
    --ServerApp.password='argon2:$argon2id$v=19$m=10240,t=10,p=8$CitYS3BPMSBPtBVrfKRxLg$Oao8niNXff1Ai5SxJHeQvA' \
    --notebook-dir=/app/workspace --collaborative

```
