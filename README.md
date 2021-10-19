# The perf-insight Project

## Get started

This guideline is based on Fedora 34.

Clone repo:

`git clone https://github.com/virt-s1/perf-insight.git /opt/perf-insight`

Install packages:

`pip3 install podman-compose`, or
`pip3 install https://github.com/containers/podman-compose/archive/devel.tar.gz`

Put the following variables into `/opt/perf-insight/compose/.env`:

```
HOST_PERF_INSIGHT_REPO=/opt/perf-insight
HOST_PERF_INSIGHT_ROOT=/nfs/perf-insight
HOST_PERF_INSIGHT_DATA=/root/pilocaldata
```

```
source /opt/perf-insight/compose/.env

mkdir -p $HOST_PERF_INSIGHT_ROOT/testruns
mkdir -p $HOST_PERF_INSIGHT_ROOT/reports
mkdir -p $HOST_PERF_INSIGHT_ROOT/.staging
mkdir -p $HOST_PERF_INSIGHT_DATA

cp /opt/perf-insight/config.yaml $HOST_PERF_INSIGHT_DATA
cp /opt/perf-insight/dashboard_server/app.db.origin $HOST_PERF_INSIGHT_DATA/app.db

chcon -R -u system_u -t svirt_sandbox_file_t $HOST_PERF_INSIGHT_REPO
chcon -R -u system_u -t svirt_sandbox_file_t $HOST_PERF_INSIGHT_ROOT
chcon -R -u system_u -t svirt_sandbox_file_t $HOST_PERF_INSIGHT_DATA
```

Update the config.yaml as following:
```bash
$ cat $HOST_PERF_INSIGHT_DATA/config.yaml
global:
  perf_insight_root: /mnt/perf-insight
  perf_insight_repo: /opt/perf-insight
  perf_insight_temp: /opt/perf-insight/templates
dashboard:
  dashboard_db_file: /data/app.db
  file_server: 10.73.199.83:8081
jupyter:
  jupyter_workspace: /app/workspace
  jupyter_lab_host: 10.73.199.83
  jupyter_lab_ports: 8890-8899
api:
  file_server: 10.73.199.83:8081
  jupyter_api_server: 10.73.199.83:8880
```

> Please note these variables are used by the services in container.
> `10.73.199.83` is the host's IP in my case, a hostname should be used in production.

Start the stack:

```bash
cd /opt/perf-insight/compose/
podman-compose up -d
```

Check the stack:

```bash
# List services
$ podman-compose ps
CONTAINER ID  IMAGE                                            COMMAND               CREATED         STATUS             PORTS                                                                                                   NAMES
078b640ee20b  localhost/compose_perf_insight_api:latest        /app/api-server.s...  15 seconds ago  Up 13 seconds ago  0.0.0.0:8081->80/tcp, 0.0.0.0:5000->5000/tcp, 0.0.0.0:8080->8080/tcp, 0.0.0.0:8880-8899->8880-8899/tcp  compose_perf_insight_api_1
2eeef0ef78a5  localhost/compose_perf_insight_dashboard:latest  /app/dashboard-se...  11 seconds ago  Up 11 seconds ago  0.0.0.0:8081->80/tcp, 0.0.0.0:5000->5000/tcp, 0.0.0.0:8080->8080/tcp, 0.0.0.0:8880-8899->8880-8899/tcp  compose_perf_insight_dashboard_1
13938710c411  localhost/compose_perf_insight_jupyter:latest    /app/jupyter-serv...  9 seconds ago   Up 9 seconds ago   0.0.0.0:8081->80/tcp, 0.0.0.0:5000->5000/tcp, 0.0.0.0:8080->8080/tcp, 0.0.0.0:8880-8899->8880-8899/tcp  compose_perf_insight_jupyter_1
41590de4f474  localhost/compose_perf_insight_file:latest       /app/httpd-foregr...  7 seconds ago   Up 7 seconds ago   0.0.0.0:8081->80/tcp, 0.0.0.0:5000->5000/tcp, 0.0.0.0:8080->8080/tcp, 0.0.0.0:8880-8899->8880-8899/tcp  compose_perf_insight_file_1

```

Check the services:

```bash
curl http://localhost:5000/testruns
# Below outputs show perf_insight_api service works
# {"testruns":[]}

curl http://localhost:5000/studies
# Below outputs show perf_insight_jupyter service works
# {"studies":[]}

curl http://localhost:8080/ 2>/dev/null | grep "<title>"
# Below outputs show perf_insight_dashboard service works
# <title>Perf Insight</title>

curl http://localhost:8081/ 2>/dev/null
# Below outputs show perf_insight_file service works
# <html><head><meta http-equiv="refresh" content="0; url=/perf-insight/"/></head></html>
```

```
# Stop services
podman-compose down -t 1
```

