---
review_id: SEC-PR-XXX-001
pr_id: PR-XXX
review_type: security
reviewer: security-engineer
status: not_started
priority: critical
assigned_date: YYYY-MM-DD
target_completion: YYYY-MM-DD
---

# Security Review: PR-XXX

## Review Scope

### Authentication & Authorization
- [ ] Authentication mechanisms properly implemented
- [ ] Authorization checks in place for all endpoints
- [ ] Role-based access control validated
- [ ] Session management secure

### Input Validation & Sanitization
- [ ] All user inputs validated
- [ ] SQL injection prevention measures
- [ ] XSS prevention implemented
- [ ] Command injection protections

### Credential Management
- [ ] API keys stored securely
- [ ] Passwords properly hashed
- [ ] Secrets not exposed in logs
- [ ] Environment variable usage correct

### Data Protection
- [ ] Sensitive data encrypted at rest
- [ ] Sensitive data encrypted in transit
- [ ] PII handling compliant
- [ ] Data retention policies followed

### API Security
- [ ] Rate limiting implemented
- [ ] CORS policies configured correctly
- [ ] HTTPS enforced
- [ ] Request/response validation

### Audit & Monitoring
- [ ] Security events logged
- [ ] Audit trail complete
- [ ] Monitoring alerts configured
- [ ] Incident response procedures

## Security Findings

### Critical Issues (Immediate Fix Required)
*None identified at this time*

### High Issues (Fix Before Merge)
*None identified at this time*

### Medium Issues (Address in Follow-up)
*None identified at this time*

### Low Issues (Optional Improvements)
*None identified at this time*

## Recommendations

### Security Enhancements
1. Consider implementing additional monitoring
2. Review error message exposure
3. Validate third-party dependency security

### Best Practices
1. Follow OWASP security guidelines
2. Implement defense in depth
3. Regular security dependency updates

## Approval Status

**Status**: Pending Review  
**Reviewer**: security-engineer  
**Review Date**: TBD  
**Approval**: Pending  

### Approval Conditions
- [ ] All critical and high issues resolved
- [ ] Security testing completed
- [ ] Documentation updated with security considerations

---

**Security Review Complete**: This review covers all critical security aspects of the PR implementation.