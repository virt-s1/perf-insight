# perf-insight/dashboard

The performance test report system, allowing quality engineers to gain insight into the valuable data in the test results.

## Clone the repo

    git clone https://github.com/virt-s1/perf-insight.git

## Swith to repo directory and install required pkgs

    cd perf-insight/dashboard
    pip install -r requirements.txt

## Create an Admin user (only required at first run)

    flask fab create-admin

## Start the app

    flask run -h 0.0.0.0 -p 5000

## Access it via below link

    http://$ip:5000

## Access via rest api

```bash
# curl -XPOST http://$ip:$port/api/v1/security/login -d '{"username": "admin", "password": "$password", "provider": "db"}' -H "Content-Type: application/json"
# export TOKEN=$token
# curl http://$ip:$port/api/v1/storage/ -H "Content-Type: application/json" -H "A/0 /0uthorization: Bearer $TOKEN"
# curl -XPOST http://$ip:$port/api/v1/storage/ -d \
 '{"backend":"test2","branch":"RHEL-9.1","bs":900,"bw":5,"comments":"Test","compose":"RHEL-9.1.0-20201112.1","cpu":"AMD Opteron(tm) Processor 4284","debug":"testlog","driver":"nvme","format":"xfs","instance_type":"x1.16xlarge","iodepth":18,"iops":50000,"kernel":"5.9.0-38.el9.x86_64","latency":4,"memory":"1900","numjobs":15,"platform":"xen","round":5,"rw":1000,"test_date":"2020-11-17","testrun":"aws_testrun_2","tool_version":"fio-3.23-5.el9"}' \
 -H "Content-Type: application/json" \
 -H "Authorization: Bearer $TOKEN"
```

## References

### - *[Flask-AppBuilder](https://flask-appbuilder.readthedocs.io/en/latest/index.html)*


# Dashboard Server

## Container usage

```bash
# build container image
podman build ./dashboard/ -t dashboard-server

# correct SELinux context for container
chcon -R -u system_u -t svirt_sandbox_file_t $HOME/mirror/codespace/perf-insight
chcon -R -u system_u -t svirt_sandbox_file_t /nfs/perf-insight
chcon -R -u system_u -t svirt_sandbox_file_t $HOME/.perf-insight.yaml
chcon -R -u system_u -t svirt_sandbox_file_t /nfs/app.db

# run as debug container
podman run --rm -it --name dashboard-server \
    --volume $HOME/mirror/codespace/perf-insight:/opt/perf-insight:rw \
    --volume $HOME/.perf-insight.yaml:/root/.perf-insight.yaml:rw \
    --volume /nfs/app.db:/data/app.db:rw \
    --publish 5000:5000 \
    dashboard-server /bin/bash

# start API server (inside container)
cd /opt/perf-insight/dashboard/
flask run --host 0.0.0.0 --port 5000

```
