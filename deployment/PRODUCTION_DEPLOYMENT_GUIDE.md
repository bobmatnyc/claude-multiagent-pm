# Claude PM Framework - Production Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying Claude PM Framework in production environments with CLAUDE_PM_ROOT support (M01-039).

## Pre-Deployment Checklist

### System Requirements

- [ ] **Operating System**: Linux (Ubuntu 20.04+, CentOS 8+, or RHEL 8+)
- [ ] **Python**: Version 3.9 or higher
- [ ] **Memory**: Minimum 4GB RAM (8GB+ recommended)
- [ ] **Storage**: Minimum 20GB free space (50GB+ recommended)
- [ ] **Network**: Stable internet connection for dependencies

### Security Requirements

- [ ] **User Account**: Dedicated service account (non-root)
- [ ] **Firewall**: Configured to allow only necessary ports
- [ ] **SSL/TLS**: Valid certificates for HTTPS
- [ ] **Secrets Management**: Secure storage for API keys and passwords
- [ ] **Backup Strategy**: Automated backup solution configured

### Infrastructure Requirements

- [ ] **Load Balancer**: Configured if using multiple instances
- [ ] **Database**: PostgreSQL or equivalent (if not using SQLite)
- [ ] **Monitoring**: Log aggregation and metrics collection
- [ ] **Alerting**: Email/Slack notifications configured

## Production Deployment Steps

### Step 1: Environment Preparation

1. **Create service user**:
   ```bash
   sudo useradd -r -s /bin/bash claude-pm
   sudo mkdir -p /opt/claude-pm
   sudo chown claude-pm:claude-pm /opt/claude-pm
   ```

2. **Set environment variables**:
   ```bash
   export CLAUDE_PM_ROOT=/opt/claude-pm
   echo "export CLAUDE_PM_ROOT=/opt/claude-pm" | sudo tee /etc/environment.d/claude-pm.conf
   ```

3. **Install system dependencies**:
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-venv python3-pip git make curl nginx
   ```

### Step 2: Deployment Configuration

1. **Prepare production environment file**:
   ```bash
   cp deployment/environments/production.env /opt/claude-pm/.env
   ```

2. **Configure production values**:
   ```bash
   sudo -u claude-pm nano /opt/claude-pm/.env
   ```
   
   **Required Changes**:
   - Set `CLAUDE_PM_ROOT=/opt/claude-pm`
   - Replace all `REPLACE_WITH_*` values
   - Configure database URLs
   - Set secure session secrets
   - Configure SMTP settings
   - Set up Slack webhooks

3. **Validate configuration**:
   ```bash
   sudo -u claude-pm ./deployment/scripts/validate.sh
   ```

### Step 3: Framework Installation

1. **Run production deployment**:
   ```bash
   sudo -u claude-pm ./deployment/scripts/deploy.sh production --backup
   ```

2. **Verify installation**:
   ```bash
   sudo -u claude-pm -i
   cd /opt/claude-pm
   source .venv/bin/activate
   claude-pm util info
   claude-pm health check
   ```

### Step 4: Service Configuration

1. **Install systemd services**:
   ```bash
   # Copy service files
   sudo cp /opt/claude-pm/claude-pm-health-monitor.service /etc/systemd/system/
   
   # Update paths in service files
   sudo sed -i "s|/path/to/claude-pm|/opt/claude-pm|g" /etc/systemd/system/claude-pm-*.service
   
   # Enable and start services
   sudo systemctl daemon-reload
   sudo systemctl enable claude-pm-health-monitor
   sudo systemctl start claude-pm-health-monitor
   ```

2. **Configure nginx (if using)**:
   ```bash
   sudo cp deployment/nginx/claude-pm.conf /etc/nginx/sites-available/
   sudo ln -s /etc/nginx/sites-available/claude-pm.conf /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

3. **Set up cron jobs**:
   ```bash
   sudo -u claude-pm crontab deployment/cron/claude-pm.cron
   ```

### Step 5: Security Hardening

1. **Configure firewall**:
   ```bash
   sudo ufw allow ssh
   sudo ufw allow 80
   sudo ufw allow 443
   sudo ufw allow 8003  # API port
   sudo ufw enable
   ```

