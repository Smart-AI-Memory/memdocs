# Future Plans: Auto-Loading Memory & Book Project

Comprehensive planning document for two major initiatives:
1. Auto-loading MemDocs memories when projects load
2. Creating a book about MemDocs and Empathy Framework

---

## Part 1: Auto-Loading MemDocs Memories

### Vision

**Problem:** AI assistants (Claude Code, Cursor, etc.) don't automatically load MemDocs memory when opening a project, forcing users to manually export or reference context.

**Goal:** Seamlessly integrate MemDocs memory into AI assistant workflows so that when a developer opens a project with MemDocs, the AI automatically has full context.

### Implementation Strategy

#### Option A: IDE Extensions (Recommended)

Create native extensions for popular IDEs that automatically load `.memdocs/` context.

**VS Code Extension (`memdocs-vscode`)**

```typescript
// Extension activates when .memdocs.yml is detected
export function activate(context: vscode.ExtensionContext) {
  // Watch for .memdocs/ changes
  const watcher = vscode.workspace.createFileSystemWatcher('**/.memdocs/**');

  // Auto-load context when workspace opens
  if (hasMemDocs()) {
    loadMemDocsContext();
  }

  // Provide context to AI assistant
  vscode.workspace.onDidOpenTextDocument(async (doc) => {
    const context = await getMemDocsContext(doc.uri);
    injectContextToAI(context);
  });
}

async function loadMemDocsContext() {
  // Read .memdocs/cursor or generate on-the-fly
  const cursor = await fs.readFile('.memdocs/cursor', 'utf8');

  // Inject into VS Code AI context
  vscode.workspace.updateWorkspaceFolders(0, 0, {
    uri: vscode.Uri.file('.memdocs'),
    name: 'AI Memory',
    index: 0
  });
}
```

**Features:**
- ✅ Auto-detect `.memdocs.yml` in workspace
- ✅ Load context on workspace open
- ✅ Watch for memory updates (live reload)
- ✅ Provide file-specific context based on active editor
- ✅ Status bar indicator showing memory status
- ✅ Commands: Refresh Memory, View Memory Stats

**Cursor Extension (`memdocs-cursor`)**

Similar to VS Code but integrates with Cursor's AI panel:

```typescript
// Cursor-specific API integration
import { CursorAI } from '@cursor/api';

export async function injectMemDocs() {
  const memory = await loadMemDocsMemory();

  CursorAI.setContext({
    type: 'project-memory',
    source: 'memdocs',
    content: memory,
    priority: 'high'
  });
}
```

**Implementation Plan:**

1. **Phase 1: VS Code Extension (4 weeks)**
   - Week 1: Extension scaffold, manifest, activation
   - Week 2: File watcher, context loading
   - Week 3: AI context injection, commands
   - Week 4: Testing, marketplace submission

2. **Phase 2: Cursor Extension (2 weeks)**
   - Week 1: Adapt VS Code extension for Cursor
   - Week 2: Cursor-specific features, testing

3. **Phase 3: JetBrains Plugin (4 weeks)**
   - Similar approach for IntelliJ, PyCharm, WebStorm

**Marketplace Listing:**
- **Name:** MemDocs - AI Memory Manager
- **Description:** Persistent memory for AI assistants
- **Category:** AI Tools, Productivity
- **Keywords:** AI, documentation, context, memory

---

#### Option B: MCP Server Integration (Current Best Approach)

Leverage Model Context Protocol (MCP) to serve MemDocs memory to any MCP-compatible AI assistant.

**Why MCP?**
- ✅ Standard protocol supported by Claude Desktop, Cursor, Continue.dev
- ✅ Real-time updates without file watching
- ✅ Query-based context (AI requests what it needs)
- ✅ Works across all IDEs/tools
- ✅ Already implemented in `memdocs/mcp_server.py`!

**Current Implementation:**

```python
# memdocs/mcp_server.py (already exists!)
class MemDocsMCPServer:
    """MCP server for serving MemDocs memory."""

    def __init__(self, docs_dir: Path, memory_dir: Path):
        self.docs_dir = docs_dir
        self.memory_dir = memory_dir

    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        if request.tool == "search_memory":
            return await self.search(request.params["query"])
        elif request.tool == "get_symbols":
            return await self.get_symbols(request.params["file"])
        # ... more tools
```

**Enhancement Plan:**

1. **Auto-Start MCP Server (Week 1)**
   ```yaml
   # Add to Claude Desktop config automatically
   # ~/.config/claude/config.json
   {
     "mcpServers": {
       "memdocs": {
         "command": "memdocs",
         "args": ["serve", "--mcp"],
         "env": {
           "MEMDOCS_DIR": "${workspaceFolder}/.memdocs"
         }
       }
     }
   }
   ```

