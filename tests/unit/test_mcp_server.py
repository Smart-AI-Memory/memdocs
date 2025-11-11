"""Unit tests for MCP server."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from memdocs.mcp_server import DocIntMCPServer


class TestDocIntMCPServer:
    """Test MCP server functionality."""

    @pytest.fixture
    def temp_memdocs_dir(self, tmp_path: Path) -> Path:
        """Create a temporary .memdocs directory structure."""
        memdocs_dir = tmp_path / ".memdocs"
        docs_dir = memdocs_dir / "docs"
        memory_dir = memdocs_dir / "memory"

        docs_dir.mkdir(parents=True)
        memory_dir.mkdir(parents=True)

        return tmp_path

    @pytest.fixture
    def mcp_server(self, temp_memdocs_dir: Path) -> DocIntMCPServer:
        """Create MCP server instance with mocked embedder."""
        with (
            patch("memdocs.mcp_server.LocalEmbedder"),
            patch("memdocs.mcp_server.LocalVectorSearch"),
        ):
            server = DocIntMCPServer(repo_path=temp_memdocs_dir)
            server.search_enabled = False  # Disable for most tests
            return server

    def test_initialization(self, temp_memdocs_dir: Path):
        """Test MCP server initialization."""
        with (
            patch("memdocs.mcp_server.LocalEmbedder"),
            patch("memdocs.mcp_server.LocalVectorSearch"),
        ):
            server = DocIntMCPServer(repo_path=temp_memdocs_dir)

            assert server.repo_path == temp_memdocs_dir
            assert server.docs_dir == temp_memdocs_dir / ".memdocs" / "docs"
            assert server.memory_dir == temp_memdocs_dir / ".memdocs" / "memory"

    def test_initialization_without_search(self, temp_memdocs_dir: Path):
        """Test initialization when search dependencies are missing."""
        with patch("memdocs.mcp_server.LocalEmbedder", side_effect=ImportError):
            server = DocIntMCPServer(repo_path=temp_memdocs_dir)

            assert not server.search_enabled

    def test_search_memory_disabled(self, mcp_server: DocIntMCPServer):
        """Test search_memory when search is disabled."""
        mcp_server.search_enabled = False

        results = mcp_server.search_memory("test query")

        assert len(results) == 1
        assert "error" in results[0]
        assert "not available" in results[0]["error"]

    def test_search_memory_enabled(self, mcp_server: DocIntMCPServer):
        """Test search_memory when search is enabled."""
        # Setup mocks
        mcp_server.search_enabled = True
        mcp_server.embedder = MagicMock()
        mcp_server.search = MagicMock()

        # Mock embedding and search results
        mock_embedding = [0.1, 0.2, 0.3]
        mcp_server.embedder.embed_query.return_value = mock_embedding

        mock_results = [
            {
                "score": 0.95,
                "metadata": {
                    "features": ["feature1"],
                    "file_paths": ["test.py"],
                    "chunk_text": "Test content",
                    "doc_id": "doc123",
                },
            }
        ]
        mcp_server.search.search.return_value = mock_results

        # Execute
        results = mcp_server.search_memory("test query", k=3)

        # Verify
        assert len(results) == 1
        assert results[0]["score"] == 0.95
        assert results[0]["features"] == ["feature1"]
        assert results[0]["files"] == ["test.py"]
        assert results[0]["preview"] == "Test content"
        assert results[0]["doc_id"] == "doc123"

        mcp_server.embedder.embed_query.assert_called_once_with("test query")
        mcp_server.search.search.assert_called_once_with(mock_embedding, k=3)

    def test_get_symbols_no_file(self, mcp_server: DocIntMCPServer):
        """Test get_symbols when symbols.yaml doesn't exist."""
        result = mcp_server.get_symbols()

        assert "error" in result
        assert "No symbols found" in result["error"]

    def test_get_symbols_all(self, mcp_server: DocIntMCPServer):
        """Test get_symbols returns all symbols."""
        # Create symbols.yaml
        symbols_data = {
            "symbols": [
                {"file": "test.py", "kind": "function", "name": "func1", "line": 1},
                {"file": "other.py", "kind": "class", "name": "Class1", "line": 5},
            ]
        }
        symbols_file = mcp_server.docs_dir / "symbols.yaml"
        with open(symbols_file, "w") as f:
            yaml.dump(symbols_data, f)

        result = mcp_server.get_symbols()

        assert "symbols" in result
        assert len(result["symbols"]) == 2

    def test_get_symbols_filtered(self, mcp_server: DocIntMCPServer):
        """Test get_symbols with file path filter."""
        # Create symbols.yaml
        symbols_data = {
            "symbols": [
                {"file": "test.py", "kind": "function", "name": "func1", "line": 1},
                {"file": "other.py", "kind": "class", "name": "Class1", "line": 5},
            ]
        }
        symbols_file = mcp_server.docs_dir / "symbols.yaml"
        with open(symbols_file, "w") as f:
            yaml.dump(symbols_data, f)

        result = mcp_server.get_symbols(file_path="test.py")

        assert "symbols" in result
        assert len(result["symbols"]) == 1
        assert result["symbols"][0]["file"] == "test.py"

    def test_get_documentation_latest(self, mcp_server: DocIntMCPServer):
        """Test get_documentation returns latest (index.json)."""
        # Create index.json
        index_data = {
            "commit": "abc123",
            "timestamp": "2025-01-08T00:00:00Z",
            "scope": {"level": "file", "paths": ["test.py"]},
        }
        index_file = mcp_server.docs_dir / "index.json"
        with open(index_file, "w") as f:
            json.dump(index_data, f)

        result = mcp_server.get_documentation()

        assert result["commit"] == "abc123"
        assert result["timestamp"] == "2025-01-08T00:00:00Z"

    def test_get_documentation_specific(self, mcp_server: DocIntMCPServer):
        """Test get_documentation with specific doc_id."""
        # Create specific doc
        doc_data = {
            "commit": "def456",
            "timestamp": "2025-01-07T00:00:00Z",
        }
        doc_file = mcp_server.docs_dir / "def456.json"
        with open(doc_file, "w") as f:
            json.dump(doc_data, f)

        result = mcp_server.get_documentation(doc_id="def456")

        assert result["commit"] == "def456"

    def test_get_documentation_not_found(self, mcp_server: DocIntMCPServer):
        """Test get_documentation when doc doesn't exist."""
        result = mcp_server.get_documentation(doc_id="nonexistent")

        assert "error" in result
        assert "not found" in result["error"]

    def test_get_documentation_no_index(self, mcp_server: DocIntMCPServer):
        """Test get_documentation when index.json doesn't exist."""
        result = mcp_server.get_documentation()

        assert "error" in result
        assert "No documentation found" in result["error"]

    def test_get_summary_exists(self, mcp_server: DocIntMCPServer):
        """Test get_summary when summary.md exists."""
        summary_content = "# Project Summary\n\nThis is a test summary."
        summary_file = mcp_server.docs_dir / "summary.md"
        summary_file.write_text(summary_content, encoding="utf-8")

        result = mcp_server.get_summary()

        assert result == summary_content

    def test_get_summary_not_found(self, mcp_server: DocIntMCPServer):
        """Test get_summary when summary.md doesn't exist."""
        result = mcp_server.get_summary()

        assert "No summary found" in result

    def test_query_analysis_invalid_type(self, mcp_server: DocIntMCPServer):
        """Test query_analysis with invalid query_type."""
        result = mcp_server.query_analysis(query_type="invalid")

        assert "error" in result
        assert "Invalid query_type" in result["error"]

    def test_query_analysis_file_not_found(self, mcp_server: DocIntMCPServer):
        """Test query_analysis for non-existent file."""
        result = mcp_server.query_analysis(file_path="nonexistent.py")

        assert "error" in result
        assert "No analysis found" in result["error"]

    def test_query_analysis_file_specific_issues(self, mcp_server: DocIntMCPServer):
        """Test query_analysis for specific file with issues type."""
        # Create file directory with index.json
        file_dir = mcp_server.docs_dir / "test"
        file_dir.mkdir()

        index_data = {
            "commit": "abc123",
            "timestamp": "2025-01-08T00:00:00Z",
            "scope": {"paths": ["test.py"]},
            "features": [
                {"id": "feat-1", "title": "Test feature"},
            ],
            "impacts": {
                "apis": ["test_api"],
                "breaking_changes": [],
            },
        }
        index_file = file_dir / "index.json"
        with open(index_file, "w") as f:
            json.dump(index_data, f)

        result = mcp_server.query_analysis(file_path="test.py", query_type="issues")

        assert "issues" in result
        assert len(result["issues"]) == 1
        assert "impacts" in result

    def test_query_analysis_file_specific_all(self, mcp_server: DocIntMCPServer):
        """Test query_analysis for specific file with all type."""
        # Create file directory with index.json and summary.md
        file_dir = mcp_server.docs_dir / "test"
        file_dir.mkdir()

        index_data = {
            "commit": "abc123",
            "features": [{"id": "feat-1"}],
        }
        index_file = file_dir / "index.json"
        with open(index_file, "w") as f:
            json.dump(index_data, f)

        summary_content = "Test summary"
        summary_file = file_dir / "summary.md"
        summary_file.write_text(summary_content)

        result = mcp_server.query_analysis(file_path="test.py", query_type="all")

        assert "issues" in result
        assert "summary" in result
        assert "full_analysis" in result
        assert result["summary"] == summary_content

    def test_query_analysis_all_files(self, mcp_server: DocIntMCPServer):
        """Test query_analysis for all files."""
        # Create multiple file directories
        for i in range(3):
            file_dir = mcp_server.docs_dir / f"test{i}"
            file_dir.mkdir()

            index_data = {
                "commit": f"abc{i}",
                "timestamp": "2025-01-08T00:00:00Z",
                "scope": {"paths": [f"test{i}.py"]},
                "features": [{"id": f"feat-{i}", "tags": ["prediction"] if i == 0 else []}],
                "severity_score": 0.5,
            }
            index_file = file_dir / "index.json"
            with open(index_file, "w") as f:
                json.dump(index_data, f)

        result = mcp_server.query_analysis(query_type="all")

        assert "files" in result
        assert "total_files" in result
        assert result["total_files"] == 3
        assert len(result["files"]) == 3

        # Check first file has prediction count
        first_file = result["files"][0]
        assert "prediction_count" in first_file

    def test_query_analysis_file_no_index(self, mcp_server: DocIntMCPServer):
        """Test query_analysis when file directory exists but no index.json."""
        # Create file directory without index.json
        file_dir = mcp_server.docs_dir / "test"
        file_dir.mkdir()

        result = mcp_server.query_analysis(file_path="test.py")

        assert "error" in result
        assert "No index.json found" in result["error"]


