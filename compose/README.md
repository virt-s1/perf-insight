# Introduction

The perf-insight services can be managed by podman-compose now.

# Usage

## Setup

`dnf install -y podman-compose`

## Config

Provision the data according to your needs.

`vi ./compose/.env`

## Manage the services

```bash
cd ./compose

# Start services
podman-compose up -d

# Stop services
podman-compose down -t 1

# List services
podman-compose ps
```
