# Claude PM Scripts Directory

This directory contains utility scripts for the Claude PM Framework, including GitHub sync tools, installation helpers, and development utilities.

## 🔧 Installation Scripts

### macOS Installation Helpers

**`install-claude-pm-macos.sh`** - Quick installer for macOS users
- Handles "externally-managed-environment" errors automatically
- Installs using pipx (recommended method)
- Checks dependencies and Python version
- Usage: `./install-claude-pm-macos.sh`

**`diagnose-macos-python.py`** - Diagnostic tool for macOS Python environments
- Identifies Python installation type (Homebrew, System, etc.)
- Checks for PEP 668 restrictions
- Suggests appropriate installation methods
- Usage: `python3 diagnose-macos-python.py`

## 📦 GitHub Sync System

Production-ready system for syncing Claude PM trackdown tickets to GitHub Issues with comprehensive error handling, logging, and management capabilities.

## 🚀 Quick Start

1. **Setup GitHub Token**
   ```bash
   # Token is already configured in .env file
   echo "GITHUB_TOKEN=your_token_here" >> /Users/masa/Projects/claude-multiagent-pm/.env
   ```

2. **Basic Sync Operation**
   ```bash
   # Navigate to scripts directory
   cd /Users/masa/Projects/claude-multiagent-pm/scripts
   
   # Basic sync (dry run first)
   python github_sync_cli.py sync --repository bobmatnyc/your-repo --dry-run
   
   # Actual sync
   python github_sync_cli.py sync --repository bobmatnyc/your-repo
   ```

3. **Repository Setup** (first time only)
   ```bash
   # Setup labels, milestones, and epic projects
   python github_sync_cli.py setup --repository bobmatnyc/your-repo --setup-epics
   ```

## 📁 File Structure

```
scripts/
├── github_sync.py           # Main sync script with core functionality
├── github_sync_cli.py       # CLI interface for all operations
├── github_utils.py          # GitHub API utilities and helpers
├── sync_logger.py           # Comprehensive logging and monitoring
├── github_sync_config.yaml  # Configuration settings
└── README.md               # This documentation
```

## 🛠️ Core Scripts

### `github_sync.py`
Main synchronization engine with:
- **Ticket Parsing**: Extracts tickets from BACKLOG.md with metadata
- **Issue Management**: Creates/updates GitHub issues with proper labeling
- **Rate Limiting**: Handles GitHub API limits with exponential backoff
- **Error Handling**: Comprehensive error recovery and reporting
- **Backup System**: Creates backups before operations

### `github_sync_cli.py`
Command-line interface providing:
- `sync` - Sync tickets to GitHub Issues
- `status` - Show current sync status and statistics
- `validate` - Verify sync integrity
- `setup` - Initialize repository with labels/milestones
- `report` - Generate comprehensive sync reports
- `cleanup` - Clean old logs and backups

### `github_utils.py`
Advanced GitHub operations:
- **Project Management**: GitHub Projects V2 for epic tracking
- **Search Operations**: Advanced issue searching and filtering
- **Batch Operations**: Efficient bulk operations with rate limiting
- **Validation**: Data integrity checks and validation

### `sync_logger.py`
Enterprise logging system:
- **Structured Events**: JSON-based event logging
- **Error Categorization**: Severity-based error classification
- **Performance Monitoring**: Metrics and health monitoring
- **Alerting**: Automatic alert generation for issues

## 🎯 Features

### Ticket Sync Capabilities
- ✅ **42 Active Tickets**: Syncs all Claude PM Framework tickets
- ✅ **Full Metadata**: Preserves priority, story points, dependencies, epics
- ✅ **Status Tracking**: Handles completed, in-progress, and pending tickets
- ✅ **Milestone Mapping**: Automatically assigns M01/M02/M03 milestones
- ✅ **Epic Organization**: Creates GitHub Projects for epic tracking

### GitHub Integration
- ✅ **Labels**: Automatic creation of priority, type, milestone, epic labels
- ✅ **Milestones**: M01 Foundation, M02 Automation, M03 Orchestration
- ✅ **Projects**: Epic tracking via GitHub Projects V2
- ✅ **Issue Templates**: Consistent issue formatting with metadata
- ✅ **Search**: Advanced searching and filtering capabilities

### Production Features
- ✅ **Rate Limiting**: Intelligent handling with exponential backoff
- ✅ **Error Recovery**: Comprehensive error handling and retry logic
- ✅ **Backup/Rollback**: Automatic backups with rollback capability
- ✅ **Dry Run Mode**: Safe testing without making changes
- ✅ **Monitoring**: Health monitoring and alerting system
- ✅ **Logging**: Structured logging with rotation and archival

