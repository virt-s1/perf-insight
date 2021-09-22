FROM fedora:34

# metadata
LABEL author="Charles Shih"
LABEL maintainer="cheshi@redhat.com"
LABEL version="1.0"
LABEL description="This image provdes environment for dashboard of the perf-insight project."

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1

# configure application
WORKDIR /app

# install basic packages
RUN dnf install -y pip jq psmisc findutils which ncurses tree procps-ng

# install pip requirements
ADD ./requirements.txt /tmp/requirements.txt
RUN python3 -m pip install -r /tmp/requirements.txt

# create mount point
RUN mkdir -p /opt/perf-insight
RUN mkdir -p /data

# Export volumes
VOLUME [ "/root/.perf-insight.yaml" ]
VOLUME [ "/opt/perf-insight" ]
VOLUME [ "/data/app.db" ]

# During debugging, this entry point will be overridden.
CMD ["/bin/bash"]
