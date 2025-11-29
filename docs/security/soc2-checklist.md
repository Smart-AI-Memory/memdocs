# SOC 2 Type II Alignment Checklist

## Overview

This document maps MemDocs security controls to SOC 2 Trust Service Criteria. MemDocs is designed to support your organization's SOC 2 compliance by minimizing third-party risk through git-native, local-first architecture.

## Why MemDocs Simplifies SOC 2 Compliance

| Traditional AI Memory | MemDocs |
|----------------------|---------|
| New vendor to assess | Uses existing git infrastructure |
| Separate access controls | Inherits git permissions |
| Additional audit logs | Git history IS the audit log |
| Data residency concerns | Data never leaves your repos |
| API key sprawl | Single optional API key |

## Trust Service Criteria Mapping

### CC1: Control Environment

| Criteria | MemDocs Control | Evidence |
|----------|-----------------|----------|
| CC1.1 - Demonstrates commitment to integrity | Apache 2.0 open source license | LICENSE file |
| CC1.2 - Board oversight | N/A (customer responsibility) | - |
| CC1.3 - Organizational structure | Clear module separation | CONTRIBUTING.md |
| CC1.4 - Competent personnel | Type hints, comprehensive tests | 78%+ coverage |
| CC1.5 - Accountability | Git commit attribution | Git history |

### CC2: Communication and Information

| Criteria | MemDocs Control | Evidence |
|----------|-----------------|----------|
| CC2.1 - Information quality | Structured schemas (Pydantic) | schemas.py |
| CC2.2 - Internal communication | Comprehensive documentation | docs/ directory |
| CC2.3 - External communication | SECURITY.md, README.md | Public docs |

### CC3: Risk Assessment

| Criteria | MemDocs Control | Evidence |
|----------|-----------------|----------|
| CC3.1 - Risk objectives | Security-first architecture | security-architecture.md |
| CC3.2 - Risk identification | Threat modeling in design | guard.py, security.py |
| CC3.3 - Fraud risk | Input validation, rate limiting | InputValidator class |
| CC3.4 - Change impact | Git-based change tracking | Git history |

### CC4: Monitoring Activities

| Criteria | MemDocs Control | Evidence |
|----------|-----------------|----------|
| CC4.1 - Ongoing monitoring | CI/CD pipelines | .github/workflows/ |
| CC4.2 - Deficiency evaluation | GitHub Issues, PRs | Public tracker |

### CC5: Control Activities

| Criteria | MemDocs Control | Evidence |
|----------|-----------------|----------|
| CC5.1 - Control selection | Defense in depth | security-architecture.md |
| CC5.2 - Technology controls | Automated testing, type checking | pyproject.toml |
| CC5.3 - Policy deployment | Pre-commit hooks | .pre-commit-config.yaml |

### CC6: Logical and Physical Access

| Criteria | MemDocs Control | Evidence |
|----------|-----------------|----------|
| CC6.1 - Access provisioning | Git permissions (inherited) | Repository settings |
| CC6.2 - Access removal | Git permissions (inherited) | Repository settings |
| CC6.3 - Access review | Git audit log | `git log` |
| CC6.4 - Access restrictions | PathValidator, rate limiting | security.py |
| CC6.5 - Authentication | API key validation | InputValidator |
| CC6.6 - Access credentials | Environment variables only | No stored secrets |
| CC6.7 - Transmission protection | TLS 1.3 for API calls | anthropic library |
| CC6.8 - Malicious software | No executable code stored | .memdocs/ contains only data |

### CC7: System Operations

| Criteria | MemDocs Control | Evidence |
|----------|-----------------|----------|
| CC7.1 - Infrastructure detection | N/A (runs locally) | - |
| CC7.2 - Security monitoring | Audit logs for redactions | guard.py |
| CC7.3 - Security evaluation | Dependency scanning | pip-audit in CI |
| CC7.4 - Incident response | SECURITY.md process | SECURITY.md |
| CC7.5 - Recovery | Git-native (inherent backup) | .memdocs/ in git |

### CC8: Change Management

| Criteria | MemDocs Control | Evidence |
|----------|-----------------|----------|
| CC8.1 - Change authorization | PR review process | CONTRIBUTING.md |

### CC9: Risk Mitigation