## 📋 Commands Reference

### Sync Operations

```bash
# Basic sync (Claude PM → GitHub)
python github_sync_cli.py sync --repository owner/repo

# Dry run (show what would change)
python github_sync_cli.py sync --repository owner/repo --dry-run

# Bidirectional sync
python github_sync_cli.py sync --repository owner/repo --direction bidirectional

# Custom backlog file
python github_sync_cli.py sync --repository owner/repo --backlog-path /path/to/BACKLOG.md

# Verbose logging
python github_sync_cli.py sync --repository owner/repo --verbose
```

### Management Operations

```bash
# Repository setup (labels, milestones, epic projects)
python github_sync_cli.py setup --repository owner/repo --setup-epics

# Check sync status
python github_sync_cli.py status --repository owner/repo

# Validate sync integrity
python github_sync_cli.py validate --repository owner/repo

# Generate sync report
python github_sync_cli.py report --output sync_report.md

# Clean up old logs/backups
python github_sync_cli.py cleanup
```

### Direct Script Usage

```bash
# Direct script usage (legacy interface)
python github_sync.py --repository owner/repo --dry-run --verbose
```

## ⚙️ Configuration

### Environment Variables
```bash
# .env file (already configured)
GITHUB_TOKEN=ghp_your_token_here
GITHUB_OWNER=bobmatnyc
```

### Configuration File
Modify `github_sync_config.yaml` for:
- API rate limiting settings
- Label colors and descriptions
- Milestone due dates
- Sync behavior preferences
- Logging levels

### Required GitHub Permissions
Your GitHub token needs these permissions:
- ✅ **Issues**: Read and write
- ✅ **Metadata**: Read
- ✅ **Projects**: Read and write (for epic tracking)
- ✅ **Pull Requests**: Read (for linking)

## 📊 Ticket Processing

### Supported Ticket Types
The system processes these ticket types from BACKLOG.md:

| Prefix | Type | Example | Epic | Milestone |
|--------|------|---------|------|-----------|
| MEM-* | Memory/AI | MEM-001 | FEP-007 | M01/M02/M03 |
| LGR-* | LangGraph | LGR-001 | FEP-011 | M01 |
| M01-* | Foundation | M01-001 | FEP-001 | M01 |
| M02-* | Automation | M02-001 | FEP-002 | M02 |
| M03-* | Orchestration | M03-001 | FEP-004 | M03 |
| FEP-* | Framework Epic | FEP-007 | Self | Various |
| INT-* | Integration | INT-001 | FEP-002 | M02 |
| INF-* | Infrastructure | INF-001 | FEP-001 | M03 |
| CPT-* | Cross-Project | CPT-001 | FEP-003 | M02 |

### Ticket Format Examples

**Simple Format** (from backlog sections):
```markdown
- [x] **[M01-001]** Establish core Claude PM directory structure
```

**Detailed Format** (from priority sections):
```markdown
### MEM-001: Core mem0AI Integration Setup
**Priority**: CRITICAL
**Story Points**: 8
**Epic**: FEP-007 Claude Max + mem0AI Enhanced Architecture
**Dependencies**: mem0ai service running on port 8002

**Scope**:
- Configure OpenAI API key for mem0ai service
- Create ClaudePMMemory class for project management
```

## 🔍 Monitoring and Debugging

### Log Files
```bash
# Main sync log
tail -f /Users/masa/Projects/claude-multiagent-pm/logs/github_sync.log

# Error-specific log
tail -f /Users/masa/Projects/claude-multiagent-pm/logs/sync_errors.log

# API request log
tail -f /Users/masa/Projects/claude-multiagent-pm/logs/api_requests.log

# Structured events
tail -f /Users/masa/Projects/claude-multiagent-pm/logs/sync_events.jsonl
```

### Backup Location
```bash
# Automatic backups
ls -la /Users/masa/Projects/claude-multiagent-pm/backups/

# Sync state tracking
cat /Users/masa/Projects/claude-multiagent-pm/sync/github_sync_log.json
```

### Health Monitoring
```bash
# Check sync health
python github_sync_cli.py status --repository owner/repo

# Generate detailed report
python github_sync_cli.py report --output detailed_report.md

# Validate data integrity
python github_sync_cli.py validate --repository owner/repo
```

## 🚨 Error Handling

### Common Issues and Solutions

**Rate Limiting**
```bash
# If you hit rate limits, the script will automatically wait
# Monitor with:
grep "Rate limit" /Users/masa/Projects/claude-multiagent-pm/logs/github_sync.log
```

