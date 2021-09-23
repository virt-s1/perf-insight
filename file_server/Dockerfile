FROM fedora:34

# Set metadata
LABEL author="Charles Shih"
LABEL maintainer="cheshi@redhat.com"
LABEL version="1.0"
LABEL description="This image provdes environment for file server of the perf-insight project."

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1

# Install basic packages
RUN dnf install -y psmisc findutils which ncurses tree procps-ng
RUN dnf install -y httpd

# Create mount point
RUN mkdir -p /opt/perf-insight /mnt/perf-insight

# Configure application
WORKDIR /app
RUN echo '<html><head><meta http-equiv="refresh" content="0; url=/perf-insight/"/></head></html>' > /var/www/html/index.html
RUN ln -s /mnt/perf-insight /var/www/html/perf-insight
COPY ./httpd-foreground.sh /app/httpd-foreground.sh

# During debugging, this entry point will be overridden.
CMD ["/app/httpd-foreground.sh"]