2. **Auto-Detection Hook (Week 2)**
   ```bash
   # Add to shell startup (.bashrc, .zshrc)
   function cd() {
     builtin cd "$@"
     if [ -f ".memdocs.yml" ]; then
       memdocs serve --mcp --daemon &
     fi
   }
   ```

3. **Project Init Hook (Week 3)**
   ```python
   # When running `memdocs init`, also configure MCP
   def init_mcp_integration():
       """Configure MCP server for this project."""
       # Add to Claude config
       # Add to VS Code settings
       # Add to shell hook
   ```

4. **VS Code Task Runner (Week 4)**
   ```json
   // .vscode/tasks.json (auto-generated by memdocs init)
   {
     "version": "2.0.0",
     "tasks": [
       {
         "label": "MemDocs MCP Server",
         "type": "shell",
         "command": "memdocs serve --mcp",
         "isBackground": true,
         "runOptions": {
           "runOn": "folderOpen"
         }
       }
     ]
   }
   ```

**Benefits:**
- ✅ Works immediately with Claude Desktop
- ✅ No extension needed for each IDE
- ✅ Real-time memory serving
- ✅ Query-based (efficient)

---

#### Option C: Git Hooks + Auto-Export

Simplest approach: automatically export context on git operations.

**Implementation:**

```bash
# .git/hooks/post-checkout (auto-installed by memdocs init)
#!/bin/bash
if [ -f ".memdocs.yml" ]; then
    echo "Loading MemDocs memory..."
    memdocs export cursor --silent
    memdocs export claude --silent
fi
```

**Triggers:**
- `post-checkout` - When switching branches
- `post-merge` - After pulling changes
- `post-commit` - After committing (update memory)

**Pros:**
- ✅ Simple, no dependencies
- ✅ Works with any IDE
- ✅ Git-native integration

**Cons:**
- ❌ Not real-time (only on git operations)
- ❌ Manual export to multiple formats

---

### Recommended Hybrid Approach

**Combine MCP + Git Hooks + IDE Extensions:**

1. **MCP Server** - Real-time serving for Claude Desktop, Cursor
2. **Git Hooks** - Auto-export on git operations (fallback)
3. **IDE Extensions** - Enhanced UX with status indicators, commands

**Implementation Timeline:**

- **Month 1:** Enhance MCP server, add auto-start
- **Month 2:** Create VS Code extension
- **Month 3:** Create Cursor extension
- **Month 4:** Polish, documentation, marketplace

---

## Part 2: MemDocs + Empathy Book Project

### Book Vision

**Title:** "Persistent Memory for AI: Building Intelligent Systems with MemDocs and Empathy"

**Subtitle:** A Practical Guide to Git-Native AI Memory and Level 4 Anticipatory Intelligence

### Should This Be a Separate Project?

**Yes, absolutely.** Here's why:

#### Reasons for Separate Project

1. **Different Audience**
   - **MemDocs:** Developers, engineers, technical users
   - **Book:** Broader audience (executives, researchers, AI enthusiasts)

2. **Different Lifecycle**
   - **MemDocs:** Continuous updates, rapid iteration
   - **Book:** Periodic editions (v1.0, v2.0), stable content

3. **Different Tooling**
   - **MemDocs:** Python, MkDocs, Sphinx
   - **Book:** LaTeX, Markdown Book, Jupyter Book, or publishing platform

4. **Different Content Structure**
   - **MemDocs:** API docs, tutorials, references
   - **Book:** Narrative chapters, case studies, philosophy

5. **Different Publishing Channels**
   - **MemDocs:** GitHub, PyPI, documentation sites
   - **Book:** Amazon KDP, O'Reilly, LeanPub, self-published

6. **Licensing Considerations**
   - **MemDocs:** Apache 2.0 (permissive, open source)
   - **Book:** Copyright retained, or Creative Commons with attribution

### Proposed Project Structure

```
memdocs-empathy-book/
├── manuscript/
│   ├── chapters/
│   │   ├── 01-introduction.md
│   │   ├── 02-why-memory-matters.md
│   │   ├── 03-memdocs-architecture.md
│   │   ├── 04-empathy-framework.md
│   │   ├── 05-level-4-intelligence.md
│   │   ├── 06-case-studies.md
│   │   ├── 07-implementation.md
│   │   ├── 08-future-vision.md
│   │   └── appendices/
│   ├── images/
│   ├── code-examples/
│   └── references.bib
├── build/
│   ├── pdf/
│   ├── epub/
│   └── html/
├── tools/
│   ├── build.sh
│   └── deploy.sh
├── .memdocs.yml          # Use MemDocs to document the book!
├── book.toml             # mdBook config
├── Makefile
└── README.md
```

