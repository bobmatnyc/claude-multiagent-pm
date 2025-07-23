# Claude PM Framework - Comprehensive Deployment Guide

## Overview

This guide provides complete deployment instructions for the Claude PM Framework, covering all deployment scenarios from local development to production environments. The framework supports multiple deployment methods including npm, pip, Docker, and cloud platforms.

## 3-Stage Deployment Model

The Claude PM Framework follows a structured 3-stage deployment model to ensure quality and consistency:

### Stage 1: Development (Automatic)
- **What**: Changes made in the framework source code
- **Where**: This project repository (`claude-multiagent-pm`)
- **When**: Automatic on every file save
- **How**: Development changes are immediately available in the source directory
- **Verification**: Run `./scripts/deploy-3stage.sh dev`

### Stage 2: Local Machine Deployment
- **What**: Deploy framework updates to your local machine
- **Where**: Updates `~/.local/bin/claude-pm` and Python packages
- **When**: After development changes are tested and ready
- **How**: Run `./scripts/deploy-3stage.sh local`
- **Purpose**: Test changes on your actual machine before publishing

### Stage 3: Publish
- **What**: Release to npm and PyPI registries
- **Where**: Public package registries
- **When**: After local testing confirms stability
- **How**: Run `./scripts/deploy-3stage.sh publish`
- **Purpose**: Make changes available to all users

### Quick Deployment Commands

```bash
# Stage 1: Verify development changes
./scripts/deploy-3stage.sh dev

# Stage 2: Deploy to local machine
./scripts/deploy-3stage.sh local

# Stage 3: Publish to registries
./scripts/deploy-3stage.sh publish

# Check deployment status
./scripts/deploy-3stage.sh status
```

### Deployment Workflow Example

When implementing a new feature (like config aliases):

1. **Development Stage**:
   ```bash
   # Make changes to source files
   vim claude_pm/core/config_aliases.py
   
   # Run tests
   pytest tests/unit/test_config_aliases.py
   
   # Verify development stage
   ./scripts/deploy-3stage.sh dev
   ```

2. **Local Deployment Stage**:
   ```bash
   # Deploy to your machine
   ./scripts/deploy-3stage.sh local
   
   # Test the feature locally
   claude-pm --create-config ~/.claude-personal personal
   claude-pm --config personal
   ```

3. **Publication Stage**:
   ```bash
   # After thorough testing
   ./scripts/deploy-3stage.sh publish
   ```

## Table of Contents

