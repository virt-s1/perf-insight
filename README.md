# The perf-insight Project

## Get started

This guideline is based on Fedora 34.

### Clone repo

`git clone https://github.com/virt-s1/perf-insight.git /opt/perf-insight`

### Install packages

`pip3 install podman-compose`, or  
`pip3 install https://github.com/containers/podman-compose/archive/devel.tar.gz`

### Config environment

Put the following variables into `/opt/perf-insight/compose/.env`:

```
HOST_PERF_INSIGHT_REPO=/opt/perf-insight
HOST_PERF_INSIGHT_ROOT=/nfs/perf-insight
HOST_PERF_INSIGHT_DATA=/root/pilocaldata
```

Prepare environment:

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

Update the `$HOST_PERF_INSIGHT_DATA/config.yaml` as following:

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

> Notes:  
> Only IP addresses need to be changed here.  
> These variables are used by the services in container, so `localhost` doesn't work.  
> `10.73.199.83` is the host's IP in my case, a hostname should be used in production.

### Start the services

```bash
cd /opt/perf-insight/compose/
podman-compose up -d
```

### Check the services

List services by `podman-compose ps` command, and it should like this:

```bash
CONTAINER ID  IMAGE                                            COMMAND               CREATED         STATUS             PORTS                                                                                                   NAMES
078b640ee20b  localhost/compose_perf_insight_api:latest        /app/api-server.s...  15 seconds ago  Up 13 seconds ago  0.0.0.0:8081->80/tcp, 0.0.0.0:5000->5000/tcp, 0.0.0.0:8080->8080/tcp, 0.0.0.0:8880-8899->8880-8899/tcp  compose_perf_insight_api_1
2eeef0ef78a5  localhost/compose_perf_insight_dashboard:latest  /app/dashboard-se...  11 seconds ago  Up 11 seconds ago  0.0.0.0:8081->80/tcp, 0.0.0.0:5000->5000/tcp, 0.0.0.0:8080->8080/tcp, 0.0.0.0:8880-8899->8880-8899/tcp  compose_perf_insight_dashboard_1
13938710c411  localhost/compose_perf_insight_jupyter:latest    /app/jupyter-serv...  9 seconds ago   Up 9 seconds ago   0.0.0.0:8081->80/tcp, 0.0.0.0:5000->5000/tcp, 0.0.0.0:8080->8080/tcp, 0.0.0.0:8880-8899->8880-8899/tcp  compose_perf_insight_jupyter_1
41590de4f474  localhost/compose_perf_insight_file:latest       /app/httpd-foregr...  7 seconds ago   Up 7 seconds ago   0.0.0.0:8081->80/tcp, 0.0.0.0:5000->5000/tcp, 0.0.0.0:8080->8080/tcp, 0.0.0.0:8880-8899->8880-8899/tcp  compose_perf_insight_file_1
```

You can use `picli` tool to further check the service status. Or do these checks by:

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

### Stop the services

You can stop the services by `podman-compose down -t 1` command.

## Use CLI tool

Install the necessary Python modules by `pip3 install tabulate click` command.

Link `picli` to `/usr/bin` by `ln -s /opt/perf-insight/cli_tool/picli /usr/bin/picli` command.

Run the following commands to check the services:

```bash
picli testrun-list >/dev/null && echo "The API server is working properly."
picli lab-list >/dev/null && echo "Both the API server and Jupyter server are working properly."
```
