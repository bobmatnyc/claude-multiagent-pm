# Claude PM Framework Deployment Guide

## Overview

This directory contains deployment templates and configurations for the Claude PM Framework with CLAUDE_PM_ROOT environment variable support.

## Quick Start

### 1. Choose Your Deployment Type

- **Development**: Local development with hot reloading
- **Staging**: Testing environment with production-like settings
- **Production**: Full production deployment with monitoring
- **Docker**: Containerized deployment
- **Cloud**: AWS/GCP/Azure deployment

### 2. Environment Configuration

Set your deployment location:

```bash
# Default location (~/Projects/Claude-PM)
# No environment variable needed

# Custom location
export CLAUDE_PM_ROOT=/opt/claude-pm
export CLAUDE_PM_ROOT=/Users/username/my-projects/claude-pm
export CLAUDE_PM_ROOT=/srv/applications/claude-pm
```

### 3. Deploy

```bash
# Copy appropriate template
cp deployment/environments/development.env .env

# Configure your environment
nano .env

# Run deployment
./deployment/scripts/deploy.sh development
```

## Directory Structure

```
deployment/
├── README.md                    # This file
├── environments/               # Environment configuration templates
│   ├── development.env
│   ├── staging.env
│   ├── production.env
│   └── docker.env
├── scripts/                    # Deployment scripts
│   ├── deploy.sh
│   ├── validate.sh
│   └── migrate.sh
├── docker/                     # Docker configurations
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── docker-compose.prod.yml
├── cloud/                      # Cloud provider templates
│   ├── aws/
│   ├── gcp/
│   └── azure/
└── monitoring/                 # Monitoring configurations
    ├── health-checks.yml
    └── alerts.yml
```

## Migration from Existing Installations

If you have an existing Claude PM installation, see [Migration Guide](migration/README.md).

## Support

For deployment issues:
1. Run `claude-pm util doctor` for diagnostics
2. Check [Troubleshooting Guide](troubleshooting.md)
3. Review deployment logs in `logs/deployment.log`