1. [3-Stage Deployment Model](#3-stage-deployment-model)
2. [Quick Start](#quick-start)
3. [Installation Methods](#installation-methods)
4. [Local Development Deployment](#local-development-deployment)
5. [Production Deployment](#production-deployment)
6. [Docker Deployment](#docker-deployment)
7. [Cloud Platform Deployment](#cloud-platform-deployment)
8. [Framework Deployment](#framework-deployment)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

## Quick Start

### Fastest Installation

```bash
# Using npm (recommended for most users)
npm install -g @bobmatnyc/claude-multiagent-pm
claude-pm init

# Using pip
pip install claude-multiagent-pm
claude-pm init

# Using pipx (recommended for macOS)
pipx install claude-multiagent-pm
claude-pm init
```

## Installation Methods

### NPM Installation (Recommended)

```bash
# Global installation
npm install -g @bobmatnyc/claude-multiagent-pm

# Project-specific installation
npm install @bobmatnyc/claude-multiagent-pm --save-dev

# Verify installation
claude-pm --version
```

### Python Package Installation

#### Using pip

```bash
# System-wide installation
pip install claude-multiagent-pm

# User installation (avoids permission issues)
pip install --user claude-multiagent-pm

# Development installation
pip install -e .
```

#### Using pipx (Recommended for macOS)

```bash
# Install pipx if not already installed
brew install pipx
pipx ensurepath

# Install Claude PM Framework
pipx install claude-multiagent-pm
```

### Platform-Specific Installation

#### macOS

```bash
# Recommended: Using pipx to avoid Homebrew Python issues
pipx install claude-multiagent-pm

# Alternative: Using npm
npm install -g @bobmatnyc/claude-multiagent-pm
```

#### Linux

```bash
# Using system package manager (Ubuntu/Debian)
sudo apt update
sudo apt install python3 python3-pip nodejs npm
pip install --user claude-multiagent-pm

# Using pipx
pipx install claude-multiagent-pm
```

#### Windows

```bash
# Using pip
pip install claude-multiagent-pm

# Using npm (requires Node.js)
npm install -g @bobmatnyc/claude-multiagent-pm

# Using Chocolatey
choco install claude-pm
```

## Local Development Deployment

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/Bobjayafam/claude-multiagent-pm.git
cd claude-multiagent-pm

# Install development dependencies
npm install
pip install -r requirements/dev.txt

# Link for local development
npm link

# Initialize framework
claude-pm init --dev
```

### Development Workflow

```bash
# Run tests
npm test
pytest tests/

# Start development server
npm run dev

# Watch for changes
npm run watch

# Build for local testing
npm run build
```

### Deploying to Local Projects

```bash
# Deploy to specific directory
npm run deploy -- --target ~/Projects/my-project

# Dry run deployment
npm run deploy:dry-run -- --target ~/Projects/my-project

# Validate deployment
npm run validate-deployment -- --target ~/Projects/my-project
```

## Production Deployment

### Pre-Deployment Checklist

- [ ] System meets minimum requirements (Python 3.8+, Node.js 16+)
- [ ] API keys configured for AI services
- [ ] Backup strategy in place
- [ ] Monitoring and logging configured
- [ ] Security scan completed
- [ ] Performance benchmarks established

### Production Installation

#### 1. Environment Preparation

```bash
# Create dedicated user
sudo useradd -r -s /bin/bash claude-pm
sudo mkdir -p /opt/claude-pm
sudo chown claude-pm:claude-pm /opt/claude-pm

# Set environment variables
export CLAUDE_PM_ROOT=/opt/claude-pm
echo "export CLAUDE_PM_ROOT=/opt/claude-pm" | sudo tee /etc/environment.d/claude-pm.conf
```

#### 2. Install Framework

```bash
# Switch to service user
sudo -u claude-pm -i

# Install framework
cd /opt/claude-pm
npm install -g @bobmatnyc/claude-multiagent-pm

# Initialize with production configuration
claude-pm init --production
```

#### 3. Configure Services

```bash
# Copy systemd service files
sudo cp deployment/systemd/*.service /etc/systemd/system/

# Enable services
sudo systemctl daemon-reload
sudo systemctl enable claude-pm-health-monitor
sudo systemctl start claude-pm-health-monitor

# Verify services
sudo systemctl status claude-pm-health-monitor
```

#### 4. Security Hardening

```bash
# Configure firewall
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS
sudo ufw enable

# Set file permissions
sudo chmod 700 /opt/claude-pm
sudo chmod 600 /opt/claude-pm/.env
sudo chown -R claude-pm:claude-pm /opt/claude-pm

# Configure SSL/TLS
sudo certbot --nginx -d yourdomain.com
```

### Production Configuration

Create `/opt/claude-pm/.env`:

```bash
# Production Environment Configuration
CLAUDE_PM_PRODUCTION=true
CLAUDE_PM_LOG_LEVEL=info
CLAUDE_PM_ROOT=/opt/claude-pm

# API Keys (use secret management in production)
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Performance Settings
CLAUDE_PM_MAX_CONCURRENT_AGENTS=20
CLAUDE_PM_TIMEOUT=120
CLAUDE_PM_CACHE_ENABLED=true

# Security Settings
CLAUDE_PM_VALIDATE_INPUTS=true
CLAUDE_PM_ENFORCE_PERMISSIONS=true
CLAUDE_PM_AUDIT_LOGGING=true
```

## Docker Deployment

### Single Container Deployment

```dockerfile
# Dockerfile
FROM node:18-slim

# Install Python
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Claude PM Framework
RUN npm install -g @bobmatnyc/claude-multiagent-pm

# Create app directory
WORKDIR /app

# Copy project files
COPY . .

# Initialize framework
RUN claude-pm init

# Expose health check port
EXPOSE 8003

# Run the application
CMD ["claude-pm", "serve"]
```

Build and run:

```bash
# Build image
docker build -t claude-pm:latest .

# Run container
docker run -d \
  --name claude-pm \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -v $(pwd):/app \
  -p 8003:8003 \
  claude-pm:latest
```

### Docker Compose Deployment

```yaml
# docker-compose.yml
version: '3.8'

services:
  claude-pm:
    build: .
    container_name: claude-pm
    environment:
      - CLAUDE_PM_PRODUCTION=true
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - CLAUDE_PM_LOG_LEVEL=info
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config:/app/config
    ports:
      - "8003:8003"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8003/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    container_name: claude-pm-redis
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

Deploy with Docker Compose:

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f claude-pm

# Scale services
docker-compose up -d --scale claude-pm=3
```

## Cloud Platform Deployment

### AWS Deployment

#### Using EC2

```bash
# Launch EC2 instance (Amazon Linux 2)
aws ec2 run-instances \
  --image-id ami-0abcdef1234567890 \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-group-ids sg-0123456789abcdef0 \
  --user-data file://user-data.sh

# user-data.sh
#!/bin/bash
yum update -y
yum install -y nodejs python3 git

# Install Claude PM Framework
npm install -g @bobmatnyc/claude-multiagent-pm

# Configure and start
export CLAUDE_PM_ROOT=/opt/claude-pm
claude-pm init --production
```

#### Using ECS/Fargate

```json
{
  "family": "claude-pm-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "claude-pm",
      "image": "your-ecr-repo/claude-pm:latest",
      "essential": true,
      "environment": [
        {"name": "CLAUDE_PM_PRODUCTION", "value": "true"}
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:openai-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/claude-pm",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Google Cloud Platform Deployment

#### Using Compute Engine

```bash
# Create instance
gcloud compute instances create claude-pm-instance \
  --machine-type=e2-medium \
  --image-family=debian-11 \
  --image-project=debian-cloud \
  --metadata-from-file startup-script=startup.sh

# startup.sh
#!/bin/bash
apt-get update
apt-get install -y nodejs npm python3 python3-pip

npm install -g @bobmatnyc/claude-multiagent-pm
export CLAUDE_PM_ROOT=/opt/claude-pm
claude-pm init --production
```

#### Using Cloud Run

```dockerfile
# Dockerfile for Cloud Run
FROM node:18-slim

RUN apt-get update && apt-get install -y python3 python3-pip
RUN npm install -g @bobmatnyc/claude-multiagent-pm

WORKDIR /app
COPY . .

RUN claude-pm init

# Cloud Run expects port 8080
ENV PORT 8080
EXPOSE 8080

CMD ["claude-pm", "serve", "--port", "8080"]
```

Deploy to Cloud Run:

```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT-ID/claude-pm

# Deploy to Cloud Run
gcloud run deploy claude-pm \
  --image gcr.io/PROJECT-ID/claude-pm \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Azure Deployment

#### Using Virtual Machines

```bash
# Create VM
az vm create \
  --resource-group claude-pm-rg \
  --name claude-pm-vm \
  --image UbuntuLTS \
  --size Standard_B2s \
  --admin-username azureuser \
  --generate-ssh-keys \
  --custom-data cloud-init.txt

# cloud-init.txt
#cloud-config
packages:
  - nodejs
  - npm
  - python3
  - python3-pip

runcmd:
  - npm install -g @bobmatnyc/claude-multiagent-pm
  - export CLAUDE_PM_ROOT=/opt/claude-pm
  - claude-pm init --production
```

#### Using Container Instances

```bash
# Deploy container
az container create \
  --resource-group claude-pm-rg \
  --name claude-pm-container \
  --image your-acr.azurecr.io/claude-pm:latest \
  --cpu 1 \
  --memory 2 \
  --environment-variables \
    CLAUDE_PM_PRODUCTION=true \
  --secure-environment-variables \
    OPENAI_API_KEY=$OPENAI_API_KEY \
    ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY
```

## Framework Deployment

### Deploying Framework to Projects

The framework can be deployed to any project directory:

```bash
# Basic deployment
claude-pm deploy --target /path/to/project

# With custom configuration
claude-pm deploy \
  --target /path/to/project \
  --config production \
  --agents "engineer,qa,documentation"

# Verify deployment
claude-pm status --project /path/to/project
```

### Framework File Structure

After deployment, your project will have:

```
project-root/
├── .claude-pm/
│   ├── CLAUDE.md          # Framework configuration
│   ├── config.json        # Project configuration
│   ├── agents/           # Agent definitions
│   │   ├── project-specific/
│   │   ├── user-agents/
│   │   └── system/
│   ├── logs/            # Framework logs
│   └── cache/           # Performance cache
├── bin/
│   ├── claude-pm        # CLI wrapper
│   └── atd              # Ticketing wrapper
└── scripts/
    └── health-check.sh  # Health monitoring
```

### Multi-Project Management

```bash
# Deploy to multiple projects
for project in ~/Projects/*; do
  claude-pm deploy --target "$project" --config shared
done

# Update all deployments
claude-pm update --all-projects

# Check health across projects
claude-pm health --scan ~/Projects
```

## Troubleshooting

### Common Installation Issues

#### NPM Installation Fails

```bash
# Clear npm cache
npm cache clean --force

# Try with different registry
npm install -g @bobmatnyc/claude-multiagent-pm --registry https://registry.npmjs.org/

# Install with verbose logging
npm install -g @bobmatnyc/claude-multiagent-pm --verbose
```

#### Python Installation Issues

```bash
# macOS external environment error
# Solution: Use pipx instead
pipx install claude-multiagent-pm

# Permission denied errors
# Solution: Use user installation
pip install --user claude-multiagent-pm

# Version conflicts
# Solution: Use virtual environment
python -m venv claude-env
source claude-env/bin/activate
pip install claude-multiagent-pm
```

#### Framework Initialization Fails

```bash
# Check permissions
ls -la ~/.claude-pm

# Fix permissions
chmod 755 ~/.claude-pm
chmod 644 ~/.claude-pm/config.json

# Reinitialize with debug logging
claude-pm init --debug --force

# Manual initialization
mkdir -p .claude-pm/agents
cp /usr/local/lib/node_modules/@bobmatnyc/claude-multiagent-pm/framework/CLAUDE.md .claude-pm/
```

### Deployment Validation

```bash
# Run comprehensive health check
claude-pm health --comprehensive

# Check specific components
claude-pm health --check agents
claude-pm health --check api-keys
claude-pm health --check permissions

# Generate diagnostic report
claude-pm diagnose --output diagnostic-report.json
```

### Performance Issues

```bash
# Check resource usage
claude-pm stats

# Clear cache
claude-pm cache clear

# Optimize performance
claude-pm optimize --aggressive

# Monitor in real-time
claude-pm monitor --interval 5
```

### API Key Issues

```bash
# Validate API keys
claude-pm config validate-keys

# Update API keys
claude-pm config set OPENAI_API_KEY "your-new-key"
claude-pm config set ANTHROPIC_API_KEY "your-new-key"

# Use environment variables
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
```

## Best Practices

### Security Best Practices

1. **Never commit API keys** - Use environment variables or secret management
2. **Run with least privileges** - Use dedicated service accounts
3. **Enable audit logging** - Track all agent activities
4. **Regular security scans** - Use automated vulnerability scanning
5. **Keep dependencies updated** - Regular updates for security patches

### Performance Best Practices

1. **Enable caching** - Reduces API calls and improves response time
2. **Limit concurrent agents** - Prevent resource exhaustion
3. **Monitor resource usage** - Set up alerts for high usage
4. **Use appropriate timeouts** - Prevent hanging operations
5. **Regular cache cleanup** - Prevent disk space issues

### Operational Best Practices

1. **Automated backups** - Regular backup of configurations and data
2. **Health monitoring** - Continuous monitoring with alerts
3. **Logging strategy** - Centralized logging with rotation
4. **Deployment automation** - Use CI/CD for updates
5. **Documentation** - Keep deployment docs updated

### Development Best Practices

1. **Test deployments first** - Always test in staging
2. **Version control** - Track all configuration changes
3. **Rollback plan** - Have a tested rollback procedure
4. **Monitor after deployment** - Watch for issues post-deployment
5. **Incremental updates** - Deploy changes gradually

---

## Quick Reference

### Essential Commands

```bash
# Installation
npm install -g @bobmatnyc/claude-multiagent-pm
claude-pm init

# Deployment
claude-pm deploy --target /path/to/project
claude-pm validate --project /path/to/project

# Health Checks
claude-pm health
claude-pm diagnose

# Updates
claude-pm update
claude-pm update --check

# Configuration
claude-pm config list
claude-pm config set KEY value
```

### Environment Variables

```bash
CLAUDE_PM_ROOT          # Framework root directory
CLAUDE_PM_PRODUCTION    # Production mode flag
CLAUDE_PM_LOG_LEVEL     # Logging level (debug/info/warn/error)
OPENAI_API_KEY          # OpenAI API key
ANTHROPIC_API_KEY       # Anthropic API key
CLAUDE_PM_CACHE_ENABLED # Enable/disable caching
```

### Support

- **Documentation**: https://docs.claude-pm.ai
- **Issues**: https://github.com/Bobjayafam/claude-multiagent-pm/issues
- **Community**: Discord/Slack channels
- **Email**: support@claude-pm.ai

---

*Last updated: July 2025 | Framework Version: 1.4.5*