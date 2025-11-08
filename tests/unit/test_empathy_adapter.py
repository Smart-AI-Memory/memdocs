"""
Unit tests for empathy_adapter module.
"""
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml


class TestEmpathyAdapter:
    """Test EmpathyAdapter class."""

    @patch("memdocs.empathy_adapter.MemoryIndexer")
    def test_initialization(self, mock_indexer_class, tmp_path: Path):
        """Test adapter initialization."""
        from memdocs.empathy_adapter import EmpathyAdapter

        mock_indexer = Mock()
        mock_indexer_class.return_value = mock_indexer

        memdocs_root = tmp_path / ".memdocs"
        adapter = EmpathyAdapter(memdocs_root)

        assert adapter.memdocs_root == memdocs_root
        assert adapter.docs_dir == memdocs_root / "docs"
        assert adapter.memory_dir == memdocs_root / "memory"
        assert adapter.docs_dir.exists()
        assert adapter.memory_dir.exists()
        mock_indexer_class.assert_called_once_with(adapter.memory_dir)

    @patch("memdocs.empathy_adapter.MemoryIndexer")
    def test_extract_features_critical_issues(self, mock_indexer_class, tmp_path: Path):
        """Test extracting features from critical issues."""
        from memdocs.empathy_adapter import EmpathyAdapter

        adapter = EmpathyAdapter(tmp_path / ".memdocs")

        analysis_results = {
            "current_issues": [
                {
                    "message": "Critical security vulnerability",
                    "severity": "critical",
                    "type": "security",
                    "layer": "rules",
                    "recommendation": "Fix immediately",
                },
                {
                    "message": "Error in authentication",
                    "severity": "error",
                    "type": "logic",
                    "layer": "patterns",
                },
                {
                    "message": "Warning about style",
                    "severity": "warning",  # Should be filtered out
                    "type": "style",
                },
            ],
            "predictions": [],
        }

        features = adapter._extract_features(analysis_results)

        # Should only extract critical/error severity issues
        assert len(features) == 2
        assert features[0].id == "feat-001"
        assert "Critical security vulnerability" in features[0].title
        assert features[0].description == "Fix immediately"
        assert "security" in features[0].risk
        assert "rules" in features[0].tags

    @patch("memdocs.empathy_adapter.MemoryIndexer")
    def test_extract_features_with_predictions(self, mock_indexer_class, tmp_path: Path):
        """Test extracting features including predictions."""
        from memdocs.empathy_adapter import EmpathyAdapter

        adapter = EmpathyAdapter(tmp_path / ".memdocs")

        analysis_results = {
            "current_issues": [],
            "predictions": [
                {
                    "title": "Future API breaking change",
                    "description": "This will break in v3.0",
                    "impact": "high",
                    "timeframe": "6 months",
                },
                {
                    "title": "Performance degradation expected",
                    "description": "Load will increase",
                    "impact": "medium",
                    "timeframe": "3 months",
                },
            ],
        }

        features = adapter._extract_features(analysis_results)

        # Should have 2 prediction features
        assert len(features) == 2
        assert "Future API breaking change" in features[0].title
        assert "prediction" in features[0].tags
        assert "6 months" in features[0].tags
        assert "anticipatory" in features[0].risk

    @patch("memdocs.empathy_adapter.MemoryIndexer")
    def test_extract_features_limit(self, mock_indexer_class, tmp_path: Path):
        """Test that features are limited to reasonable count."""
        from memdocs.empathy_adapter import EmpathyAdapter

        adapter = EmpathyAdapter(tmp_path / ".memdocs")

        # Create many issues
        issues = [
            {
                "message": f"Issue {i}",
                "severity": "critical",
                "type": "test",
                "layer": "rules",
            }
            for i in range(10)
        ]

        predictions = [
            {
                "title": f"Prediction {i}",
                "description": "Test",
                "impact": "high",
                "timeframe": "soon",
            }
            for i in range(10)
        ]

        analysis_results = {"current_issues": issues, "predictions": predictions}

        features = adapter._extract_features(analysis_results)

        # Should limit to 5 issues + 3 predictions = 8 total
        assert len(features) == 8

    @patch("memdocs.empathy_adapter.MemoryIndexer")
    def test_extract_impacts(self, mock_indexer_class, tmp_path: Path):
        """Test extracting impact information."""
        from memdocs.empathy_adapter import EmpathyAdapter

        adapter = EmpathyAdapter(tmp_path / ".memdocs")

        analysis_results = {
            "current_issues": [
                {"message": "API endpoint /users is broken", "severity": "critical"},
                {"message": "Route /auth needs update", "severity": "error"},
                {"message": "Test suite failing", "severity": "error"},
                {"message": "Critical database error", "severity": "critical"},
            ]
        }

        impacts = adapter._extract_impacts(analysis_results)

        assert len(impacts.apis) >= 2  # Should detect API/route issues
        assert len(impacts.breaking_changes) == 2  # Critical severity
        assert impacts.tests_modified == 1  # Test-related issue
        assert impacts.migration_required is True  # Has breaking changes

    @patch("memdocs.empathy_adapter.MemoryIndexer")
    def test_extract_impacts_no_breaking_changes(self, mock_indexer_class, tmp_path: Path):
        """Test impacts when there are no breaking changes."""
        from memdocs.empathy_adapter import EmpathyAdapter

        adapter = EmpathyAdapter(tmp_path / ".memdocs")

        analysis_results = {
            "current_issues": [
                {"message": "Minor style issue", "severity": "warning"},
            ]
        }

        impacts = adapter._extract_impacts(analysis_results)

        assert impacts.breaking_changes == []
        assert impacts.migration_required is False

    @patch("memdocs.empathy_adapter.MemoryIndexer")
    def test_write_index_json(self, mock_indexer_class, tmp_path: Path):
        """Test writing index.json file."""
        from memdocs.empathy_adapter import EmpathyAdapter
        from memdocs.schemas import (
            DocumentIndex,
            ImpactSummary,
            ReferenceSummary,
            ScopeInfo,
            ScopeLevel,
        )

        memdocs_root = tmp_path / ".memdocs"
        adapter = EmpathyAdapter(memdocs_root)

        file_path = Path("src/test.py")
        doc_index = DocumentIndex(
            commit="abc123",
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            scope=ScopeInfo(paths=[file_path], level=ScopeLevel.FILE, file_count=1),
            features=[],
            impacts=ImpactSummary(),
            refs=ReferenceSummary(),
        )

        adapter._write_index_json(doc_index, file_path)

        # Verify file was created
        output_file = memdocs_root / "docs" / "test" / "index.json"
        assert output_file.exists()

        # Verify contents
        with open(output_file, "r") as f:
            data = json.load(f)

        assert data["commit"] == "abc123"
        assert "scope" in data

    @patch("memdocs.empathy_adapter.MemoryIndexer")
    def test_write_summary_md(self, mock_indexer_class, tmp_path: Path):
        """Test writing summary.md file."""
        from memdocs.empathy_adapter import EmpathyAdapter
        from memdocs.schemas import (
            DocumentIndex,
            FeatureSummary,
            ImpactSummary,
            ReferenceSummary,
            ScopeInfo,
            ScopeLevel,
        )

        memdocs_root = tmp_path / ".memdocs"
        adapter = EmpathyAdapter(memdocs_root)

        file_path = Path("src/test.py")
        doc_index = DocumentIndex(
            commit="abc123",
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            scope=ScopeInfo(paths=[file_path], level=ScopeLevel.FILE, file_count=1),
            features=[
                FeatureSummary(
                    id="feat-001",
                    title="Test Feature",
                    description="Test description",
                    risk=["high"],
                    tags=["security"],
                )
            ],
            impacts=ImpactSummary(
                apis=["API1"],
                breaking_changes=["Breaking change"],
                tests_modified=2,
                migration_required=True,
            ),
            refs=ReferenceSummary(pr=42, issues=[1, 2], files_changed=[file_path]),
        )

        analysis_results = {
            "severity_score": 75,
            "current_issues": [{"message": "Issue 1"}],
            "predictions": [
                {
                    "title": "Future issue",
                    "timeframe": "6 months",
                    "confidence": "high",
                    "impact": "medium",
                    "description": "Will happen",
                    "recommendation": "Prepare now",
                }
            ],
        }

        adapter._write_summary_md(doc_index, analysis_results, file_path)

        # Verify file was created
        output_file = memdocs_root / "docs" / "test" / "summary.md"
        assert output_file.exists()

        # Verify contents
        content = output_file.read_text()
        assert "# Empathy Analysis: test.py" in content
        assert "abc123" in content
        assert "Test Feature" in content
        assert "## Predictions" in content
        assert "Future issue" in content
        assert "PR:** #42" in content

    @patch("memdocs.empathy_adapter.MemoryIndexer")
    def test_write_symbols_yaml_extraction_error(self, mock_indexer_class, tmp_path: Path):
        """Test writing symbols.yaml when extraction fails."""
        from memdocs.empathy_adapter import EmpathyAdapter

        memdocs_root = tmp_path / ".memdocs"
        adapter = EmpathyAdapter(memdocs_root)

        file_path = tmp_path / "nonexistent.py"
        analysis_results = {}

        # Should not raise, even if file doesn't exist
        adapter._write_symbols_yaml(analysis_results, file_path)

        output_file = memdocs_root / "docs" / "nonexistent" / "symbols.yaml"
        assert output_file.exists()

        with open(output_file, "r") as f:
            data = yaml.safe_load(f)

        assert data["symbols"] == []

    @patch("memdocs.empathy_adapter.MemoryIndexer")
    def test_store_empathy_analysis(self, mock_indexer_class, tmp_path: Path):
        """Test full store_empathy_analysis flow."""
        from memdocs.empathy_adapter import EmpathyAdapter

        mock_indexer = Mock()
        mock_indexer.index_document.return_value = {"indexed": True}
        mock_indexer_class.return_value = mock_indexer

        memdocs_root = tmp_path / ".memdocs"
        adapter = EmpathyAdapter(memdocs_root)

        file_path = tmp_path / "test.py"
        file_path.write_text("def test(): pass")

        analysis_results = {
            "current_issues": [
                {
                    "message": "Critical issue",
                    "severity": "critical",
                    "type": "security",
                    "layer": "rules",
                }
            ],
            "predictions": [],
            "severity_score": 80,
        }

        doc_index = adapter.store_empathy_analysis(
            analysis_results,
            file_path,
            commit="abc123",
            pr_number=42,
            issues=[1, 2],
        )

        # Verify doc_index was created
        assert doc_index.commit == "abc123"
        assert doc_index.refs.pr == 42
        assert doc_index.refs.issues == [1, 2]
        assert len(doc_index.features) == 1
        assert doc_index.features[0].title == "Critical issue"

        # Verify files were created
        file_dir = memdocs_root / "docs" / "test"
        assert (file_dir / "index.json").exists()
        assert (file_dir / "summary.md").exists()
        assert (file_dir / "symbols.yaml").exists()

        # Verify memory indexer was called
        mock_indexer.index_document.assert_called_once()

    @patch("memdocs.empathy_adapter.MemoryIndexer")
    def test_update_memory_index_error_handling(self, mock_indexer_class, tmp_path: Path):
        """Test that memory index errors are handled gracefully."""
        from memdocs.empathy_adapter import EmpathyAdapter
        from memdocs.schemas import (
            DocumentIndex,
            ImpactSummary,
            ReferenceSummary,
            ScopeInfo,
            ScopeLevel,
        )

        mock_indexer = Mock()
        mock_indexer.index_document.side_effect = Exception("Indexing failed")
        mock_indexer_class.return_value = mock_indexer

        adapter = EmpathyAdapter(tmp_path / ".memdocs")

        file_path = Path("test.py")
        doc_index = DocumentIndex(
            commit="abc123",
            timestamp=datetime(2024, 1, 1),
            scope=ScopeInfo(paths=[file_path], level=ScopeLevel.FILE, file_count=1),
            features=[],
            impacts=ImpactSummary(),
            refs=ReferenceSummary(),
        )

        analysis_results = {"current_issues": []}

        # Should not raise even if indexing fails
        adapter._update_memory_index(doc_index, analysis_results, file_path)


class TestAdaptEmpathyToMemdocs:
    """Test convenience function."""

    @patch("memdocs.empathy_adapter.EmpathyAdapter")
    def test_adapt_empathy_to_memdocs(self, mock_adapter_class, tmp_path: Path):
        """Test convenience function."""
        from memdocs.empathy_adapter import adapt_empathy_to_memdocs

        mock_adapter = Mock()
        mock_doc_index = Mock()
        mock_adapter.store_empathy_analysis.return_value = mock_doc_index
        mock_adapter_class.return_value = mock_adapter

        analysis_results = {"current_issues": []}
        file_path = "test.py"
        memdocs_root = tmp_path / ".memdocs"

        result = adapt_empathy_to_memdocs(
            analysis_results,
            file_path,
            memdocs_root=memdocs_root,
            commit="abc123",
            pr_number=42,
        )

        assert result == mock_doc_index
        mock_adapter_class.assert_called_once_with(memdocs_root)
        mock_adapter.store_empathy_analysis.assert_called_once_with(
            analysis_results, file_path, commit="abc123", pr_number=42
        )
