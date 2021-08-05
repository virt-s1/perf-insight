#!/bin/bash

# Description:
#   Compare the pbench TestRuns. It helps:
#   1. Make a new path for the report
#   2. Collect all the config and data
#   3. Generate the benchmark report
#   4. [TODO] Update the Flask database

function show_usage() {
    echo "Compare the pbench TestRuns."
    echo "$(basename $0) <-b BASE_TESTRUNID> <-t TEST_TESTRUNID>"
}

while getopts :hb:t: ARGS; do
    case $ARGS in
    h)
        # Help option
        show_usage
        exit 0
        ;;
    b)
        # BaseTestRunID option
        baseid=$OPTARG
        ;;
    t)
        # TestTestRunID option
        testid=$OPTARG
        ;;
    "?")
        echo "$(basename $0): unknown option: $OPTARG" >&2
        ;;
    ":")
        echo "$(basename $0): option requires an argument -- '$OPTARG'" >&2
        echo "Try '$(basename $0) -h' for more information." >&2
        exit 1
        ;;
    *)
        # Unexpected errors
        echo "$(basename $0): unexpected error -- $ARGS" >&2
        echo "Try '$(basename $0) -h' for more information." >&2
        exit 1
        ;;
    esac
done

if [ -z $baseid ] || [ -z $testid ]; then
    show_usage
    exit 1
fi

function get_newpath() {
    # $1: the benchmark report path
    [ -d $1 ] && cd $1
    local lastname=$(ls -d benchmark_* | tail -n 1)
    : ${lastname:="benchmark_000000"}
    local lastnumb=${lastname##*_}
    local nextnumb=$(echo "$lastnumb + 1" | bc)
    local nextname=$(printf "benchmark_%06d" $nextnumb)
    [ -d $1 ] && echo $1/$nextname || echo $nextname
}

# Main
PATH=/usr/local/bin/:$PATH
config=$HOME/.perf-insight.yaml
basepath=$(cat $config | shyaml get-value -q flask.data_path)
repo=$(cat $config | shyaml get-value -q flask.perf_insight_repo)
apache_server=$(cat $config | shyaml get-value -q flask.apache_server)

: ${basepath:=/nfs/perf-insight}
: ${repo:=/opt/perf-insight}
: ${apache_server:=perf-insight.lab.eng.pek2.redhat.com}

PATH=$repo/utils:$repo/data_process:$PATH
templates=$repo/data_process/templates

# Verify TestRunID
if [ ! -d $basepath/testruns/$baseid ]; then
    echo "$(basename $0): TestRun ($baseid) cannot be found in $basepath/testruns/" >&2
    exit 1
fi
if [ ! -d $basepath/testruns/$testid ]; then
    echo "$(basename $0): TestRun ($testid) cannot be found in $basepath/testruns/" >&2
    exit 1
fi

# Get TestRunType
basetype=${baseid%%_*}
testtype=${testid%%_*}
if [ $basetype != $testtype ]; then
    echo "Mismatched TestRunTypes: base is $basetype, while test is $testtype." >&2
    exit 1
else
    testrun_type=$testtype
fi

# Get platform
platform=$(echo $testid | cut -d_ -f2 | tr [:upper:] [:lower:])

# Set environment
workspace=$(get_newpath $basepath/reports)
compareid=$(basename $workspace)
mkdir -p $workspace || exit 1

# Collect config and data
gtr_yaml=$templates/generate_testrun_results-${testrun_type}-${platform}.yaml
[ ! -f $gtr_yaml ] && gtr_yaml=$templates/generate_testrun_results-${testrun_type}.yaml
echo "DEBUG: Use config file $gtr_yaml"
g2b_yaml=$templates/generate_2way_benchmark-${testrun_type}-${platform}.yaml
[ ! -f $g2b_yaml ] && g2b_yaml=$templates/generate_2way_benchmark-${testrun_type}.yaml
echo "DEBUG: Use config file $g2b_yaml"
g2m_yaml=$templates/generate_2way_metadata-${testrun_type}-${platform}.yaml
[ ! -f $g2m_yaml ] && g2m_yaml=$templates/generate_2way_metadata-${testrun_type}.yaml
echo "DEBUG: Use config file $g2m_yaml"

if [ -f $gtr_yaml ]; then
    cp $gtr_yaml $workspace/base.generate_testrun_results.yaml
    cp $gtr_yaml $workspace/test.generate_testrun_results.yaml

    # backward support (all-in-one yaml)
    cat $gtr_yaml >$workspace/benchmark_config.yaml
    echo -e "\n\n" >>$workspace/benchmark_config.yaml
else
    echo "Cannot found GTR yaml ($gtr_yaml) from templates." >&2
    exit 1
fi

if [ -f $g2b_yaml ]; then
    cp $g2b_yaml $workspace/generate_2way_benchmark.yaml

    # backward support (all-in-one yaml)
    cat $g2b_yaml >>$workspace/benchmark_config.yaml
    echo -e "\n\n" >>$workspace/benchmark_config.yaml
else
    echo "Cannot found G2B yaml ($g2b_yaml) from templates." >&2
    exit 1
fi

if [ -f $g2m_yaml ]; then
    cp $g2m_yaml $workspace/generate_2way_metadata.yaml

    # backward support (all-in-one yaml)
    cat $g2m_yaml >>$workspace/benchmark_config.yaml
    echo -e "\n\n" >>$workspace/benchmark_config.yaml
else
    echo "Cannot found G2M yaml ($g2m_yaml) from templates." >&2
    exit 1
fi

cp $basepath/testruns/$baseid/datastore.json $workspace/base.datastore.json || exit 1
cp $basepath/testruns/$baseid/metadata.json $workspace/base.metadata.json || exit 1
cp $basepath/testruns/$testid/datastore.json $workspace/test.datastore.json || exit 1
cp $basepath/testruns/$testid/metadata.json $workspace/test.metadata.json || exit 1

# Generate report
chcon -Rt svirt_sandbox_file_t $workspace
podman run --rm -v $workspace:/workspace:rw \
    -v $config:/root/.perf-insight.yaml:ro jupyter_reporting

# Show results
if [ $? != 0 ]; then
    echo http://$apache_server/perf-insight/reports/$compareid/
else
    echo http://$apache_server/perf-insight/reports/$compareid/report.html
fi

exit 0
