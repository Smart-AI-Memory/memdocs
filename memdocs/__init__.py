"""
Doc-Intelligence: Lightweight documentation system for AI-powered memory.

Generate machine-friendly docs from code changes without bureaucratic overhead.
"""

__version__ = "2.0.0"
__author__ = "Patrick Roebuck"
__license__ = "Apache-2.0"

from memdocs.schemas import (
    DocIntConfig,
    ReviewResult,
    DocumentIndex,
    Symbol,
    FeatureSummary,
)

__all__ = [
    "__version__",
    "DocIntConfig",
    "ReviewResult",
    "DocumentIndex",
    "Symbol",
    "FeatureSummary",
]
