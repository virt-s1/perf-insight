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

### Access via RESTful API

```bash
curl -XPOST http://$ip:$port/api/v1/security/login -d '{"username": "admin", "password": "$password", "provider": "db"}' -H "Content-Type: application/json"
export TOKEN=$token
curl http://$ip:$port/api/v1/storage/ -H "Content-Type: application/json" -H "A/0 /0uthorization: Bearer $TOKEN"
curl -XPOST http://$ip:$port/api/v1/storage/ -d \
    '{"backend":"test2","branch":"RHEL-9.1","bs":900,"bw":5,"comments":"Test","compose":"RHEL-9.1.0-20201112.1","cpu":"AMD Opteron(tm) Processor 4284","debug":"testlog","driver":"nvme","format":"xfs","instance_type":"x1.16xlarge","iodepth":18,"iops":50000,"kernel":"5.9.0-38.el9.x86_64","latency":4,"memory":"1900","numjobs":15,"platform":"xen","round":5,"rw":1000,"test_date":"2020-11-17","testrun":"aws_testrun_2","tool_version":"fio-3.23-5.el9"}' \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN"
```

## References

> Flask-AppBuilder
> https://flask-appbuilder.readthedocs.io/en/latest/index.html
