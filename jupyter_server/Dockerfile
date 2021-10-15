FROM fedora:34

# Set metadata
LABEL author="Charles Shih"
LABEL maintainer="cheshi@redhat.com"
LABEL version="1.0"
LABEL description="This image provdes environment for Jupyter server of the perf-insight project."

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1

# Install basic packages
RUN dnf install -y psmisc findutils which ncurses tree procps-ng
RUN dnf install -y pip

# Install pip requirements
ADD ./requirements.txt /tmp/requirements.txt
RUN python3 -m pip install -r /tmp/requirements.txt

# Create mount point
RUN mkdir -p /opt/perf-insight /mnt/perf-insight

# Configure application
WORKDIR /app
COPY ./jupyter-server.sh /app/jupyter-server.sh

# During debugging, this entry point will be overridden.
CMD ["/app/jupyter-server.sh"]
