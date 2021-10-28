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

# Documentation

## Datastore

The "datastore" is a structured json file. It is a collection of the pbench data (ie the `result.json` files).
A script named `gather_testrun_datastore.py` is provided in `utils` to help you do this. The output file is usually called `datastore.json`.

## Test Results

The "Test Results" is a CSV file, which can be used for DB loading or Benchmark Report generation.
A script named `generate_testrun_results.py` is provided in `utils` to help you do this. The output file is usually called `testrun_results.csv`.

In addition, the user also needs to provide a configuration file named `generate_testrun_results.yaml` to complete this process.
You can find many examples of this configuration file in the `templates` folder. In most cases, you can use them directly to complete the work.

If you want to make some customizations, a detailed description of this configuration is provided below (let us take `fio` as an example):

```yaml
testrun_results_generator:            # This is a keyword associated with generate_testrun_results.py
  defaults:                           # This section defines the default behavior
    split: yes                        # This function splits the sample into separate cases
    round: 6                          # All numeric data will retain 6 decimal places
    fillna: "NaN"                     # The string to be filled in when the data does not exist
  columns:                            # This section defines the columns (attributes) of each case
    - name: CaseID                    # The display name of this attribute
      method: batch_query_datastore   # Use the `batch_query_datastore` method to get the value
      format: "%s-%s-%sd-%sj"         # This value will be generated by `format % (jqexpr[:])`
      jqexpr:                         # Define the jq expression used to get specific data from the datastore
        - ".iteration_data.parameters.benchmark[].rw"
        - ".iteration_data.parameters.benchmark[].bs"
        - ".iteration_data.parameters.benchmark[].iodepth"
        - ".iteration_data.parameters.benchmark[].numjobs"
    - name: RW                                                # The display name
      method: query_datastore                                 # Use the `query_datastore` method
      jqexpr: ".iteration_data.parameters.benchmark[].rw"     # The jq expression used to get the value
    - name: LAT
      method: query_datastore
      jqexpr: '.iteration_data.latency.lat[] | select(.client_hostname=="all") | .samples[].value'
      unit: ms                        # The unit will be placed in brackets after the display name
      factor: 0.000001                # The factor for unit conversion
      round: 3                        # Retain 3 decimal places (overwrite the default value 6)
    - name: Sample                    # Add this attribute if you want to distinguish each sample
      method: get_sample              # The `query_datastore` method will name each sample sequentially
    - name: Testrun
      method: query_metadata          # The `query_metadata` method gets the value from the metadata json file
      key: testrun-id                 # The key in the metadata json block
    - name: Path
      method: get_source_url          # The `get source url` method obtains the source data URL (or part of it)
                                      # of the current case by processing the relevant data in the datastore
```

## Benchmark Results

The "Benchmark Results" is a CSV file, which can be used for Benchmark Report generation.
A script named `generate_benchmark_results.py` is provided in `utils` to help you do this. The output file is usually called `benchmark_results.csv`.

In addition, the user also needs to provide a configuration file named `generate_benchmark_results.yaml` to complete this process.
You can find examples of this configuration file in the `templates` folder. In most cases, you can use them directly to complete the work.

If you want to make some customizations, a detailed description of this configuration is provided below (let us take `fio` as an example):

```yaml
benchmark_comparison_generator:       # This is a keyword associated with generate_benchmark_results.py
  functions:                          # This section defines some function switches
    report_items: combined_base       # This option is used to handle the case when BASE and TEST sets are different;
                                      # `combined_base` means that a combination of BASE and TEST will be used, while
                                      # `test_only` will generate reports based on the TEST set.
    case_conclusion: yes              # Generate overall conclusions for each case in the report
    case_conclusion_abbr: no          # Don't use abbreviations in the overall conclusion
  defaults:                           # This section defines the default behavior
    round: 6                          # All numeric data will retain 6 decimal places
    round_pct: 2                      # All percentage data will retain 2 decimal places
    use_abbr: yes                     # Use abbreviations in the overall conclusion (like "DR" for "Dramatic Regression")
    fillna: "NaN"                     # The string to be filled in when the data does not exist
  kpi_defaults:                       # This section defines the default behavior for KPIs
    higher_is_better: yes             # The higher the value, the better
    max_pctdev_threshold: 0.10        # When the standard deviation of any sample in BASE or TEST is higher than 10%,
                                      # The case will be judged as "High Variance". (A value of zero will disable this feature)
    confidence_threshold: 0.95        # The significance threshold (1-p) for the T-test. If this value is higher than 95%,
                                      # it is considered that there is a significant difference between the samples.
    negligible_threshold: 0.05        # Mark differences within 5% as negligible changes
    regression_threshold: 0.10        # Mark differences greater than 10% as dramatic changes (the difference between 5%
                                      # and 10% will be marked as a moderate changes)
  keys:                               # This section defines the key to associate the BASE and TEST samples
    - name: CaseID
    - name: RW
    - name: BS
    - name: IOdepth
    - name: Numjobs
  kpis:                               # This section defines the KPIs to be measured
    - name: IOPS
      round: 1
    - name: LAT                       # The display name of the KPI
      unit: ms                        # The unit of value (shouldn't be changed)
      from: LAT(ms)                   # The attribute's name in the "Test Results"
      higher_is_better: no            # For latency, the lower it is, the better
      round: 3                        # Retain 3 decimal places (overwrite the default value 6)
    - name: CLAT
      unit: ms
      from: CLAT(ms)
      higher_is_better: no
      round: 3
      max_pctdev_threshold: 0.00      # Disable checking SD%
      negligible_threshold: 0.20
      regression_threshold: 0.20      # Mark differences greater than 20% as drastic changes and ignore other differences.
```
