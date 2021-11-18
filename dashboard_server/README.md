# Dashboard Server

The dashboard of the performance test report system, allowing quality engineers to gain insight into the valuable data in the test results.

## Container usage

```bash
# Build container image
podman build ./dashboard_server/ -t perf-insight-dashboard-server

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
podman run --rm -itd --name perf-insight-dashboard-server \
    --volume $HOST_PERF_INSIGHT_REPO:/opt/perf-insight:ro \
    --volume $HOST_PERF_INSIGHT_DATA:/data:rw \
    --publish 8080:8080 \
    perf-insight-dashboard-server

# DEBUG: Run as debug container
podman run --rm -it --name perf-insight-dashboard-server \
    --volume $HOST_PERF_INSIGHT_REPO:/opt/perf-insight:ro \
    --volume $HOST_PERF_INSIGHT_DATA:/data:rw \
    --publish 8080:8080 \
    perf-insight-dashboard-server /bin/bash

# DEBUG: Start Flask server (inside container)
cd /opt/perf-insight/dashboard_server/
FLASK_APP=app.py
FLASK_ENV=development
[ ! -e /data/app.db ] && flask fab create-admin # init (first time only)
flask run --host 0.0.0.0 --port 8080

```

## More information

### Clean up user data from database

1. Open database by `sqlite3 ./app.db`
2. List all tables by `>.table`
3. Drop all tables except the ones start with `ab_` by `>drop table <table_name>;`
4. Quit by `>.quit`


## References

> Flask-AppBuilder
> https://flask-appbuilder.readthedocs.io/en/latest/index.html
