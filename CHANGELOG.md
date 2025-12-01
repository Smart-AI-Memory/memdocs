# Changelog

All notable changes to MemDocs will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.3] - 2025-12-01

### Changed
- Upgraded Codecov action to v5 with verbose output for better CI integration
- Updated MCP dependencies for compatibility (pydantic, httpx, uvicorn, pydantic-settings, python-multipart)

---

## [2.1.2] - 2025-11-29

### Changed
- **Rebranding**: Updated all documentation and links from Deep Study AI to Smart AI Memory
- Updated GitHub repository URLs to Smart-AI-Memory organization
- Updated copyright in LICENSE to Smart AI Memory
- Updated website references to smartaimemory.com

---

## [2.1.1] - 2025-11-29

### Added
- **Enterprise Security Documentation**: SOC 2 Type II compliance checklist, HIPAA readiness guide, data residency documentation
- **Air-Gapped Deployment Guide**: Complete offline installation instructions for secure environments
- **Comprehensive API Reference**: Full documentation for all public modules and interfaces
- **New Unit Tests**: Test coverage increased from 78% to 86%
  - `doctor_cmd.py` coverage: 18% → 100%
  - `setup_hooks_cmd.py` coverage: 19% → 100%
  - `update_config_cmd.py` coverage: 17% → 96%

### Changed
- **Focused Core Architecture**: Removed wizards module to concentrate on core competencies (git-native memory, cross-conversation LLM memory, enterprise security)
- Wizards now maintained in separate domain-specific archives (healthcare, software development, general business)

### Fixed
- CI formatting issues with Black code formatter
- Test assertion handling for terminal line-wrapping differences

---

## [2.0.0] - 2025-11-07

### Added
- **Rebranding**: DocInt → MemDocs (new name, same powerful memory)
- Comprehensive README with examples and use cases
- Empathy Framework integration (Level 4 Anticipatory Intelligence)
- Model Context Protocol (MCP) server support
- Python API for programmatic access
- Example scripts demonstrating all features
- Improved configuration with `.memdocs.yml`
- Token-efficient summarization (no embeddings required)
- Git-native storage architecture

### Changed
- Package name: `docint` → `memdocs`
- Directory structure: `.docint/` → `.memdocs/`
- CLI command: `docint` → `memdocs`
- Updated to Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)
- Improved documentation and examples
- Modernized pyproject.toml configuration

### Improved
- Better scoping policies (file/module/repo levels)
- Auto-escalation for important changes
- Enhanced privacy controls (PHI/PII optional)
- Faster local search (no API calls)
- Cleaner API design

### Migration from DocInt 1.x
If you're upgrading from DocInt 1.x:

1. **Rename directory**: `.docint/` → `.memdocs/`
2. **Update config**: `.docint.yml` → `.memdocs.yml`
3. **Update CLI commands**: `docint` → `memdocs`
4. **Update Python imports**: `from docint import *` → `from memdocs import *`
5. **Re-install package**: `pip uninstall docint && pip install memdocs`

Migration script:
```bash
# Automated migration (run in project root)
mv .docint .memdocs 2>/dev/null || true
mv .docint.yml .memdocs.yml 2>/dev/null || true
sed -i '' 's/docint/memdocs/g' .memdocs.yml
pip uninstall docint -y
pip install memdocs
```

## [1.0.0] - 2025-10-23 (DocInt)

### Added
- Initial release of DocInt
- Git-native memory storage
- Claude API integration
- File/module/repo scoping
- Symbol extraction with tree-sitter
- CLI tool
- Python API
- Basic privacy guards

---

## Upcoming Releases

### [2.2.0] - Q1 2026 (Planned)
- Multi-language support (Go, Rust, Java, C++)
- VSCode extension
- JetBrains plugin
- Automatic PR summary generation

### [2.3.0] - Q2 2026 (Planned)
- Optional semantic search with embeddings
- Memory compression (summarize old memories)
- Team analytics dashboard

### [3.0.0] - Q3 2026 (Planned)
- MemDocs Cloud (optional hosted version)
- Enterprise features (SSO, audit logs, access control)
- Real-time collaboration features

---

## Support

For questions, issues, or feature requests:
- **GitHub Issues**: https://github.com/Smart-AI-Memory/memdocs/issues
- **Email**: patrick.roebuck@pm.me