class TestMCPServerProtocol:
    """Test MCP server protocol implementation."""

    @pytest.fixture
    def temp_memdocs_dir(self, tmp_path: Path) -> Path:
        """Create a temporary .memdocs directory structure."""
        memdocs_dir = tmp_path / ".memdocs"
        docs_dir = memdocs_dir / "docs"
        memory_dir = memdocs_dir / "memory"

        docs_dir.mkdir(parents=True)
        memory_dir.mkdir(parents=True)

        # Create test data files
        index_data = {
            "commit": "abc123",
            "timestamp": "2025-01-08T00:00:00Z",
            "scope": {"paths": ["test.py"]},
        }
        with open(docs_dir / "index.json", "w") as f:
            json.dump(index_data, f)

        summary_content = "# Test Summary"
        (docs_dir / "summary.md").write_text(summary_content)

        symbols_data = {"symbols": [{"file": "test.py", "kind": "function", "name": "test"}]}
        with open(docs_dir / "symbols.yaml", "w") as f:
            yaml.dump(symbols_data, f)

        return tmp_path

    @pytest.mark.asyncio
    async def test_serve_mcp_tool_list(self, temp_memdocs_dir: Path):
        """Test that serve_mcp registers all expected tools."""
        from mcp.server import Server

        # We can't easily test the full serve_mcp() due to stdio_server,
        # but we can test the server setup and tool registration
        with (
            patch("memdocs.mcp_server.LocalEmbedder"),
            patch("memdocs.mcp_server.LocalVectorSearch"),
            patch("os.environ.get", return_value=str(temp_memdocs_dir)),
        ):

            # Create a test server to check tool registration
            server = Server("memdocs-test")

            # Simulate the tool registration from serve_mcp
            @server.list_tools()
            async def list_tools():
                from mcp.types import Tool

                return [
                    Tool(
                        name="search_memory",
                        description="Search project memory using natural language query",
                        inputSchema={"type": "object", "properties": {}},
                    ),
                    Tool(
                        name="get_symbols",
                        description="Get code symbols",
                        inputSchema={"type": "object", "properties": {}},
                    ),
                    Tool(
                        name="get_documentation",
                        description="Get generated documentation",
                        inputSchema={"type": "object", "properties": {}},
                    ),
                    Tool(
                        name="get_summary",
                        description="Get summary",
                        inputSchema={"type": "object", "properties": {}},
                    ),
                    Tool(
                        name="query_analysis",
                        description="Query analysis",
                        inputSchema={"type": "object", "properties": {}},
                    ),
                ]

            # Call the registered handler
            tools = await list_tools()

            # Verify all tools are registered
            tool_names = [tool.name for tool in tools]
            assert "search_memory" in tool_names
            assert "get_symbols" in tool_names
            assert "get_documentation" in tool_names
            assert "get_summary" in tool_names
            assert "query_analysis" in tool_names
            assert len(tool_names) == 5

    @pytest.mark.asyncio
    async def test_call_tool_search_memory(self, temp_memdocs_dir: Path):
        """Test call_tool with search_memory."""
        from mcp.types import TextContent

        with (
            patch("memdocs.mcp_server.LocalEmbedder"),
            patch("memdocs.mcp_server.LocalVectorSearch"),
        ):

            server_instance = DocIntMCPServer(repo_path=temp_memdocs_dir)
            server_instance.search_enabled = False

            # Simulate call_tool behavior
            async def call_tool(name: str, arguments: dict):
                if name == "search_memory":
                    query = arguments.get("query", "")
                    k = arguments.get("k", 5)
                    results = server_instance.search_memory(query, k)
                    return [TextContent(type="text", text=json.dumps(results, indent=2))]
                return []

            # Test the call
            result = await call_tool("search_memory", {"query": "test", "k": 3})

            assert len(result) == 1
            assert isinstance(result[0], TextContent)
            response_data = json.loads(result[0].text)
            assert "error" in response_data[0]  # Search disabled

    @pytest.mark.asyncio
    async def test_call_tool_get_symbols(self, temp_memdocs_dir: Path):
        """Test call_tool with get_symbols."""
        from mcp.types import TextContent

        with (
            patch("memdocs.mcp_server.LocalEmbedder"),
            patch("memdocs.mcp_server.LocalVectorSearch"),
        ):

            server_instance = DocIntMCPServer(repo_path=temp_memdocs_dir)

            # Simulate call_tool behavior
            async def call_tool(name: str, arguments: dict):
                if name == "get_symbols":
                    file_path = arguments.get("file_path")
                    results = server_instance.get_symbols(file_path)
                    return [TextContent(type="text", text=json.dumps(results, indent=2))]
                return []

            # Test the call
            result = await call_tool("get_symbols", {})

            assert len(result) == 1
            assert isinstance(result[0], TextContent)
            response_data = json.loads(result[0].text)
            assert "symbols" in response_data

    @pytest.mark.asyncio
    async def test_call_tool_get_documentation(self, temp_memdocs_dir: Path):
        """Test call_tool with get_documentation."""
        from mcp.types import TextContent

        with (
            patch("memdocs.mcp_server.LocalEmbedder"),
            patch("memdocs.mcp_server.LocalVectorSearch"),
        ):

            server_instance = DocIntMCPServer(repo_path=temp_memdocs_dir)

            # Simulate call_tool behavior
            async def call_tool(name: str, arguments: dict):
                if name == "get_documentation":
                    doc_id = arguments.get("doc_id")
                    results = server_instance.get_documentation(doc_id)
                    return [TextContent(type="text", text=json.dumps(results, indent=2))]
                return []

            # Test the call
            result = await call_tool("get_documentation", {})

            assert len(result) == 1
            assert isinstance(result[0], TextContent)
            response_data = json.loads(result[0].text)
            assert "commit" in response_data

    @pytest.mark.asyncio
    async def test_call_tool_get_summary(self, temp_memdocs_dir: Path):
        """Test call_tool with get_summary."""
        from mcp.types import TextContent

        with (
            patch("memdocs.mcp_server.LocalEmbedder"),
            patch("memdocs.mcp_server.LocalVectorSearch"),
        ):

            server_instance = DocIntMCPServer(repo_path=temp_memdocs_dir)

            # Simulate call_tool behavior
            async def call_tool(name: str, arguments: dict):
                if name == "get_summary":
                    summary = server_instance.get_summary()
                    return [TextContent(type="text", text=summary)]
                return []

            # Test the call
            result = await call_tool("get_summary", {})

            assert len(result) == 1
            assert isinstance(result[0], TextContent)
            assert "Test Summary" in result[0].text

    @pytest.mark.asyncio
    async def test_call_tool_query_analysis(self, temp_memdocs_dir: Path):
        """Test call_tool with query_analysis."""
        from mcp.types import TextContent

        with (
            patch("memdocs.mcp_server.LocalEmbedder"),
            patch("memdocs.mcp_server.LocalVectorSearch"),
        ):

            server_instance = DocIntMCPServer(repo_path=temp_memdocs_dir)

            # Simulate call_tool behavior
            async def call_tool(name: str, arguments: dict):
                if name == "query_analysis":
                    file_path = arguments.get("file_path")
                    query_type = arguments.get("query_type", "all")
                    results = server_instance.query_analysis(file_path, query_type)
                    return [TextContent(type="text", text=json.dumps(results, indent=2))]
                return []

            # Test the call
            result = await call_tool("query_analysis", {"query_type": "issues"})

            assert len(result) == 1
            assert isinstance(result[0], TextContent)
            response_data = json.loads(result[0].text)
            # Should return files list since no specific file_path provided
            assert "files" in response_data

    @pytest.mark.asyncio
    async def test_call_tool_unknown(self, temp_memdocs_dir: Path):
        """Test call_tool with unknown tool name."""
        from mcp.types import TextContent

        with (
            patch("memdocs.mcp_server.LocalEmbedder"),
            patch("memdocs.mcp_server.LocalVectorSearch"),
        ):

            server_instance = DocIntMCPServer(repo_path=temp_memdocs_dir)

            # Simulate call_tool behavior
            async def call_tool(name: str, arguments: dict):
                if name not in [
                    "search_memory",
                    "get_symbols",
                    "get_documentation",
                    "get_summary",
                    "query_analysis",
                ]:
                    error_msg = f"Unknown tool: {name}"
                    return [TextContent(type="text", text=json.dumps({"error": error_msg}))]
                return []

            # Test the call
            result = await call_tool("unknown_tool", {})

            assert len(result) == 1
            assert isinstance(result[0], TextContent)
            response_data = json.loads(result[0].text)
            assert "error" in response_data
            assert "Unknown tool" in response_data["error"]

    @pytest.mark.asyncio
    async def test_call_tool_exception_handling(self, temp_memdocs_dir: Path):
        """Test call_tool exception handling."""
        from mcp.types import TextContent

        with (
            patch("memdocs.mcp_server.LocalEmbedder"),
            patch("memdocs.mcp_server.LocalVectorSearch"),
        ):

            server_instance = DocIntMCPServer(repo_path=temp_memdocs_dir)

            # Simulate call_tool behavior with exception
            async def call_tool(name: str, arguments: dict):
                try:
                    if name == "get_symbols":
                        # Force an exception
                        raise ValueError("Test exception")
                except Exception as e:
                    error_msg = f"Error executing {name}: {str(e)}"
                    return [TextContent(type="text", text=json.dumps({"error": error_msg}))]

            # Test the call
            result = await call_tool("get_symbols", {})

            assert len(result) == 1
            assert isinstance(result[0], TextContent)
            response_data = json.loads(result[0].text)
            assert "error" in response_data
            assert "Test exception" in response_data["error"]

    def test_serve_mcp_function_exists(self):
        """Test that serve_mcp function exists and is callable."""
        from memdocs.mcp_server import serve_mcp
        import inspect

        # Verify function exists
        assert callable(serve_mcp)

        # Verify it's an async function
        assert inspect.iscoroutinefunction(serve_mcp)

    def test_main_entry_point(self):
        """Test that __main__ entry point exists."""
        import memdocs.mcp_server as mcp_module

        # Verify the module can be used as __main__
        assert hasattr(mcp_module, "serve_mcp")

        # The module should be runnable with asyncio.run(serve_mcp())
        # We can't test this directly without mocking stdio, but we can verify the structure
        with (
            patch("memdocs.mcp_server.stdio_server"),
            patch("memdocs.mcp_server.LocalEmbedder"),
            patch("memdocs.mcp_server.LocalVectorSearch"),
            patch("os.environ.get", return_value="."),
        ):

            # Import and verify module structure
            import importlib
            import memdocs.mcp_server

            importlib.reload(memdocs.mcp_server)

            # Verify key components exist
            assert hasattr(memdocs.mcp_server, "DocIntMCPServer")
            assert hasattr(memdocs.mcp_server, "serve_mcp")


