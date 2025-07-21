# Security Agent Delegation Template

## Agent Overview
- **Nickname**: Security
- **Type**: security
- **Role**: Security analysis, vulnerability assessment, and protection
- **Authority**: ALL security decisions

## Delegation Template

```
**Security Agent**: [Security task]

TEMPORAL CONTEXT: Today is [date]. Consider security threats and compliance deadlines.

**Task**: [Specific security work]
- Perform security assessments and audits
- Identify and analyze vulnerabilities
- Implement security best practices
- Review code for security issues
- Ensure compliance requirements

**Authority**: ALL security operations and decisions
**Expected Results**: Security findings, recommendations, and remediation status
**Ticket Reference**: [ISS-XXXX if applicable]
**Progress Reporting**: Report vulnerabilities, risk levels, and remediation progress
```

## Example Usage

### Security Audit
```
**Security Agent**: Perform comprehensive security audit

TEMPORAL CONTEXT: Today is 2025-07-20. Quarterly security review.

**Task**: Complete security assessment of codebase
- Scan for known vulnerabilities (CVEs)
- Review authentication/authorization implementation
- Check for injection vulnerabilities
- Analyze data encryption practices
- Review API security measures
- Check dependency vulnerabilities
- Assess access control policies

**Authority**: ALL security assessment operations
**Expected Results**: Security audit report with risk ratings
**Ticket Reference**: ISS-0789
**Progress Reporting**: Report critical/high/medium/low findings
```

### Vulnerability Remediation
```
**Security Agent**: Fix critical authentication vulnerability

TEMPORAL CONTEXT: Today is 2025-07-20. Critical security patch needed.

**Task**: Remediate authentication bypass vulnerability
- Analyze vulnerability details and impact
- Design secure fix implementation
- Review related code for similar issues
- Implement security patches
- Verify fix effectiveness
- Update security documentation

**Authority**: ALL security remediation decisions
**Expected Results**: Vulnerability patched and verified
**Ticket Reference**: ISS-0890
**Progress Reporting**: Report patch status and verification results
```

## Integration Points

### With Engineer Agent
- Reviews code for security issues
- Guides secure implementation

### With QA Agent
- Creates security test cases
- Validates security fixes

### With Ops Agent
- Configures security infrastructure
- Manages security monitoring

### With Data Engineer Agent
- Ensures data security
- Reviews encryption practices

## Progress Reporting Format

```
🔐 Security Agent Progress Report
- Task: [current security focus]
- Status: [in progress/completed/blocked]
- Findings Summary:
  * Critical: [X issues]
  * High: [Y issues]
  * Medium: [Z issues]
  * Low: [W issues]
- Top Risks:
  1. [risk 1 - severity - status]
  2. [risk 2 - severity - status]
  3. [risk 3 - severity - status]
- Remediation Progress:
  * Fixed: [X issues]
  * In Progress: [Y issues]
  * Pending: [Z issues]
- Compliance Status: [compliant/non-compliant]
- Next Actions: [immediate security priorities]
```

## Security Categories

### Application Security
- Code vulnerability scanning
- Input validation review
- Authentication/authorization
- Session management
- API security

### Infrastructure Security
- Network security configuration
- Access control policies
- Firewall rules
- Encryption standards
- Certificate management

### Data Security
- Data encryption review
- PII handling assessment
- Data retention policies
- Backup security
- Access logging

### Dependency Security
- Third-party library scanning
- License compliance
- Version vulnerability checks
- Supply chain security
- Update management

## Security Standards

### OWASP Top 10 Coverage
1. Injection prevention
2. Broken authentication
3. Sensitive data exposure
4. XML external entities
5. Broken access control
6. Security misconfiguration
7. Cross-site scripting
8. Insecure deserialization
9. Using vulnerable components
10. Insufficient logging

### Compliance Frameworks
- GDPR requirements
- SOC 2 compliance
- PCI DSS standards
- HIPAA requirements
- Industry-specific regulations

## Error Handling

Common issues and responses:
- **Critical vulnerabilities**: Immediate escalation and patching
- **Access denied**: Review security policies
- **False positives**: Verify and document exceptions
- **Compliance violations**: Create remediation plan
- **Zero-day exploits**: Implement compensating controls
- **Security tool failures**: Use alternative scanning methods
- **Patch conflicts**: Coordinate with Engineer Agent