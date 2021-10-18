#!/bin/bash

#==============================================================================
#         FILE: html_report.sh
#
#        USAGE: ./html_report.sh
#
#  DESCRIPTION: Generate the HTML report on Jupyter Server.
#
#      OPTIONS: ---
# REQUIREMENTS: ---
#         BUGS: ---
#        NOTES: ---
#       AUTHOR: Charles Shih (schrht@gmail.com)
# ORGANIZATION: ---
#      CREATED: Thu Oct 14 12:21:16 PM CST 2021
#     REVISION: Mon Oct 18 12:13:42 PM CST 2021
#==============================================================================

# Parse parameters
[ -z "$1" ] && echo "Usage: $0 <workspace>" >&2 && exit 1

# Prepare environment
cd $1 || exit 1

# Generate report html
jupyter nbconvert --to html --execute ./report_portal.ipynb --output-dir . \
    --ExecutePreprocessor.timeout=300 --TemplateExporter.exclude_input=True \
    --output report.html

# Add shortcut icon to the html
sed -i '/<head>/a <link rel="shortcut icon" href="https://raw.githubusercontent.com/virt-s1/perf-insight/main/logo.jpg"/>' ./report.html

exit 0
