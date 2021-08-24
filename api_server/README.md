# API Server

## Usage

```bash
cd ./api_server/
FLASK_APP=app.py
FLASK_ENV=development

flask run
```

## Container

```bash
podman build ./api_server/ -t perf-insight-api-server

chcon -Rt svirt_sandbox_file_t /home/cheshi/mirror/codespace/perf-insight
chcon -Rt svirt_sandbox_file_t /nfs/perf-insight
chcon -Rt svirt_sandbox_file_t ~/.perf-insight.yaml

podman run --volume /home/cheshi/mirror/codespace/perf-insight:/opt/perf-insight:rw \
    --volume /nfs/perf-insight:/nfs/perf-insight:rw \
    --volume ~/.perf-insight.yaml:/root/.perf-insight.yaml:rw \
    --publish 5001:5000 \
    --rm -it perf-insight-api-server /bin/bash

cd /opt/perf-insight/api_server
FLASK_APP=app.py
FLASK_ENV=development
flask run --host 0.0.0.0 --port 5000
```
