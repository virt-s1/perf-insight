# Performance Test Report Portal Jupyter page

## Build image
```
cd perf-insight
podman build -t jupyter_reporting . -f ./jupyter/container/Dockerfile 
```

## Prepare user config

```
$ cat $HOME/.perf-insight.yaml
jupyter:
  flask_server: perf-insight.lab.eng.pek2.redhat.com:5000
  apache_server: perf-insight.lab.eng.pek2.redhat.com
```

## Prepare data

Under `/path-to/workspace/`, prepare the following files for the Jupter reporting:

```
workspace/
├── base.datastore.json
├── base.metadata.json
├── benchmark_config.yaml
├── test.datastore.json
└── test.metadata.json
```

## Change selinux context

Change folder selinux context, or container cannot read the files:

```
chcon -Rt svirt_sandbox_file_t /workspace
```

## Run the container

The following container will generate the `report.html` into `/path-to/workspace/`:

```
podman run --rm -v /path-to/workspace:/workspace:rw \
    -v $HOME/.perf-insight.yaml:/root/.perf-insight.yaml:ro jupyter_reporting
```
