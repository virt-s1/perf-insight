#!/bin/bash

# Description:
#   Process the pbench TestRun. It helps:
#   1. Gather datastore JSON file, and/or
#   2. Generate Plots as SVG files, and/or
#   3. Update the Flask DB.

function show_usage() {
    echo "Process the pbench TestRun."
    echo "$(basename $0) <-t TESTRUNID> [-s] [-d] [-p|-P] "
    echo "  -s: Gather datastore JSON file."
    echo "  -d: Update the Flask DB"
    echo "  -p: Generate Plots as SVG files."
    echo "  -P: Same as '-p', but running in backgroud."
}

while getopts :ht:sdpP ARGS; do
    case $ARGS in
    h)
        # Help option
        show_usage
        exit 0
        ;;
    t)
        # TestRunID option
        testrun=$OPTARG
        ;;
    s)
        # GatherDatastore option
        gather_datastore=1
        ;;
    d)
        # UpdateDB option
        update_db=1
        ;;
    p)
        # GeneratePlots option
        generate_plots=1
        put_background=0
        ;;
    P)
        # GeneratePlots(bg) option
        generate_plots=1
        put_background=1
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

if [ -z $testrun ]; then
    show_usage
    exit 1
fi

# Main
PATH=/usr/local/bin/:$PATH
config=$HOME/.perf-insight.yaml
basepath=$(cat $config | shyaml get-value -q flask.data_path)
repo=$(cat $config | shyaml get-value -q flask.perf_insight_repo)
db=$(cat $config | shyaml get-value -q flask.db_file)

: ${basepath:=/nfs/perf-insight}
: ${repo:=/opt/perf-insight}
: ${db:=/opt/perf-insight/flask/app.db}

PATH=$repo/utils:$repo/data_process:$PATH
templates=$repo/templates

# Verify TestRunID
if [ ! -e $basepath/testruns/$testrun ]; then
    echo "$(basename $0): TestRun ($testrun) cannot be found in $basepath/testruns/" >&2
    exit 1
fi

# Get TestRunType and Platform
testrun_type=${testrun%%_*}
platform=$(echo $testrun | cut -d_ -f2 | tr [:upper:] [:lower:])

# Set environment
cd $basepath/testruns/$testrun

# Generate plots as requested
if [ "$testrun_type" != 'fio' ]; then
    echo "Only fio tests support generating plots."
    generate_plots=0
fi
if [ "$generate_plots" = "1" ]; then
    echo "Generating Plots..."
    if [ "$put_background" = "1" ]; then
        (nohup generate_pbench_fio_plots.sh &>./generate_plots.log &)
        echo "Running in the background..."
    else
        generate_pbench_fio_plots.sh &>./generate_plots.log &
    fi
fi

# Create datastore as requested
if [ "$gather_datastore" = "1" ]; then
    gather_testrun_datastore.py
    [ $? != 0 ] && wait && exit 1
fi

# Update database as requested
if [ "$update_db" = "1" ]; then
    csv_file=./.testrun_results_dbloader.csv
    [ "$testrun_type" = "fio" ] && flag="--storage"
    [ "$testrun_type" = "uperf" ] && flag="--network"

    cfg_file=$templates/generate_testrun_results-${testrun_type}-dbloader-${platform}.yaml
    [ ! -f $cfg_file ] && cfg_file=$templates/generate_testrun_results-${testrun_type}-dbloader.yaml
    echo "DEBUG: Use config file $cfg_file"

    generate_testrun_results.py \
        --config $cfg_file \
        --output $csv_file &&
        cp $db $db.writebackup_$(date +%Y%m%d_%H%M%S) &&
        flask_load_db.py --db_file $db --delete $testrun $flag &&
        flask_load_db.py --db_file $db --csv_file $csv_file $flag
    [ $? != 0 ] && wait && exit 1
fi

wait

exit 0
