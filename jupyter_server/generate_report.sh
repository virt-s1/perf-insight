#!/bin/bash

# Parse parameters
[ -z "$1" ] && echo "Usage: $0 <workspace>" >&2 && exit 1

# Prepare environment
cd ${1:-"/workspace"} || exit 1

# # Generate report html
# jupyter nbconvert --to html --execute report_portal.ipynb --output-dir $PWD \
#     --ExecutePreprocessor.timeout=240 --TemplateExporter.exclude_input=True \
#     --output report.html &>nbconvert.log

# # Add shortcut icon to the html
# sed -i '/<head>/a <link rel="shortcut icon" href="https://raw.githubusercontent.com/virt-s1/perf-insight/main/logo.jpg"/>' ./report.html

touch ./report.html
exit 0