2. **Set up SSL certificates**:
   ```bash
   # Using Let's Encrypt
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

3. **Secure file permissions**:
   ```bash
   sudo chmod 700 /opt/claude-pm
   sudo chmod 600 /opt/claude-pm/.env
   sudo chown -R claude-pm:claude-pm /opt/claude-pm
   ```

### Step 6: Monitoring & Logging

1. **Configure log rotation**:
   ```bash
   sudo tee /etc/logrotate.d/claude-pm << EOF
   /opt/claude-pm/logs/*.log {
       daily
       rotate 30
       compress
       delaycompress
       missingok
       notifempty
       create 644 claude-pm claude-pm
   }
   EOF
   ```

2. **Set up monitoring dashboards**:
   ```bash
   # Configure your monitoring solution (Grafana, Datadog, etc.)
   # Point to Claude PM metrics endpoints
   ```

3. **Test alerting**:
   ```bash
   sudo -u claude-pm claude-pm health check --test-alerts
   ```

## Docker Production Deployment

### Using Docker Compose

1. **Prepare production compose**:
   ```bash
   cp deployment/docker/docker-compose.prod.yml docker-compose.yml
   ```

2. **Configure environment**:
   ```bash
   # Create production .env file
   cat > .env << EOF
   CLAUDE_PM_VERSION=3.0.0
   CLAUDE_PM_SESSION_SECRET=your_secure_secret_here
   MEM0AI_API_KEY=your_mem0ai_api_key
   REDIS_PASSWORD=your_redis_password
   # ... other production variables
   EOF
   ```

3. **Create data directories**:
   ```bash
   sudo mkdir -p /opt/claude-pm/{data,logs,config,backups,mem0ai-data,redis-data}
   sudo chown -R 1000:1000 /opt/claude-pm
   ```

4. **Deploy containers**:
   ```bash
   docker-compose up -d
   ```

5. **Verify deployment**:
   ```bash
   docker-compose ps
   docker-compose logs claude-pm
   curl http://localhost:8003/health
   ```

## Cloud Provider Deployment

### AWS Deployment

1. **Prepare infrastructure**:
   ```bash
   # Use provided Terraform/CloudFormation templates
   cd deployment/cloud/aws
   terraform init
   terraform plan -var="claude_pm_root=/opt/claude-pm"
   terraform apply
   ```

2. **Configure auto-scaling**:
   ```bash
   # Set up Auto Scaling Groups
   # Configure load balancer health checks
   # Set up CloudWatch monitoring
   ```

### GCP Deployment

1. **Prepare infrastructure**:
   ```bash
   cd deployment/cloud/gcp
   gcloud deployment-manager deployments create claude-pm \
     --config claude-pm.yaml \
     --properties="claudePmRoot:/opt/claude-pm"
   ```

### Azure Deployment

1. **Prepare infrastructure**:
   ```bash
   cd deployment/cloud/azure
   az deployment group create \
     --resource-group claude-pm-rg \
     --template-file claude-pm.json \
     --parameters claudePmRoot=/opt/claude-pm
   ```

## Post-Deployment Validation

### Functional Testing

1. **Basic functionality**:
   ```bash
   curl -f http://localhost:8003/health
   claude-pm util info
   claude-pm project list
   claude-pm health check
   ```

2. **Memory service integration**:
   ```bash
   claude-pm memory stats test-project
   ```

3. **Multi-agent orchestration**:
   ```bash
   claude-pm workflows list
   claude-pm agents status
   ```

### Performance Testing

1. **Load testing**:
   ```bash
   # Use tools like Apache Bench, wrk, or custom scripts
   ab -n 1000 -c 10 http://localhost:8003/api/health
   ```

2. **Memory usage monitoring**:
   ```bash
   htop
   docker stats  # if using Docker
   ```

3. **Response time validation**:
   ```bash
   # Monitor response times under normal load
   curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8003/api/health
   ```

### Security Testing

1. **Vulnerability scanning**:
   ```bash
   # Use tools like OWASP ZAP, nmap, or commercial scanners
   nmap -sV -sC localhost
   ```

2. **SSL/TLS validation**:
   ```bash
   curl -I https://yourdomain.com
   openssl s_client -connect yourdomain.com:443 -servername yourdomain.com
   ```

3. **Access control testing**:
   ```bash
   # Test that unauthorized endpoints return proper errors
   curl -I http://localhost:8003/admin
   ```

## Backup & Recovery

### Automated Backups

1. **Database backups**:
   ```bash
   # Set up automated database dumps
   0 2 * * * /opt/claude-pm/scripts/backup-database.sh
   ```

2. **File system backups**:
   ```bash
   # Set up automated file backups
   0 3 * * * rsync -av /opt/claude-pm/ /backup/claude-pm/
   ```

3. **Cloud backups** (optional):
   ```bash
   # Configure S3/GCS/Azure Blob backup
   aws s3 sync /opt/claude-pm/data s3://claude-pm-backups/data/
   ```

### Recovery Procedures

1. **Test recovery process**:
   ```bash
   # Document and test your recovery procedures
   ./deployment/scripts/test-recovery.sh
   ```

2. **Disaster recovery plan**:
   ```bash
   # Document RTO/RPO requirements
   # Test failover procedures
   # Validate backup integrity
   ```

## Maintenance

### Regular Tasks

- [ ] **Weekly**: Review logs and metrics
- [ ] **Monthly**: Update dependencies and security patches
- [ ] **Quarterly**: Review and test backup/recovery procedures
- [ ] **Annually**: Security audit and penetration testing

### Monitoring Checklist

- [ ] **System Health**: CPU, memory, disk usage
- [ ] **Application Health**: Service availability, response times
- [ ] **Security**: Failed login attempts, unusual traffic patterns
- [ ] **Business Metrics**: Task completion rates, error rates

### Update Procedures

1. **Staging deployment**:
   ```bash
   # Test updates in staging first
   export CLAUDE_PM_ROOT=/opt/claude-pm-staging
   ./deployment/scripts/deploy.sh staging
   ```

2. **Production update**:
   ```bash
   # Blue-green deployment recommended
   ./deployment/scripts/deploy.sh production --backup
   ```

## Troubleshooting

### Common Issues

1. **Service won't start**:
   ```bash
   sudo systemctl status claude-pm-health-monitor
   sudo journalctl -u claude-pm-health-monitor -f
   ```

2. **Memory service connection issues**:
   ```bash
   nc -zv localhost 8002
   curl http://localhost:8002/health
   ```

3. **Performance issues**:
   ```bash
   htop
   iotop
   netstat -tulpn
   ```

### Log Locations

- **Application logs**: `/opt/claude-pm/logs/`
- **System logs**: `/var/log/syslog`
- **Service logs**: `sudo journalctl -u claude-pm-*`
- **Nginx logs**: `/var/log/nginx/`

### Getting Support

1. **Run diagnostics**:
   ```bash
   claude-pm util doctor
   ./deployment/scripts/validate.sh
   ```

2. **Collect logs**:
   ```bash
   tar -czf claude-pm-logs-$(date +%Y%m%d).tar.gz /opt/claude-pm/logs/
   ```

3. **Performance metrics**:
   ```bash
   claude-pm analytics productivity --format=csv > metrics.csv
   ```

## Production Checklist

### Pre-Go-Live

- [ ] All secrets configured securely
- [ ] SSL/TLS certificates installed and valid
- [ ] Monitoring and alerting configured
- [ ] Backup procedures tested
- [ ] Load testing completed
- [ ] Security scanning performed
- [ ] Documentation updated
- [ ] Team trained on operations

### Go-Live

- [ ] DNS updated to point to production
- [ ] Health checks passing
- [ ] Monitoring confirms normal operation
- [ ] All services started and stable
- [ ] Performance within acceptable limits

### Post-Go-Live

- [ ] Monitor for 24-48 hours
- [ ] Validate all functionality
- [ ] Confirm backups are working
- [ ] Team is comfortable with operations
- [ ] Incident response procedures tested

---

**Important**: This is a comprehensive production deployment guide. Adapt it to your specific infrastructure and requirements. Always test in staging before deploying to production.