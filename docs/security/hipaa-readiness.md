# HIPAA Readiness Guide

## Overview

MemDocs is designed to support HIPAA-compliant workflows through its git-native, local-first architecture and built-in PHI detection and redaction capabilities. This document outlines how MemDocs aligns with HIPAA requirements.

## Important Disclaimer

> **MemDocs is a tool, not a covered entity.** HIPAA compliance is the responsibility of the covered entity (healthcare organization) using the tool. This document describes MemDocs capabilities that support HIPAA compliance when properly configured and used within a compliant environment.

## Why MemDocs for Healthcare

| Challenge | Traditional AI Tools | MemDocs Solution |
|-----------|---------------------|------------------|
| PHI in cloud | Data sent to third parties | Local-first, git-native |
| BAA requirements | Complex vendor agreements | Minimal third-party involvement |
| Audit trails | Separate audit systems | Git history + redaction logs |
| Access control | New IAM to manage | Inherits git permissions |
| Data retention | Vendor-controlled | Customer-controlled in git |

## HIPAA Safeguards Mapping

### Administrative Safeguards (45 CFR 164.308)

| Requirement | MemDocs Support | Configuration |
|-------------|-----------------|---------------|
| **Security Management** | Defense-in-depth architecture | See security-architecture.md |
| **Assigned Security** | N/A (customer responsibility) | - |
| **Workforce Security** | Git-based access control | Repository permissions |
| **Information Access** | PathValidator restricts paths | Automatic |
| **Security Awareness** | Documentation & training materials | docs/ directory |
| **Security Incidents** | SECURITY.md process | 48-hour response |
| **Contingency Plan** | Git-native backup/recovery | `git clone` restores all |
| **Evaluation** | CI/CD testing, audits | GitHub Actions |

### Physical Safeguards (45 CFR 164.310)

| Requirement | MemDocs Support | Notes |
|-------------|-----------------|-------|
| **Facility Access** | N/A (runs on customer infra) | Customer responsibility |
| **Workstation Use** | N/A | Customer responsibility |
| **Workstation Security** | N/A | Customer responsibility |
| **Device Controls** | Git-native, no external devices | Data stays in repo |

### Technical Safeguards (45 CFR 164.312)

| Requirement | MemDocs Support | Implementation |
|-------------|-----------------|----------------|
| **Access Control** | Git permissions | Repository ACLs |
| **Unique User ID** | Git commit attribution | `git log --author` |
| **Emergency Access** | N/A (customer infra) | Customer responsibility |
| **Automatic Logoff** | N/A (CLI tool) | Customer responsibility |
| **Encryption** | TLS 1.3 for API, repo encryption | Standard git security |
| **Audit Controls** | Git history + audit.log | Automatic |
| **Integrity Controls** | Schema validation, checksums | Pydantic + git |
| **Authentication** | API key validation | InputValidator |
| **Transmission Security** | TLS 1.3 | anthropic library |

## PHI Protection Features

### Automatic PHI Detection

MemDocs Guard module detects the following PHI patterns:

| PHI Type | Detection Pattern | HIPAA Identifier |
|----------|-------------------|------------------|
| Email | RFC 5322 format | Electronic mail addresses |
| Phone | US formats with variants | Telephone numbers |
| SSN | XXX-XX-XXXX | Social Security numbers |
| MRN | MRN: XXXXXX | Medical record numbers |
| Credit Card | 16-digit patterns | Account numbers |
| IP Address | IPv4 dotted notation | Device identifiers |

### Configuration for Healthcare

```yaml
# .memdocs.yml - HIPAA-compliant configuration
version: 1

privacy:
  phi_mode: "strict"           # Enable aggressive PHI detection
  scrub:
    - email
    - phone
    - ssn
    - mrn
  audit_redactions: true       # Log all redactions for compliance

# Exclude files that may contain PHI
exclude:
  - "**/*.csv"                 # Patient data exports
  - "**/*.xlsx"                # Spreadsheets
  - "**/patient*"              # Patient-related files
  - "**/medical*"              # Medical records
  - "**/*.hl7"                 # HL7 messages
  - "**/*.fhir"                # FHIR resources
```