### Book Outline (Draft)

**Part I: The Memory Problem**
1. Introduction: Why AI Needs Memory
2. The Cost of Amnesia: Current AI Limitations
3. Existing Solutions and Their Limitations
4. The Vision: Git-Native Memory

**Part II: MemDocs Architecture**
5. Core Concepts: Scope, Context, Memory
6. Implementation Details: Extraction, Summarization, Embeddings
7. Security and Privacy: PHI/PII, Path Validation
8. Integration Patterns: CLI, API, MCP

**Part III: Empathy Framework**
9. What is Empathy in AI?
10. The Five Levels of Empathy
11. Level 4: Anticipatory Intelligence
12. Combining MemDocs and Empathy

**Part IV: Real-World Applications**
13. Case Study: Healthcare AI with PHI Protection
14. Case Study: Enterprise Code Documentation
15. Case Study: Open Source Community Memory
16. Case Study: Research Lab Knowledge Management

**Part V: Building with MemDocs**
17. Getting Started: Installation and Setup
18. Best Practices: Scope Policies, Memory Management
19. Advanced Patterns: Multi-Repo, Monorepos
20. Extending MemDocs: Custom Extractors, Summarizers

**Part VI: Future of AI Memory**
21. Distributed Memory Networks
22. Cross-Project Memory Graphs
23. Memory Economics: Cost, Value, ROI
24. Ethical Considerations: Privacy, Ownership
25. The Road Ahead: AGI and Persistent Memory

**Appendices:**
- A: Complete API Reference
- B: Configuration Examples
- C: Troubleshooting Guide
- D: Contributing to MemDocs
- E: Glossary

### Publishing Strategy

#### Option 1: Traditional Publishing (O'Reilly, Manning, etc.)

**Pros:**
- ✅ Professional editing, design
- ✅ Established distribution
- ✅ Credibility boost

**Cons:**
- ❌ Long timeline (12-18 months)
- ❌ Publisher takes majority of revenue
- ❌ Less control over content

**Recommendation:** Reach out to O'Reilly or Manning for a book proposal.

---

#### Option 2: Self-Publishing (Recommended)

**Platform:** LeanPub + Amazon KDP + Gumroad

**Pros:**
- ✅ Full control over content, pricing
- ✅ Rapid iteration (update book as MemDocs evolves)
- ✅ Higher revenue share (70-90%)
- ✅ Can offer early access, beta readers

**Cons:**
- ❌ You handle editing, design, marketing
- ❌ Build audience yourself

**Pricing Strategy:**
- **Early Access:** $15 (50% complete)
- **Beta:** $25 (80% complete)
- **Launch:** $39 (complete)
- **Bundle with MemDocs Pro:** $99 (book + premium support)

---

#### Option 3: Open Source Book (Jupyter Book, mdBook)

**Platform:** GitHub + GitHub Pages

**Pros:**
- ✅ Free for readers
- ✅ Community contributions
- ✅ Living document (always updated)
- ✅ Aligns with MemDocs open source philosophy

**Cons:**
- ❌ No direct revenue
- ❌ Requires separate monetization (courses, consulting)

**Monetization:**
- Offer paid video course based on book
- Consulting and enterprise training
- "Buy me a coffee" / sponsorships

---

### Recommended Approach: Hybrid

1. **Write book as open source** (GitHub, mdBook)
2. **Offer premium formats** (PDF, EPUB, print) via LeanPub ($29-$49)
3. **Create video course** based on chapters (Udemy, Teachable - $99-$199)
4. **Offer workshops** for enterprises ($2,000-$5,000/day)

**Revenue Streams:**
- Book sales: $10K-$50K/year (conservative)
- Course sales: $20K-$100K/year
- Workshops: $50K-$200K/year
- **Total potential:** $80K-$350K/year

---

### Timeline

**Phase 1: Planning (Month 1)**
- ✅ Create project structure
- ✅ Write detailed outline
- ✅ Set up build tooling (mdBook or Jupyter Book)
- ✅ Create sample chapters (Intro, Chapter 1)

**Phase 2: Writing (Months 2-6)**
- ✅ Write 4-5 chapters per month
- ✅ Get beta readers for feedback
- ✅ Create diagrams, code examples
- ✅ Test all examples with MemDocs

**Phase 3: Editing (Months 7-8)**
- ✅ Professional editing
- ✅ Technical review
- ✅ Design cover, format
- ✅ Build PDF, EPUB, HTML versions

