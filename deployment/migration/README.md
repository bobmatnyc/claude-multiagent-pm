# Claude PM Framework - Migration Guide

## Overview

This guide helps you migrate existing Claude PM installations to support the new CLAUDE_PM_ROOT environment variable system (M01-039).

## What Changed (M01-039)

The Claude PM Framework now supports customizable installation paths through the `CLAUDE_PM_ROOT` environment variable:

- **Before**: Fixed path at `~/Projects/Claude-PM`
- **After**: Configurable path via `CLAUDE_PM_ROOT` environment variable
- **Default**: Still `~/Projects/Claude-PM` if not set

## Migration Scenarios

### Scenario 1: Keep Current Location

If you want to keep your installation at the current location:

```bash
# No migration needed - everything works as before
# Optional: Set environment variable for clarity
export CLAUDE_PM_ROOT="/Users/username/Projects/Claude-PM"
```

### Scenario 2: Move to Custom Location

If you want to move your installation to a new location:

```bash
# Use the migration script
./deployment/scripts/migrate.sh /opt/claude-pm

# Or manually
export CLAUDE_PM_ROOT=/opt/claude-pm
./deployment/scripts/migrate.sh
```

### Scenario 3: Multiple Environments

If you want different installations for different purposes:

```bash
# Production installation
export CLAUDE_PM_ROOT=/opt/claude-pm-prod
./deployment/scripts/deploy.sh production

# Development installation  
export CLAUDE_PM_ROOT=/home/dev/claude-pm-dev
./deployment/scripts/deploy.sh development
```

## Migration Methods

### Method 1: Automated Migration Script

The easiest way to migrate:

```bash
# Validate current installation
./deployment/scripts/validate.sh

# Dry run to see what would happen
./deployment/scripts/migrate.sh --dry-run /new/path

# Migrate with backup
./deployment/scripts/migrate.sh --backup /new/path

# Force migration (no prompts)
./deployment/scripts/migrate.sh --force /new/path
```

### Method 2: Manual Migration

For more control over the process:

1. **Stop services**:
   ```bash
   pm2 stop all
   sudo systemctl stop claude-pm-health-monitor
   ```

2. **Create backup**:
   ```bash
   cp -r ~/Projects/Claude-PM ~/claude-pm-backup-$(date +%Y%m%d)
   ```

3. **Create new location**:
   ```bash
   export CLAUDE_PM_ROOT=/opt/claude-pm
   mkdir -p /opt/claude-pm
   ```

4. **Copy files**:
   ```bash
   rsync -av --exclude='.venv' ~/Projects/Claude-PM/ /opt/claude-pm/
   ```

5. **Recreate virtual environment**:
   ```bash
   cd /opt/claude-pm
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements/production.txt
   pip install -e .
   ```

6. **Update configuration**:
   ```bash
   echo "CLAUDE_PM_ROOT=/opt/claude-pm" >> .env
   ```

7. **Test installation**:
   ```bash
   claude-pm util info
   claude-pm health check
   ```

### Method 3: Fresh Installation

For a clean start:

```bash
# Set new location
export CLAUDE_PM_ROOT=/srv/claude-pm

# Deploy fresh installation
./deployment/scripts/deploy.sh production

# Import data from old installation (optional)
# Copy specific files/data you want to preserve
```

## Service Updates

After migration, update services to use the new path:

### Systemd Services

```bash
# Update service file
sudo sed -i "s|/old/path|$CLAUDE_PM_ROOT|g" /etc/systemd/system/claude-pm-*.service

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart claude-pm-health-monitor
```

### PM2 Services

```bash
# Update ecosystem file
sed -i "s|cwd: '/old/path'|cwd: '$CLAUDE_PM_ROOT'|" ecosystem.config.js

# Restart services
pm2 restart all
```

### Cron Jobs

```bash
# Update cron jobs
crontab -l | sed "s|/old/path|$CLAUDE_PM_ROOT|g" | crontab -
```

## Environment Variable Management

### Shell Profile

Add to your shell profile for permanent configuration:

```bash
# For Bash
echo "export CLAUDE_PM_ROOT=/opt/claude-pm" >> ~/.bashrc

# For Zsh  
echo "export CLAUDE_PM_ROOT=/opt/claude-pm" >> ~/.zshrc

# For Fish
echo "set -gx CLAUDE_PM_ROOT /opt/claude-pm" >> ~/.config/fish/config.fish
```

### System-wide Configuration

For system-wide settings:

```bash
# Create system environment file
sudo tee /etc/environment.d/claude-pm.conf << EOF
CLAUDE_PM_ROOT=/opt/claude-pm
EOF

# Or add to /etc/environment
echo "CLAUDE_PM_ROOT=/opt/claude-pm" | sudo tee -a /etc/environment
```

### Docker Environment

For Docker deployments:

```bash
# In docker-compose.yml
environment:
  - CLAUDE_PM_ROOT=/app/claude-pm

# Or in .env file
CLAUDE_PM_ROOT=/app/claude-pm
```

## Validation

After migration, validate the installation:

```bash
# Run validation script
./deployment/scripts/validate.sh

# Test framework functionality
claude-pm util info
claude-pm health check
claude-pm project list

# Check configuration
python3 -c "
from claude_pm.core.config import Config
config = Config()
print(f'Claude PM Path: {config.get(\"claude_pm_path\")}')
print(f'Base Path: {config.get(\"base_path\")}')
print(f'Managed Path: {config.get(\"managed_path\")}')
"
```

## Troubleshooting

### Common Issues

1. **Permission Errors**:
   ```bash
   # Fix ownership
   sudo chown -R $USER:$USER $CLAUDE_PM_ROOT
   
   # Fix permissions
   chmod -R 755 $CLAUDE_PM_ROOT
   ```

2. **Virtual Environment Issues**:
   ```bash
   # Remove and recreate
   rm -rf $CLAUDE_PM_ROOT/.venv
   cd $CLAUDE_PM_ROOT
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements/production.txt
   pip install -e .
   ```

3. **Path Not Found**:
   ```bash
   # Check environment variable
   echo $CLAUDE_PM_ROOT
   
   # Verify path exists
   ls -la $CLAUDE_PM_ROOT
   
   # Check configuration
   python3 -c "import os; print(os.environ.get('CLAUDE_PM_ROOT', 'Not set'))"
   ```

4. **Service Startup Issues**:
   ```bash
   # Check logs
   journalctl -u claude-pm-health-monitor -f
   
   # Test manually
   $CLAUDE_PM_ROOT/.venv/bin/python -m claude_pm.cli health check
   ```

### Recovery

If migration fails:

1. **Restore from backup**:
   ```bash
   rm -rf $CLAUDE_PM_ROOT
   cp -r ~/claude-pm-backup-* ~/Projects/Claude-PM
   unset CLAUDE_PM_ROOT
   ```

2. **Reset services**:
   ```bash
   sudo systemctl stop claude-pm-*
   pm2 delete all
   # Reconfigure with original paths
   ```

3. **Get support**:
   ```bash
   # Run diagnostics
   ./deployment/scripts/validate.sh
   
   # Check logs
   tail -f $CLAUDE_PM_ROOT/logs/*.log
   ```

## Migration Checklist

- [ ] Validate current installation
- [ ] Choose new installation path
- [ ] Stop running services
- [ ] Create backup
- [ ] Set CLAUDE_PM_ROOT environment variable
- [ ] Run migration script or manual migration
- [ ] Update service configurations
- [ ] Update environment variables
- [ ] Test installation
- [ ] Restart services
- [ ] Validate functionality
- [ ] Update documentation/scripts
- [ ] Clean up old installation (optional)

## Best Practices

1. **Always backup** before migration
2. **Test in development** first
3. **Use absolute paths** for CLAUDE_PM_ROOT
4. **Document your configuration** for team members
5. **Update CI/CD pipelines** if applicable
6. **Consider security implications** of new paths
7. **Monitor services** after migration
8. **Keep migration logs** for troubleshooting

## Support

For migration issues:
- Run: `./deployment/scripts/validate.sh`
- Check: `$CLAUDE_PM_ROOT/logs/`
- Review: `deployment/README.md`
- Test: `claude-pm util doctor`