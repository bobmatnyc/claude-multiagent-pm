# Security Comprehensive Guide - Claude PM Framework

## Overview

This comprehensive guide covers all security aspects of the Claude PM Framework, including mem0AI integration security, pre-push security scanning, agent authority, and best practices for secure development workflows.

## Security Architecture

The Claude PM Framework implements a multi-layered security approach:

1. **Agent-Based Security Authority** - Security Agent with pre-push veto power
2. **API Authentication & Authorization** - Bearer token and custom header authentication
3. **TLS/SSL Encryption** - Secure communication channels
4. **Secrets Management** - Secure storage and rotation of API keys
5. **Vulnerability Detection** - Static and dynamic security analysis
6. **Access Control** - Role-based permissions and authentication
7. **Compliance Framework** - OWASP, HIPAA, PCI DSS, SOC 2 support

## Security Agent Authority

### Agent Role Definition

**Security Agent operates with Pre-Push Security Scanning Authority**

#### Core Authority
- **Veto Power**: Full authority to block pushes based on security violations
- **Scope**: All code and configuration files before origin push
- **Override**: User can explicitly override per-push basis only
- **Escalation**: Critical issues require mandatory remediation

#### Security Posture Framework

**Medium Security (Default)**
- Standard security practices for general development
- Applies to most projects without regulatory requirements
- Balanced approach between security and development velocity

**High Security (Automatic Escalation)**
- Triggered by detection of:
  - HIPAA/healthcare data patterns
  - COPPA/children's data indicators
  - PII handling patterns
  - Financial data processing
  - Government/regulated industry markers
- Enhanced protocols with stricter validation
- Mandatory remediation for Medium+ findings

## Veto Decision Framework

### Critical Issues (Automatic Veto)

**Immediate Block - No Exceptions:**
- Hardcoded secrets, API keys, passwords
- Private keys, certificates in code
- SQL injection vulnerabilities
- Remote code execution risks
- Insecure deserialization

**Veto Response Format:**
```
🚨 SECURITY VETO - CRITICAL ISSUE DETECTED

Issue: Hardcoded API key detected
File: src/config/database.js:15
Pattern: AWS_ACCESS_KEY_ID = "AKIA..."

RESOLUTION REQUIRED:
1. Remove hardcoded secret from code
2. Add to environment variables
3. Update code to use process.env.AWS_ACCESS_KEY_ID
4. Verify secret is not in git history

Push BLOCKED until resolved.
```

### High Issues (Conditional Veto)

**Block with Explanation:**
- Weak cryptography (MD5, SHA1)
- Insecure configurations
- Missing security headers
- Vulnerable dependencies
- Insufficient input validation

### Medium Issues (Warning + High Security Veto)

**Default**: Warning only
**High Security**: Veto with remediation guidance

## Security Scanning Categories

### 1. Secrets Detection (Critical Priority)

#### API Keys & Tokens
```regex
# Generic API key patterns
(?i)(api[_-]?key|apikey|secret[_-]?key|access[_-]?token|auth[_-]?token|bearer[_-]?token)[\s]*[:=][\s]*['"]*[a-zA-Z0-9]{10,}['"]*

# AWS patterns
AKIA[0-9A-Z]{16}
aws_access_key_id\s*=\s*[A-Z0-9]{20}
aws_secret_access_key\s*=\s*[A-Za-z0-9/+=]{40}

# GitHub tokens
ghp_[0-9a-zA-Z]{36}
github_pat_[0-9a-zA-Z_]{82}
```

#### Passwords & Credentials
```regex
# Password patterns
(?i)(password|passwd|pwd|secret|key)[\s]*[:=][\s]*['"]*[^\s'"]{8,}['"]*

# Database connections
(?i)(db[_-]?password|database[_-]?password|mysql[_-]?password|postgres[_-]?password|mongo[_-]?password)
```

