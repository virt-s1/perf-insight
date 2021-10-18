# Convert to html
jupyter nbconvert --to html --execute report_portal.ipynb --output-dir /workspace --ExecutePreprocessor.timeout=240 --TemplateExporter.exclude_input=True --output report.html

# Add shortcut icon
sed -i '/<head>/a <link rel="shortcut icon" href="https://raw.githubusercontent.com/virt-s1/perf-insight/main/flask/app/static/img/logo.jpg" />' /workspace/report.html
