"""
Claude Codebase Indexer

A semantic search system that enhances Claude Code with intelligent codebase understanding.
"""

__version__ = "0.1.0"
__author__ = "Claude Codebase Indexer Team"

from .indexer.core import CodebaseIndexer
from .search.engine import SemanticSearchEngine
from .integration.claude import ClaudeCodeIntegration

__all__ = [
    "CodebaseIndexer",
    "SemanticSearchEngine", 
    "ClaudeCodeIntegration"
]