#!/bin/bash

# Description:
#   Process the pbench TestRun. It helps:
#   1. Gather datastore JSON file, and/or
#   2. Generate Plots as SVG files, and/or
#   3. Update the Flask DB.

function show_usage() {
    echo "Process the pbench TestRun."
    echo "$(basename $0) <-t TESTRUNID> [-s] [-p] [-d]"
    echo "  -s: Gather datastore JSON file."
    echo "  -p: Generate Plots as SVG files."
    echo "  -d: Update the Flask DB"
}

while getopts :ht:spd ARGS; do
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
        gather_datastore=yes
        ;;
    p)
        # GeneratePlots option
        generate_plots=yes
        ;;
    d)
        # UpdateDB option
        update_db=yes
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
config=$HOME/.perf-insight.yaml
basepath=$(cat $config | shyaml get-value -q flask.data_path)
repo=$(cat $config | shyaml get-value -q flask.perf_insight_repo)
db=$(cat $config | shyaml get-value -q flask.db_file)

: ${basepath:=/nfs/perf-insight}
: ${repo:=/opt/perf-insight}
: ${db:=/opt/perf-insight/flask/app.db}

utils=$repo/data_process
templates=$repo/data_process/templates

# Verify TestRunID
if [ ! -e $basepath/testruns/$testrun ]; then
    echo "$(basename $0): TestRun ($testrun) cannot be found in $basepath/testruns/" >&2
    exit 1
fi

PATH=$utils:$PATH
cd $basepath/testruns/$testrun

# Generate plots as requested (background)
if [ "$generate_plots" = "yes" ]; then
    echo "Generating Plots..."
    generate_pbench_fio_plots.sh &>./generate_plots.log &
fi

# Create datastore as requested
if [ "$gather_datastore" = "yes" ]; then
    gather_testrun_datastore.py
    [ $? != 0 ] && wait && exit 1
fi

# Update database as requested
if [ "$update_db" = "yes" ]; then
    generate_testrun_results.py --config $templates/generate_testrun_results-flask_fio.yaml &&
        flask_load_db.py --db_file $db --delete $testrun &&
        flask_load_db.py --db_file $db --csv_file ./testrun_results.csv
    [ $? != 0 ] && wait && exit 1
fi

wait

exit 0