**Phase 4: Launch (Month 9)**
- ✅ Soft launch to beta readers
- ✅ Publish on LeanPub, Amazon KDP
- ✅ Create landing page
- ✅ Marketing campaign (blog, social, podcasts)

**Phase 5: Course + Workshops (Months 10-12)**
- ✅ Create video course
- ✅ Offer workshops
- ✅ Build community

---

### Tooling Recommendations

#### Writing Platform

**Recommended:** mdBook (Rust-based, simple, fast)

```toml
# book.toml
[book]
title = "Persistent Memory for AI"
authors = ["Patrick Roebuck"]
description = "Building Intelligent Systems with MemDocs and Empathy"
language = "en"

[build]
build-dir = "build"

[output.html]
git-repository-url = "https://github.com/Smart-AI-Memory/memdocs-empathy-book"
edit-url-template = "https://github.com/Smart-AI-Memory/memdocs-empathy-book/edit/main/{path}"

[output.pdf]
enable = true
```

**Alternatives:**
- **Jupyter Book** - Great for code-heavy books
- **LaTeX** - Professional typesetting (steep learning curve)
- **Obsidian Publish** - If using Obsidian for writing

---

#### Diagram Tools

- **Excalidraw** - Hand-drawn style diagrams
- **Mermaid** - Code-to-diagram (integrated with mdBook)
- **draw.io** - Professional diagrams

---

#### CI/CD for Book

```yaml
# .github/workflows/build-book.yml
name: Build Book

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install mdBook
        run: |
          curl -sSL https://github.com/rust-lang/mdBook/releases/download/v0.4.36/mdbook-v0.4.36-x86_64-unknown-linux-gnu.tar.gz | tar -xz
          chmod +x mdbook

      - name: Build book
        run: ./mdbook build

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./build/html
```

---

## Next Steps

### For Auto-Loading Memory

1. **Immediate (This Week)**
   - ✅ Document MCP server usage in README
   - ✅ Create `.vscode/tasks.json` template
   - ✅ Write guide for Claude Desktop MCP setup

2. **Short-term (Next Month)**
   - Enhance MCP server with auto-start
   - Create VS Code extension MVP
   - Test with Claude Desktop beta

3. **Long-term (3-6 Months)**
   - Full VS Code extension release
   - Cursor extension
   - JetBrains plugin

### For Book Project

1. **Immediate (This Week)**
   - Create separate repo: `memdocs-empathy-book`
   - Set up mdBook infrastructure
   - Write introduction and chapter 1 outline

2. **Short-term (Next Month)**
   - Complete Part I (4 chapters)
   - Get 3-5 beta readers
   - Create 5-10 diagrams

3. **Long-term (6-9 Months)**
   - Complete manuscript
   - Professional editing
   - Launch on LeanPub + Amazon KDP

---

## Open Questions

### For Auto-Loading Memory

1. **Security:** How to handle API keys in MCP server?
   - Use system keychain?
   - Environment variables only?
   - Encrypted config file?

2. **Performance:** Will real-time MCP server impact IDE performance?
   - Benchmark with large projects
   - Add caching layer?
   - Lazy loading strategies?

3. **Privacy:** Should memory auto-load be opt-in or opt-out?
   - Opt-in (explicit `memdocs serve` command)
   - Opt-out (auto-start with disable flag)
   - Per-project setting in `.memdocs.yml`?

### For Book Project

1. **Audience:** Primary vs secondary audiences?
   - Primary: Senior engineers, architects, tech leads
   - Secondary: AI researchers, product managers
   - Tertiary: Executives, non-technical leaders

2. **Technical Depth:** How much code vs concepts?
   - 60% concepts, 40% code (recommended)
   - Each chapter: theory → examples → exercises
   - Appendices for deep technical content

3. **MemDocs Version:** Track current version or be version-agnostic?
   - Focus on v2.0 (current)
   - Include "Future of MemDocs" chapter for v3.0 vision
   - Update book with major MemDocs releases

---

## Conclusion

Both initiatives are valuable and complementary:

1. **Auto-Loading Memory** enhances MemDocs usability and adoption
2. **Book Project** establishes thought leadership and creates new revenue streams

**Recommendation:**
- Start **auto-loading memory** immediately (low-hanging fruit via MCP)
- Begin **book planning** in parallel (low time investment initially)
- Ramp up book writing once auto-loading is stable

**Resource Allocation:**
- **70% MemDocs development** (core product)
- **20% Auto-loading memory** (usability enhancement)
- **10% Book planning/writing** (long-term investment)

This ensures MemDocs remains the priority while building momentum for the book.

---

**Questions? Feedback?** Let's discuss and refine this plan!