| Criteria | MemDocs Control | Evidence |
|----------|-----------------|----------|
| CC9.1 - Vendor management | Minimal dependencies | pyproject.toml |
| CC9.2 - Vendor risk assessment | Open source, auditable | GitHub repository |

## Additional Security Controls

### A1: Availability

| Criteria | MemDocs Control | Evidence |
|----------|-----------------|----------|
| A1.1 - Capacity management | Local processing, no cloud limits | - |
| A1.2 - Environmental controls | N/A (runs on customer infra) | - |
| A1.3 - Recovery procedures | Git clone restores everything | Git-native |

### C1: Confidentiality

| Criteria | MemDocs Control | Evidence |
|----------|-----------------|----------|
| C1.1 - Confidential information | PHI/PII detection & redaction | guard.py |
| C1.2 - Confidential disposal | Git-native (customer controls) | - |

### PI1: Processing Integrity

| Criteria | MemDocs Control | Evidence |
|----------|-----------------|----------|
| PI1.1 - Processing accuracy | Schema validation (Pydantic) | schemas.py |
| PI1.2 - Processing completeness | Structured output formats | JSON, YAML, MD |
| PI1.3 - Processing timeliness | Rate limiting prevents overload | RateLimiter |

### P1: Privacy

| Criteria | MemDocs Control | Evidence |
|----------|-----------------|----------|
| P1.1 - Privacy notice | N/A (no data collection) | - |
| P2.1 - Privacy choice | PHI mode configurable | .memdocs.yml |
| P3.1 - Privacy collection | Minimal data, local only | - |
| P4.1 - Privacy use | No telemetry or analytics | Code audit |
| P5.1 - Privacy access | Git permissions | - |
| P6.1 - Privacy disclosure | Open source, auditable | - |
| P7.1 - Privacy quality | Redaction audit logs | guard.py |
| P8.1 - Privacy monitoring | Audit trail in JSONL | audit.log |

## Auditor FAQ

### Q: Does MemDocs store customer data in the cloud?
**A:** No. All data is stored in the `.memdocs/` directory within the customer's git repository. The only external communication is optional API calls to Claude (Anthropic) for summarization, which can be disabled for air-gapped environments.

### Q: How is access controlled?
**A:** MemDocs inherits the access controls of the git repository it operates in. No additional user management, authentication systems, or access credentials are introduced.

### Q: Where are audit logs stored?
**A:**
1. **Git history**: All changes to `.memdocs/` are tracked in git commits
2. **Redaction logs**: PHI/PII redaction events are logged to `audit.log` in JSONL format
3. **No external logging**: No data is sent to external logging services

### Q: How is sensitive data protected?
**A:**
1. **Detection**: Guard module scans for 7+ PII/PHI patterns
2. **Redaction**: Automatic replacement with `[REDACTED:TYPE]`
3. **Audit**: All redactions logged with timestamp and context
4. **Validation**: Content can be re-scanned before commit

### Q: What third-party dependencies exist?
**A:** See `pyproject.toml` for complete list. Key dependencies:
- `anthropic`: Claude API client (optional)
- `sentence-transformers`: Local embeddings (no API)
- `faiss-cpu`: Local vector search (no API)
- All dependencies are open source and auditable

### Q: How are vulnerabilities managed?
**A:**
1. `pip-audit` runs in CI to detect CVEs
2. GitHub Dependabot monitors dependencies
3. SECURITY.md provides disclosure process
4. 48-hour response commitment

## Compliance Evidence Package

For auditors, the following evidence is available:

| Document | Location | Purpose |
|----------|----------|---------|
| Security Architecture | docs/security/security-architecture.md | Technical controls |
| HIPAA Readiness | docs/security/hipaa-readiness.md | Healthcare compliance |
| Data Residency | docs/security/data-residency.md | Data location |
| Security Policy | SECURITY.md | Vulnerability handling |
| Code of Conduct | CODE_OF_CONDUCT.md | Community standards |
| Contribution Guide | CONTRIBUTING.md | Change management |
| Test Coverage | CI reports | Quality assurance |
| Dependency Audit | pip-audit reports | Supply chain security |

## Contact

For SOC 2 audit inquiries:
- **Email**: patrick.roebuck@pm.me
- **Enterprise Support**: Available for licensed customers