**Authentication Errors**
```bash
# Check token validity
curl -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/user

# Refresh token if needed and update .env file
```

**Validation Errors**
```bash
# Check ticket format in BACKLOG.md
python github_sync_cli.py validate --repository owner/repo

# Review parsing errors
grep "validation" /Users/masa/Projects/claude-multiagent-pm/logs/sync_errors.log
```

**Permission Errors**
```bash
# Verify repository permissions
python -c "
from github_utils import validate_github_permissions
from github_sync import GitHubAPIClient, TokenManager
client = GitHubAPIClient(TokenManager.load_token_from_env())
print(validate_github_permissions(client, 'owner/repo'))
"
```

### Recovery Operations

**Rollback Sync**
```python
# Manual rollback using backup
from github_sync import SyncBackupManager
backup_manager = SyncBackupManager()
backup_manager.rollback_sync('/path/to/backup/file.json')
```

**Clean Sync State**
```bash
# Remove sync records to start fresh
rm /Users/masa/Projects/claude-multiagent-pm/sync/github_sync_log.json

# Clean up GitHub issues (manual via web interface)
# or use GitHub CLI:
gh issue list --repo owner/repo --label "claude-pm-sync"
```

## 📈 Performance

### Optimization Settings
- **Batch Size**: 50 tickets per batch (configurable)
- **Rate Limiting**: Respects GitHub's 5000 req/hour limit
- **Concurrent Requests**: 3 parallel requests max
- **Request Delay**: 100ms between requests
- **Retry Logic**: Exponential backoff with 5 max retries

### Expected Performance
- **Small Repos** (< 50 tickets): 1-2 minutes
- **Medium Repos** (50-100 tickets): 3-5 minutes  
- **Large Repos** (> 100 tickets): 5-10 minutes
- **Rate Limited**: May take longer with automatic delays

## 🔒 Security

### Token Security
- ✅ Tokens stored in `.env` file with restricted permissions
- ✅ Never logged or exposed in output
- ✅ Automatic token validation before operations
- ✅ Support for fine-grained personal access tokens

### Data Protection
- ✅ Automatic backups before destructive operations
- ✅ Dry-run mode for safe testing
- ✅ Read-only mode for trackdown files (no modifications)
- ✅ Comprehensive audit logging

## 🚀 Production Deployment

### CI/CD Integration
```yaml
# Example GitHub Actions workflow
name: Sync Claude PM Tickets
on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install requests
      - name: Sync tickets
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          cd scripts
          python github_sync_cli.py sync --repository ${{ github.repository }}
```

### Monitoring Integration
```bash
# Cron job for health monitoring
*/30 * * * * cd /Users/masa/Projects/claude-multiagent-pm/scripts && python github_sync_cli.py status >> /tmp/sync_health.log
```

### Alerting Setup
```python
# Custom alerting (extend sync_logger.py)
def send_slack_alert(message):
    # Integration with Slack, Discord, etc.
    pass
```

## 📝 Contributing

### Adding New Features
1. **New Ticket Types**: Update `TicketParser._determine_epic()` and related methods
2. **New Labels**: Add to `GitHubLabelManager.ensure_claude_pm_labels()`
3. **Custom Sync Logic**: Extend `ClaudePMGitHubSync` class methods
4. **Additional Commands**: Add to `GitHubSyncCLI` class in `github_sync_cli.py`

### Testing
```bash
# Always test with dry-run first
python github_sync_cli.py sync --repository test-repo --dry-run

# Validate configuration
python github_sync_cli.py setup --repository test-repo

# Check data integrity
python github_sync_cli.py validate --repository test-repo
```

## 📚 Additional Resources

- **GitHub API Documentation**: https://docs.github.com/en/rest
- **Projects V2 API**: https://docs.github.com/en/graphql/reference/objects#projectv2
- **Rate Limiting**: https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting
- **Personal Access Tokens**: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token

---

## 🎯 Summary

This GitHub sync system provides production-ready synchronization between Claude PM Framework trackdown tickets and GitHub Issues with:

- ✅ **Complete Coverage**: All 42 active tickets supported
- ✅ **Production Ready**: Error handling, logging, monitoring
- ✅ **Safe Operations**: Dry-run mode, backups, validation
- ✅ **Comprehensive**: CLI interface, reporting, management tools
- ✅ **Maintainable**: Structured code, documentation, configuration

The system is ready for immediate use and can safely sync all Claude PM Framework tickets to GitHub for enhanced project management and collaboration.

**Next Steps**: Run the setup command, then execute a dry-run sync to see the system in action!