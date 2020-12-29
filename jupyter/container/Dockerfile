FROM fedora:32

# metadata
LABEL author="Yuxin Sun"
LABEL maintainer="yuxisun@redhat.com"
LABEL version="1.0"
LABEL description="This image provdes a running environment for jupyter reporting."

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1

# configure application
WORKDIR /jupyter

# install basic packages
RUN dnf install -y python3-pip

# install pip requirements
ADD ./jupyter/container/requirements.txt ./container/requirements.txt
RUN pip install -r ./container/requirements.txt

# add source code
ADD ./jupyter /jupyter
ADD ./data_process /data_process

# create mount point
RUN mkdir -p /workspace

# Export volumes
VOLUME [ "/workspace" ]

# During debugging, this entry point will be overridden.
CMD ["jupyter", "nbconvert", "--to", "html", \
    "--execute", "report_portal.ipynb", "--output-dir", \
    "/workspace", "--ExecutePreprocessor.timeout=240", \
    "--TemplateExporter.exclude_input=True","--output", "report.html"]
