# API Server

## Container usage

```bash
# build container image
podman build ./api_server/ -t perf-insight-api-server

# correct SELinux context for container
chcon -R -u system_u -t svirt_sandbox_file_t $HOME/mirror/codespace/perf-insight
chcon -R -u system_u -t svirt_sandbox_file_t /nfs/perf-insight
chcon -R -u system_u -t svirt_sandbox_file_t $HOME/.perf-insight.yaml

# run as debug container
podman run --rm -it --name perf-insight-api-server \
    --volume $HOME/mirror/codespace/perf-insight:/opt/perf-insight:rw \
    --volume /nfs/perf-insight:/nfs/perf-insight:rw \
    --volume $HOME/.perf-insight.yaml:/root/.perf-insight.yaml:rw \
    --publish 5001:5000 \
    perf-insight-api-server /bin/bash

# start API server (inside container)
cd /opt/perf-insight/api_server
FLASK_APP=app.py
FLASK_ENV=development
flask run --host 0.0.0.0 --port 5000
```
