FROM fedora:32
RUN dnf -y install python3-pip svn && dnf clean all
RUN pip install notebook nbconvert==5.6.1 pandas numpy jq pyyaml ipython scipy
RUN svn checkout https://github.com/virt-s1/perf-insight/trunk/jupyter /jupyter/
RUN svn checkout https://github.com/virt-s1/perf-insight/trunk/data_process /data_process/
WORKDIR "/jupyter"
ENTRYPOINT ["jupyter", "nbconvert", "--to", "html", "--execute", "report_portal.ipynb", "--output-dir", "/workspace", "--ExecutePreprocessor.timeout=120", "--TemplateExporter.exclude_input=True"]
CMD ["--output", "report.html"]
