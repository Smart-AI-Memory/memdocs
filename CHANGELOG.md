# Changelog

All notable changes to MemDocs will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

### [2.1.0] - Q1 2026 (Planned)
- Multi-language support (Go, Rust, Java, C++)
- VSCode extension
- JetBrains plugin
- Automatic PR summary generation
- Improved Empathy sync wizards

### [2.2.0] - Q2 2026 (Planned)
- Optional semantic search with embeddings
- Memory compression (summarize old memories)
- Team analytics dashboard
- Enhanced privacy features (HIPAA/GDPR compliance)

### [3.0.0] - Q3 2026 (Planned)
- MemDocs Cloud (optional hosted version)
- Enterprise features (SSO, audit logs, access control)
- Advanced Empathy integration (Level 5 predictions)
- Real-time collaboration features

---

## Support

For questions, issues, or feature requests:
- **GitHub Issues**: https://github.com/Deep-Study-AI/memdocs/issues
- **Documentation**: https://docs.deepstudyai.com/memdocs
- **Discord**: https://discord.gg/deepstudyai
- **Email**: patrick.roebuck@pm.me