#### Certificates & Private Keys
```regex
-----BEGIN (RSA )?PRIVATE KEY-----
-----BEGIN CERTIFICATE-----
-----BEGIN ENCRYPTED PRIVATE KEY-----
-----BEGIN OPENSSH PRIVATE KEY-----
```

### 2. Code Vulnerabilities

#### Python Security (Bandit Patterns)
```python
# Critical Issues
assert user.is_authenticated()        # B101: assert_used
exec(user_input)                     # B102: exec_used
os.chmod('/path/to/file', 0o777)     # B103: set_bad_file_permissions
bind_address = '0.0.0.0'             # B104: hardcoded_bind_all_interfaces
password = 'hardcoded_password'       # B105: hardcoded_password_string

# High Risk Issues
pickle.loads(user_data)              # B301: pickle usage
hashlib.md5(password.encode())       # B303: MD5 usage
eval(user_input)                     # B307: eval usage
```

#### Node.js Security
```javascript
// Critical Issues
eval(userInput);                     // Code injection
const apiKey = 'hardcoded_key';      // Hardcoded secrets
const unsafe = new RegExp('/(x+x+)+y/'); // ReDoS vulnerability
exec('command ' + userInput);        // Shell injection

// Insecure session configuration
app.use(session({
  secret: 'short_secret',
  cookie: { httpOnly: false, secure: false }
}));
```

### 3. SQL Injection Detection
```python
# Dangerous patterns
query = "SELECT * FROM users WHERE id = " + user_id
query = "SELECT * FROM users WHERE name = '%s'" % username
query = f"SELECT * FROM users WHERE id = {user_id}"

# Secure patterns
query = "SELECT * FROM users WHERE id = %s"
cursor.execute(query, (user_id,))
```

### 4. PII Detection Patterns
```regex
# Email addresses
[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}

# Phone numbers
(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}

# Social Security Numbers
\d{3}-\d{2}-\d{4}

# Credit card numbers
\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}
```

## mem0AI Integration Security

### API Key Management

#### Environment Variables Configuration
```bash
# Required: API Key for mem0AI service authentication
MEM0AI_API_KEY=your_secure_api_key_here

# Service Configuration
MEM0AI_HOST=localhost
MEM0AI_PORT=8002
MEM0AI_TIMEOUT=30

# Security Configuration
MEM0AI_USE_TLS=false              # Enable TLS/HTTPS (recommended for production)
MEM0AI_VERIFY_SSL=true            # Verify SSL certificates (recommended)
MEM0AI_AUTH_RETRY_ATTEMPTS=3      # Authentication retry attempts
MEM0AI_AUTH_RETRY_DELAY=1.0       # Delay between retries (seconds)
MEM0AI_MAX_AUTH_FAILURES=5        # Max failures before lockout
MEM0AI_AUTH_LOCKOUT_MINUTES=15    # Lockout duration (minutes)
```

#### API Key Requirements
- **Minimum Length**: 32 characters
- **Entropy**: Cryptographically secure random generation
- **Storage**: Environment variables only, never in code
- **Rotation**: Regular rotation recommended (quarterly)

#### API Key Validation
The system validates API keys for:
- Minimum length requirements
- Common insecure patterns (test, demo, password, etc.)
- Format and character set validity

### Authentication Flow

#### Basic Authentication
```python
from claude_pm.integrations.mem0ai_integration import create_mem0ai_integration

# Create integration with API key authentication
integration = create_mem0ai_integration(
    host="localhost",
    port=8002,
    api_key="your_secure_api_key_here"
)

# Connect with authentication
async with integration:
    if integration.is_authenticated():
        print("Successfully authenticated!")
    else:
        print("Authentication failed!")
```

#### Secure Integration (TLS + Authentication)
```python
from claude_pm.integrations.mem0ai_integration import create_secure_mem0ai_integration

# Create secure integration with TLS and authentication
integration = create_secure_mem0ai_integration(
    host="mem0ai.yourdomain.com",
    port=443,
    api_key="your_secure_api_key_here"
)
```

### Security Event Logging

