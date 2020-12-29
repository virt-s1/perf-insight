# Performance Test Report Portal Jupyter page

### Build image
```
podman build -t jupyter_reporting ./container/
```

### Generate Jupyter report
1. Prepare base/test datastore.json and base/test metadata.json, and benchmark yaml configuration file in a folder:
```
workspace/
├── base.datastore.json
├── base.testrun_metadata.json
├── benchmark_config.yaml
├── test.datastore.json
└── test.testrun_metadata.json
```

2. Change folder selinux context, or cannot read file inside container:
chcon -Rt svirt_sandbox_file_t /workspace

3. podman run --volume /workspace:/workspace:rw jupyter_reporting 
It will generate report.html in your workspace folder.
* if add "--output your_report_name.html", can specify the report file name.