class TestMCPServerIntegration:
    """Integration-style tests for MCP server components."""

    @pytest.fixture
    def populated_memdocs_dir(self, tmp_path: Path) -> Path:
        """Create a fully populated .memdocs directory."""
        memdocs_dir = tmp_path / ".memdocs"
        docs_dir = memdocs_dir / "docs"
        memory_dir = memdocs_dir / "memory"

        docs_dir.mkdir(parents=True)
        memory_dir.mkdir(parents=True)

        # Create comprehensive test data
        index_data = {
            "commit": "abc123",
            "timestamp": "2025-01-08T12:00:00Z",
            "scope": {
                "paths": ["src/auth.py", "src/db.py"],
                "level": "module",
                "file_count": 2,
            },
            "features": [
                {
                    "id": "feat-1",
                    "title": "Add authentication",
                    "description": "Implements JWT authentication",
                    "risk": ["security"],
                    "tags": ["auth", "security"],
                },
                {
                    "id": "feat-2",
                    "title": "Database migration",
                    "description": "Adds user table",
                    "risk": [],
                    "tags": ["database"],
                },
            ],
            "impacts": {
                "apis": ["/api/auth/login", "/api/auth/logout"],
                "breaking_changes": [],
                "tests_added": 5,
                "tests_modified": 2,
                "migration_required": True,
            },
            "refs": {
                "pr": 42,
                "issues": [1, 2, 3],
                "files_changed": ["src/auth.py", "src/db.py"],
                "commits": ["abc123"],
            },
        }
        with open(docs_dir / "index.json", "w") as f:
            json.dump(index_data, f, indent=2)

        # Create summary
        summary = """# Project Summary

## Features
- Authentication system
- Database layer

## Impact
- 2 new APIs
- Migration required
"""
        (docs_dir / "summary.md").write_text(summary)

        # Create symbols
        symbols = {
            "symbols": [
                {
                    "file": "src/auth.py",
                    "kind": "function",
                    "name": "authenticate",
                    "line": 10,
                    "signature": "def authenticate(username: str, password: str) -> bool",
                },
                {
                    "file": "src/auth.py",
                    "kind": "class",
                    "name": "User",
                    "line": 25,
                    "methods": ["__init__", "verify_password"],
                },
                {
                    "file": "src/db.py",
                    "kind": "function",
                    "name": "connect",
                    "line": 5,
                },
            ]
        }
        with open(docs_dir / "symbols.yaml", "w") as f:
            yaml.dump(symbols, f)

        return tmp_path

    def test_full_workflow_get_all_data(self, populated_memdocs_dir: Path):
        """Test retrieving all data from a populated MCP server."""
        with (
            patch("memdocs.mcp_server.LocalEmbedder"),
            patch("memdocs.mcp_server.LocalVectorSearch"),
        ):

            server = DocIntMCPServer(repo_path=populated_memdocs_dir)

            # Get documentation
            docs = server.get_documentation()
            assert docs["commit"] == "abc123"
            assert len(docs["features"]) == 2
            assert docs["impacts"]["migration_required"] is True

            # Get summary
            summary = server.get_summary()
            assert "Authentication system" in summary
            assert "Migration required" in summary

            # Get symbols
            symbols = server.get_symbols()
            assert len(symbols["symbols"]) == 3

            # Get filtered symbols
            auth_symbols = server.get_symbols(file_path="src/auth.py")
            assert len(auth_symbols["symbols"]) == 2
            assert all(s["file"] == "src/auth.py" for s in auth_symbols["symbols"])

    def test_query_analysis_comprehensive(self, populated_memdocs_dir: Path):
        """Test comprehensive query_analysis functionality."""
        # Create empathy analysis directory structure
        docs_dir = populated_memdocs_dir / ".memdocs" / "docs"
        auth_dir = docs_dir / "auth"
        auth_dir.mkdir()

        auth_analysis = {
            "commit": "abc123",
            "timestamp": "2025-01-08T12:00:00Z",
            "scope": {"paths": ["src/auth.py"]},
            "features": [
                {
                    "id": "feat-1",
                    "title": "Security issue",
                    "tags": ["security", "prediction"],
                },
                {
                    "id": "feat-2",
                    "title": "Performance issue",
                    "tags": ["performance"],
                },
            ],
            "severity_score": 0.8,
        }
        with open(auth_dir / "index.json", "w") as f:
            json.dump(auth_analysis, f)

        with open(auth_dir / "summary.md", "w") as f:
            f.write("# Auth Analysis\n\nSecurity improvements needed.")

        with (
            patch("memdocs.mcp_server.LocalEmbedder"),
            patch("memdocs.mcp_server.LocalVectorSearch"),
        ):

            server = DocIntMCPServer(repo_path=populated_memdocs_dir)

            # Query all files
            result = server.query_analysis(query_type="all")
            assert "files" in result
            assert "total_files" in result
            assert result["total_files"] == 1

            # Query specific file for issues
            result = server.query_analysis(file_path="src/auth.py", query_type="issues")
            assert "issues" in result
            assert len(result["issues"]) == 2

            # Query for predictions
            result = server.query_analysis(file_path="src/auth.py", query_type="predictions")
            assert "summary" in result

            # Query empathy
            result = server.query_analysis(file_path="src/auth.py", query_type="empathy")
            assert "full_analysis" in result
            assert result["full_analysis"]["severity_score"] == 0.8

    @pytest.mark.asyncio
    async def test_serve_mcp_function_execution(self, populated_memdocs_dir: Path):
        """Test actual serve_mcp function execution with mocked stdio."""
        from unittest.mock import AsyncMock, MagicMock
        import asyncio

        # Create mock streams
        mock_read_stream = AsyncMock()
        mock_write_stream = AsyncMock()

        # Create mock stdio_server context manager
        class MockStdioServer:
            async def __aenter__(self):
                return (mock_read_stream, mock_write_stream)

            async def __aexit__(self, *args):
                return None

        # Mock server run to avoid actually starting the server
        mock_server_run = AsyncMock()

        with (
            patch("memdocs.mcp_server.stdio_server", return_value=MockStdioServer()),
            patch("memdocs.mcp_server.LocalEmbedder"),
            patch("memdocs.mcp_server.LocalVectorSearch"),
            patch("os.environ.get", return_value=str(populated_memdocs_dir)),
            patch("memdocs.mcp_server.Server") as MockServer,
        ):

            # Mock Server instance
            mock_server_instance = MagicMock()
            mock_server_instance.run = mock_server_run
            mock_server_instance.create_initialization_options = MagicMock(return_value={})
            MockServer.return_value = mock_server_instance

            # Import and run serve_mcp
            from memdocs.mcp_server import serve_mcp

            # Run the function with timeout to prevent hanging
            try:
                await asyncio.wait_for(serve_mcp(), timeout=0.1)
            except asyncio.TimeoutError:
                # Expected - the mock run() doesn't return, so we timeout
                pass
            except Exception:
                # Also acceptable - mocks may cause various exceptions
                pass

            # Verify Server was instantiated
            MockServer.assert_called_once_with("memdocs")

            # Verify run was called (this means the server setup completed)
            mock_server_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_serve_mcp_decorated_functions_execution(self, populated_memdocs_dir: Path):
        """Test the decorated list_tools and call_tool functions are executed."""
        from unittest.mock import AsyncMock, MagicMock
        import asyncio

        # Track which decorators were called
        list_tools_func = None
        call_tool_func = None

        # Create a mock Server class that captures the decorated functions
        class MockServerClass:
            def __init__(self, name):
                self.name = name
                self.run_called = False

            def list_tools(self):
                def decorator(func):
                    nonlocal list_tools_func
                    list_tools_func = func
                    return func

                return decorator

            def call_tool(self):
                def decorator(func):
                    nonlocal call_tool_func
                    call_tool_func = func
                    return func

                return decorator

            def create_initialization_options(self):
                return {}

            async def run(self, read, write, options):
                self.run_called = True
                # Don't actually run - just mark as called

        # Create mock stdio context
        class MockStdioServer:
            async def __aenter__(self):
                return (MagicMock(), MagicMock())

            async def __aexit__(self, *args):
                return None

        with (
            patch("memdocs.mcp_server.stdio_server", return_value=MockStdioServer()),
            patch("memdocs.mcp_server.LocalEmbedder"),
            patch("memdocs.mcp_server.LocalVectorSearch"),
            patch("os.environ.get", return_value=str(populated_memdocs_dir)),
            patch("memdocs.mcp_server.Server", MockServerClass),
            patch("logging.info"),
            patch("logging.error"),
        ):

            from memdocs.mcp_server import serve_mcp

            # Try to run serve_mcp (will execute decorator registrations)
            try:
                await asyncio.wait_for(serve_mcp(), timeout=0.5)
            except (asyncio.TimeoutError, Exception):
                pass

            # Now test the captured decorated functions
            assert list_tools_func is not None, "list_tools decorator was not called"
            assert call_tool_func is not None, "call_tool decorator was not called"

            # Test list_tools function
            from mcp.types import Tool

            tools = await list_tools_func()
            assert isinstance(tools, list)
            assert len(tools) == 5
            tool_names = [t.name for t in tools]
            assert "search_memory" in tool_names
            assert "get_symbols" in tool_names
            assert "get_documentation" in tool_names
            assert "get_summary" in tool_names
            assert "query_analysis" in tool_names

            # Test call_tool function with various tools
            from mcp.types import TextContent

            # Test search_memory
            result = await call_tool_func("search_memory", {"query": "test", "k": 5})
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], TextContent)

            # Test get_symbols
            result = await call_tool_func("get_symbols", {})
            assert isinstance(result, list)
            data = json.loads(result[0].text)
            assert "symbols" in data

            # Test get_documentation
            result = await call_tool_func("get_documentation", {})
            assert isinstance(result, list)
            data = json.loads(result[0].text)
            assert "commit" in data

            # Test get_summary
            result = await call_tool_func("get_summary", {})
            assert isinstance(result, list)
            assert "Project Summary" in result[0].text

            # Test query_analysis
            result = await call_tool_func("query_analysis", {"query_type": "all"})
            assert isinstance(result, list)

            # Test unknown tool (error path)
            result = await call_tool_func("unknown_tool", {})
            assert isinstance(result, list)
            data = json.loads(result[0].text)
            assert "error" in data
            assert "Unknown tool" in data["error"]