#### Viewing Security Events
```python
from claude_pm.integrations.security import SecurityEventLogger

# Access security logger from authenticator
logger = integration.authenticator.security_logger

# View recent events
for event in logger.events[-10:]:  # Last 10 events
    print(f"{event.timestamp}: {event.event_type} - {event.service_host}")

# Check recent failures
failures = logger.get_recent_failures("localhost:8002", minutes=60)
print(f"Failures in last hour: {failures}")

# Check lockout status
locked_out = logger.is_host_locked_out("localhost:8002")
print(f"Host locked out: {locked_out}")
```

#### Security Event Types
- `auth_success` - Successful authentication
- `auth_failure` - Authentication failure
- `auth_lockout` - Host locked out due to failures
- `key_rotation` - API key rotation event

## Container Security

### Docker Security Checklist
```dockerfile
# Secure base image
FROM node:18-alpine

# Non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001
USER nextjs

# Minimal attack surface
RUN apk del --no-cache build-dependencies

# Health checks
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

# Secure defaults
ENV NODE_ENV production
EXPOSE 3000
```

### .dockerignore Security
```
# Always exclude
**/node_modules/
**/.git
**/.env*
**/.aws
**/secrets/
**/*.pem
**/*.key
**/coverage
**/npm-debug.log
```

## Dependency Security

### Vulnerability Detection Commands
```bash
# Python
pip-audit --requirement requirements.txt
bandit -r . -f json

# Node.js
npm audit --audit-level=high
yarn audit --level=high

# Docker
trivy image <image_name>
```

### High-Risk Dependency Patterns
```yaml
# Python - Known vulnerable versions
Django==2.0.0  # Multiple XSS vulnerabilities
Flask==0.12.0  # Multiple security issues
Pillow==7.0.0  # Code execution vulnerability

# Node.js - Known vulnerable versions
express@4.16.0  # Multiple vulnerabilities
lodash@4.17.15  # Prototype pollution
axios@0.19.0    # Server-side request forgery
```

## Database Security

### MongoDB Security
```javascript
// Insecure patterns
db.users.find({ $where: userInput }); // NoSQL injection
db.users.find(JSON.parse(userInput)); // JSON injection

// Secure patterns
const ObjectId = require('mongodb').ObjectId;
db.users.find({ _id: ObjectId(userId) });
```

### PostgreSQL Security
```sql
-- Secure configuration
ALTER SYSTEM SET ssl = on;
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 1000;

-- Secure user creation
CREATE USER app_user WITH ENCRYPTED PASSWORD 'secure_password';
GRANT SELECT, INSERT, UPDATE ON specific_table TO app_user;
```

## CI/CD Security

### GitHub Actions Security
```yaml
name: Security Scan

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
      contents: read
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Bandit (Python)
        uses: PyCQA/bandit-action@v1
        with:
          configfile: bandit.yaml
          
      - name: Run ESLint Security
        run: |
          npm install eslint-plugin-security
          npx eslint . --ext .js,.ts
          
      - name: Run Trivy (Docker)
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          format: 'sarif'
          output: 'trivy-results.sarif'
```

## Security Best Practices

### 1. API Key Security
- ✅ **Store in environment variables only**
- ✅ **Use minimum 32 character keys**
- ✅ **Rotate keys regularly (quarterly)**
- ✅ **Use unique keys per environment**
- ❌ **Never commit keys to version control**
- ❌ **Never log full API keys**

### 2. Network Security
- ✅ **Use TLS in production environments**
- ✅ **Verify SSL certificates**
- ✅ **Use secure network connections**
- ✅ **Implement network-level access controls**
- ❌ **Never disable SSL verification in production**

### 3. Error Handling
- ✅ **Log security events for monitoring**
- ✅ **Implement exponential backoff for retries**
- ✅ **Handle authentication failures gracefully**
- ✅ **Monitor for suspicious activity**
- ❌ **Never expose sensitive information in error messages**

