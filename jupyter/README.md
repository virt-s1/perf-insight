# Performance Test Report Portal Jupyter page

### Build image
```
cd perf-insight
podman build -t jupyter_reporting . -f ./jupyter/container/Dockerfile 
```

### Generate Jupyter report
1. Prepare base/test datastore.json and base/test metadata.json, and benchmark yaml configuration file in a folder:
```
workspace/
├── base.datastore.json
├── base.metadata.json
├── benchmark_config.yaml
├── test.datastore.json
└── test.metadata.json
```
Prepare perf_insight.yaml

2. Change folder selinux context, or cannot read file inside container:
```
chcon -Rt svirt_sandbox_file_t /workspace
```

3. Generate report.html in workspace:
```
podman run -v /workspace:/workspace:rw -v perf_insight.yaml:/root/.perf_insight.yaml:ro jupyter_reporting
```
