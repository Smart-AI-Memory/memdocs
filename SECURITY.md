# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 2.x.x   | :white_check_mark: |
| 1.x.x   | :x:                |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: **security@deepstudyai.com**

You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

### What to Include

Please include the following information in your report:

- **Type of vulnerability** (e.g., XSS, SQL injection, path traversal)
- **Full paths of source file(s)** related to the manifestation of the issue
- **Location of the affected source code** (tag/branch/commit or direct URL)
- **Step-by-step instructions** to reproduce the issue
- **Proof-of-concept or exploit code** (if possible)
- **Impact of the issue**, including how an attacker might exploit it

This information will help us triage your report more quickly.

## Security Best Practices

When using MemDocs, please follow these security best practices:

### API Keys

- **Never commit** `.env` files to version control
- **Use environment variables** for API keys
- **Rotate keys** regularly
- **Use separate keys** for development, staging, and production
- **Limit key permissions** to only what's needed

### Configuration

- **Validate all inputs** from configuration files
- **Use `.memdocs.yml.example`** as a template, not `.memdocs.yml` directly
- **Enable privacy mode** if processing sensitive data (PHI/PII)
- **Review exclude patterns** to ensure sensitive files aren't processed

### Dependencies

- **Keep dependencies updated** (use `pip-audit` to check for CVEs)
- **Pin dependency versions** in production
- **Review security advisories** for dependencies

### File Operations

- **Validate file paths** to prevent path traversal
- **Limit file sizes** to prevent DoS
- **Sanitize git commit messages** and user input
- **Don't process untrusted repositories** without review

## Disclosure Policy

When we receive a security bug report, we will:

1. **Confirm the problem** and determine affected versions
2. **Audit code** to find any similar problems
3. **Prepare fixes** for all supported versions
4. **Release patched versions** as soon as possible
5. **Publish security advisory** on GitHub

We aim to disclose vulnerabilities within 90 days of receiving the report, or sooner if possible.

## Comments on this Policy

If you have suggestions on how this policy could be improved, please submit a pull request or email security@deepstudyai.com.

## Known Security Considerations

### Claude API Prompts

- MemDocs sends code and commit messages to the Claude API
- **Do not use** with proprietary or confidential code unless you have appropriate agreements with Anthropic
- **Review the Privacy Policy** at https://www.anthropic.com/privacy

### Local Embeddings

- Local embeddings (sentence-transformers) process code locally
- No data is sent to external services when using local embeddings
- **Consider using local embeddings** for sensitive codebases

### Git Repository Access

- MemDocs reads git history and file contents
- **Ensure repositories** are from trusted sources
- **Review git hooks** in repositories before processing

## Security Contact

- **Email**: security@deepstudyai.com
- **PGP Key**: (Coming soon)

Thank you for helping keep MemDocs and our users safe!