### 4. Monitoring and Alerting
- ✅ **Monitor authentication failure rates**
- ✅ **Alert on repeated authentication failures**
- ✅ **Track API key usage patterns**
- ✅ **Monitor for unusual access patterns**

## Compliance Framework

### OWASP Top 10 Coverage
1. **A01:2021 - Broken Access Control**
   - Authorization bypass detection
   - Insecure direct object references
   - Missing function-level access control

2. **A02:2021 - Cryptographic Failures**
   - Weak encryption algorithms
   - Hardcoded secrets
   - Insecure key management

3. **A03:2021 - Injection**
   - SQL injection patterns
   - NoSQL injection
   - Command injection

4. **A04:2021 - Insecure Design**
   - Architecture security patterns
   - Threat modeling validation
   - Secure development practices

5. **A05:2021 - Security Misconfiguration**
   - Default passwords
   - Unnecessary features enabled
   - Insecure default settings

### Regulatory Compliance

**HIPAA Compliance:**
- PHI detection patterns
- Encryption requirements
- Access control validation
- Audit logging requirements

**PCI DSS Compliance:**
- Credit card data detection
- Secure transmission requirements
- Access control requirements
- Vulnerability management

**SOC 2 Compliance:**
- Security controls validation
- Access management
- Change management
- Monitoring requirements

## Agent Integration Patterns

### Project-Specific Security Agent
```python
# .claude-pm/agents/project-specific/security.py
class ProjectSecurityAgent(SecurityAgent):
    def __init__(self):
        super().__init__()
        self.security_posture = "high"  # Project override
        self.custom_patterns = self.load_project_patterns()
        
    def load_project_patterns(self):
        # Load project-specific security patterns
        return {
            "pii_patterns": ["patient_id", "medical_record"],
            "compliance": "HIPAA"
        }
```

### Security-Ops Coordination
```python
def coordinate_with_ops_agent(self, security_findings):
    """Coordinate with ops agent for deployment decisions"""
    if security_findings.has_critical_issues():
        return ops_agent.block_deployment(security_findings)
    
    if security_findings.has_high_issues():
        return ops_agent.require_approval(security_findings)
    
    return ops_agent.proceed_with_warnings(security_findings)
```

## Security Report Format

```json
{
  "scan_id": "sec-scan-2025-01-10-001",
  "timestamp": "2025-01-10T10:30:00Z",
  "project": "claude-multiagent-pm",
  "security_posture": "medium",
  "summary": {
    "total_files": 45,
    "scanned_files": 42,
    "issues_found": 8,
    "critical": 2,
    "high": 3,
    "medium": 2,
    "low": 1
  },
  "findings": [
    {
      "id": "SEC-001",
      "severity": "critical",
      "category": "secrets",
      "title": "Hardcoded API Key Detected",
      "description": "AWS API key found in configuration file",
      "file": "src/config/aws.js",
      "line": 15,
      "column": 20,
      "pattern": "AKIA[0-9A-Z]{16}",
      "recommendation": "Move to environment variables",
      "remediation": {
        "steps": [
          "Remove hardcoded key from file",
          "Add to .env file",
          "Update code to use process.env.AWS_ACCESS_KEY_ID"
        ],
        "references": [
          "https://docs.aws.amazon.com/general/latest/gr/aws-access-keys-best-practices.html"
        ]
      }
    }
  ],
  "veto_decision": "BLOCK",
  "veto_reason": "Critical security issues detected",
  "override_available": false
}
```

## Troubleshooting

### Common Issues

#### Authentication Failures
```bash
# Check API key configuration
echo "API Key configured: ${MEM0AI_API_KEY:+YES}"

# Verify key length
python -c "import os; key=os.getenv('MEM0AI_API_KEY', ''); print(f'Key length: {len(key)}')"
```