### Redaction Audit Trail

All PHI detections and redactions are logged:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "event": "redaction_applied",
  "doc_id": "commit-abc123",
  "redactions": [
    {
      "type": "mrn",
      "location": "char:1250-1262",
      "context": "Patient MRN: [REDACTED]..."
    },
    {
      "type": "phone",
      "location": "char:1890-1904",
      "context": "Contact: [REDACTED]..."
    }
  ]
}
```

### Validation Before Commit

```python
from memdocs.guard import Guard
from memdocs.schemas import PHIMode

# Create guard with strict PHI detection
guard = Guard(
    mode=PHIMode.STRICT,
    scrub_types=["email", "phone", "ssn", "mrn"],
    audit_path=Path(".memdocs/audit.log")
)

# Validate content before committing
is_valid, errors = guard.validate_content(document_text)
if not is_valid:
    print("PHI detected! Cannot commit:")
    for error in errors:
        print(f"  - {error}")
```

## Minimum Necessary Standard

MemDocs supports the HIPAA Minimum Necessary standard:

1. **Code Context Only**: Summarization sends code structure, not data
2. **Configurable Scope**: Review specific files, not entire repos
3. **Exclude Patterns**: Skip directories containing sensitive data
4. **Local Embeddings**: Search indexes built locally, no data sent

## Business Associate Considerations

### When BAA is NOT Required

MemDocs itself does not require a BAA when:
- Using local embeddings only (no API calls)
- Claude API is not used for PHI-containing code
- Running in air-gapped mode

### When BAA MAY be Required

A BAA with Anthropic may be needed if:
- Sending code that references PHI to Claude API
- Using Claude API in production healthcare workflows

**Recommendation**: Contact Anthropic directly for BAA requirements if using Claude API with healthcare codebases.

## Air-Gapped Healthcare Deployment

For maximum PHI protection, MemDocs supports air-gapped operation:

```bash
# Install without network (pre-downloaded wheels)
pip install --no-index --find-links=/path/to/wheels memdocs

# Use local embeddings only (no API)
memdocs init
memdocs review --path src/ --local-only

# Query without network
memdocs query "patient intake flow"  # Uses local FAISS
```

See [air-gapped-install.md](../enterprise/air-gapped-install.md) for complete instructions.

## Audit Checklist for Healthcare

### Pre-Deployment

- [ ] Configure `phi_mode: "strict"` in .memdocs.yml
- [ ] Enable `audit_redactions: true`
- [ ] Configure exclude patterns for PHI-containing directories
- [ ] Review and approve all scrub types
- [ ] Test PHI detection with sample data
- [ ] Verify audit log location and retention

### Ongoing Monitoring

- [ ] Review redaction audit logs weekly
- [ ] Validate no PHI in .memdocs/ directory
- [ ] Monitor git commits for .memdocs/ changes
- [ ] Review API call logs (if using Claude)
- [ ] Update exclude patterns as codebase evolves

### Incident Response

- [ ] SECURITY.md process for vulnerability reports
- [ ] Redaction failure escalation procedure
- [ ] PHI exposure notification process (customer responsibility)

## Sample HIPAA Risk Assessment Entry

| Asset | MemDocs AI Memory |
|-------|-------------------|
| Description | Git-native documentation and memory for AI assistants |
| Data Types | Code summaries, embeddings, search indexes |
| PHI Exposure | Minimal - PHI detection and redaction enabled |
| Location | Customer git repositories only |
| Access | Git repository permissions |
| Encryption | Repository-level (git-crypt compatible) |
| Audit | Git history + audit.log |
| Risk Level | Low (when properly configured) |
| Mitigations | PHI mode strict, exclude patterns, local embeddings |

## Contact

For HIPAA compliance questions:
- **Email**: patrick.roebuck@pm.me
- **Enterprise Support**: Available for licensed healthcare customers