#### TLS/SSL Issues
```python
# Test TLS configuration
from claude_pm.integrations.security import SecurityConfig, Mem0AIAuthenticator

config = SecurityConfig(use_tls=True, verify_ssl=True)
auth = Mem0AIAuthenticator(config)
ssl_context = auth.create_ssl_context()

if ssl_context:
    print("✅ SSL context created successfully")
else:
    print("❌ Failed to create SSL context")
```

#### Lockout Issues
```python
# Check if host is locked out
logger = integration.authenticator.security_logger
locked_out = logger.is_host_locked_out("localhost:8002")

if locked_out:
    print("❌ Host is locked out due to authentication failures")
    failures = logger.get_recent_failures("localhost:8002", 15)  # Last 15 minutes
    print(f"Recent failures: {failures}")
```

## Tool Integration

### Static Analysis Tools
```bash
# Python
bandit -r . -f json -o security-report.json
safety check --json --output security-deps.json
semgrep --config=auto --json --output=semgrep-report.json

# Node.js
npx eslint . --ext .js,.ts -f json -o eslint-security.json
npm audit --audit-level=high --json > npm-audit.json
snyk test --json > snyk-report.json

# Docker
trivy image --format json --output trivy-report.json image:tag
hadolint Dockerfile --format json > hadolint-report.json
```

### Dynamic Analysis Integration
```bash
# OWASP ZAP Integration
zap-cli start --port 8080
zap-cli spider http://localhost:3000
zap-cli active-scan http://localhost:3000
zap-cli report -o security-report.html
```

## Deployment Validation

### Pre-Deployment Checklist
```yaml
security_checklist:
  secrets:
    - no_hardcoded_secrets: true
    - environment_variables: true
    - key_rotation_plan: true
  
  authentication:
    - strong_passwords: true
    - mfa_enabled: true
    - session_security: true
  
  encryption:
    - data_at_rest: true
    - data_in_transit: true
    - strong_algorithms: true
  
  dependencies:
    - no_known_vulnerabilities: true
    - up_to_date_versions: true
    - security_patches: true
  
  configuration:
    - secure_defaults: true
    - principle_of_least_privilege: true
    - error_handling: true
```

### Continuous Monitoring
```bash
# Daily security scans
0 2 * * * /usr/local/bin/security_agent --daily-scan

# Weekly dependency updates
0 3 * * 0 /usr/local/bin/security_agent --update-dependencies

# Monthly security review
0 4 1 * * /usr/local/bin/security_agent --monthly-review
```

## Remediation Guidance

### Secrets Management
```bash
# Step 1: Remove secret from code
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch src/config/aws.js' \
  --prune-empty --tag-name-filter cat -- --all

# Step 2: Add to environment
echo "AWS_ACCESS_KEY_ID=your_key_here" >> .env
echo ".env" >> .gitignore

# Step 3: Update code
const awsConfig = {
  accessKeyId: process.env.AWS_ACCESS_KEY_ID,
  secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY
};
```

### Dependency Updates
```bash
# Python
pip install --upgrade package-name==secure-version

# Node.js
npm update package-name
npm audit fix

# Docker
docker pull image:latest-secure
```

## References

### Security Documentation
- **OWASP Web Security Testing Guide**: https://owasp.org/www-project-web-security-testing-guide/
- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **NIST Cybersecurity Framework**: https://www.nist.gov/cyberframework
- **CIS Controls**: https://www.cisecurity.org/controls/

### Tool Documentation
- **Bandit**: https://bandit.readthedocs.io/
- **ESLint Security**: https://github.com/eslint-community/eslint-plugin-security
- **Trivy**: https://trivy.dev/
- **Semgrep**: https://semgrep.dev/

### Best Practices
- **Node.js Security Best Practices**: https://github.com/goldbergyoni/nodebestpractices#security
- **Docker Security**: https://docs.docker.com/engine/security/
- **AWS Security Best Practices**: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/

---

**Framework Version**: 4.5.1  
**Last Updated**: 2025-07-11  
**Security Agent Version**: 1.0.0  
**Authority Level**: Pre-Push Veto with Override