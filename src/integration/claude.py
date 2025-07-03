#!/usr/bin/env python3
"""
Claude Code integration with semantic context injection
"""

import subprocess
import tempfile
import argparse
import sys
import logging
import select
from pathlib import Path
from typing import List, Optional, Dict, Any

from src.search.engine import SemanticSearchEngine

logger = logging.getLogger(__name__)


class ClaudeCodeIntegration:
    """Enhanced Claude Code with semantic context"""

    def __init__(self, index_path: str = "./claude_index"):
        self.search_engine = SemanticSearchEngine(index_path)

    def run_with_context(self,
                         user_query: str,
                         context_query: Optional[str] = None,
                         top_k: int = 3,
                         file_types: Optional[List[str]] = None,
                         claude_args: Optional[List[str]] = None,
                         interactive: bool = False) -> None:
        """Run Claude Code with semantic context"""

        # Load search index
        if not self.search_engine.load_index():
            print("❌ Could not load search index. Run indexer first.")
            sys.exit(1)

        # Use user query for context if no specific context query provided
        search_query = context_query or user_query

        print(f"🔍 Searching for context: '{search_query}'")

        # Get relevant context based on file types
        if file_types:
            results = self.search_engine.search_by_file_type(
                search_query, file_types, top_k)
        else:
            results = self.search_engine.search(search_query, top_k)

        if not results:
            print(f"⚠️  No relevant context found for '{search_query}'")
            print("Running Claude Code without additional context...")
            context = ""
        else:
            context = self.search_engine.format_for_claude(
                results, search_query)
            print(f"✅ Found {len(results)} relevant code sections")

        # Prepare the enhanced prompt
        if context:
            enhanced_prompt = f"""Here's relevant context from the codebase:

{context}

---

User Request: {user_query}

Please help with the above request using the provided codebase context."""
        else:
            enhanced_prompt = user_query

        if interactive:
            self._run_interactive_claude(enhanced_prompt, claude_args)
        else:
            self._run_claude_with_file(enhanced_prompt, claude_args)

    def _run_claude_with_file(self, prompt: str, claude_args: Optional[List[str]] = None) -> None:
        """Run Claude Code with enhanced prompt"""
        try:
            # Prepare Claude Code command
            cmd = ['claude']
            if claude_args:
                cmd.extend(claude_args)
            # Add --print for non-interactive mode
            cmd.extend(['--print', prompt])

            print(f"🤖 Running Claude Code with context...")
            result = subprocess.run(cmd, capture_output=False)
            sys.exit(result.returncode)

        except Exception as e:
            logger.error(f"Error running Claude Code: {e}")
            print(f"❌ Error running Claude Code: {e}")
            sys.exit(1)

    def _run_interactive_claude(self, initial_prompt: str, claude_args: Optional[List[str]] = None) -> None:
        """Run Claude Code in interactive mode with initial context"""
        print("🤖 Starting Claude Code in interactive mode...")
        print("📋 Initial context has been prepared.")
        print(f"💬 Your query: {initial_prompt[:100]}{'...' if len(initial_prompt) > 100 else ''}")
        print("-" * 60)

        # For interactive mode, we'll start Claude normally and the user can paste the context
        print("ℹ️  Claude Code will start. You can paste this context into the conversation:")
        print("=" * 60)
        print(initial_prompt)
        print("=" * 60)
        
        # Prepare Claude Code command for interactive mode
        cmd = ['claude']
        if claude_args:
            cmd.extend(claude_args)

        try:
            # Run Claude Code interactively
            result = subprocess.run(cmd, capture_output=False)
            sys.exit(result.returncode)
        except Exception as e:
            logger.error(f"Error running interactive Claude: {e}")
            print(f"❌ Error: {e}")

    def search_and_show(self, query: str, top_k: int = 5, file_types: Optional[List[str]] = None) -> None:
        """Search and display results without running Claude"""
        if not self.search_engine.load_index():
            print("❌ Could not load search index")
            return

        print(f"🔍 Searching for: '{query}'")

        if file_types:
            results = self.search_engine.search_by_file_type(
                query, file_types, top_k)
        else:
            results = self.search_engine.search(query, top_k)

        if results:
            formatted = self.search_engine.format_for_claude(results, query)
            print("\n" + "="*60)
            print("📋 Search Results:")
            print("="*60)
            print(formatted)
            print("="*60)
        else:
            print(f"❌ No results found for: '{query}'")

    def get_file_context(self, file_path: str) -> Optional[str]:
        """Get context for a specific file"""
        if not self.search_engine.load_index():
            return None

        summary = self.search_engine.get_file_summary(file_path)
        if not summary:
            return None

        return f"""# File Context: {file_path}

**File Type:** {summary['file_type']}
**Total Chunks:** {summary['total_chunks']}

## Content Preview:
```{summary['file_type'].lstrip('.')}
{summary['content_preview']}
```
"""

    def find_similar_files(self, file_path: str, top_k: int = 5) -> List[str]:
        """Find files similar to the given file"""
        if not self.search_engine.load_index():
            return []

        return self.search_engine.get_similar_files(file_path, top_k)

    def show_stats(self) -> None:
        """Display index statistics"""
        if not self.search_engine.load_index():
            print("❌ Could not load search index")
            return

        stats = self.search_engine.get_index_stats()

        print("📊 Index Statistics:")
        print(f"  Project: {stats.get('project_path', 'Unknown')}")
        print(f"  Documents: {stats.get('num_documents', 0)}")
        print(f"  Chunks: {stats.get('num_chunks', 0)}")
        print(f"  Embedding Model: {stats.get('embedding_model', 'Unknown')}")
        print(f"  Created: {stats.get('created_at', 'Unknown')}")
        print(
            f"  Extensions: {', '.join(stats.get('supported_extensions', []))}")


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Run Claude Code with semantic context',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with context
  python claude.py "How does authentication work?"
  
  # Search specific file types
  python claude.py "database queries" --file-types py sql
  
  # Use different context query
  python claude.py "Add error handling" --context-query "error handling patterns"
  
  # Just search without running Claude
  python claude.py "login function" --search-only
  
  # Show file context
  python claude.py --file-context src/auth.py
  
  # Find similar files
  python claude.py --similar-files src/models/user.py
        """
    )

    parser.add_argument('query', nargs='?',
                        help='Your question/request for Claude')
    parser.add_argument('--context-query',
                        help='Specific query for context search')
    parser.add_argument('--index-path', default='./claude_index',
                        help='Path to index directory')
    parser.add_argument('--top-k', type=int, default=3,
                        help='Number of context chunks')
    parser.add_argument('--file-types', nargs='+',
                        help='Filter by file extensions (e.g., py js)')
    parser.add_argument('--claude-args', nargs='*',
                        help='Additional Claude Code arguments')
    parser.add_argument('--search-only', action='store_true',
                        help='Search without running Claude')
    parser.add_argument('--interactive', action='store_true',
                        help='Run Claude in interactive mode')
    parser.add_argument(
        '--file-context', help='Show context for specific file')
    parser.add_argument('--similar-files',
                        help='Find files similar to given file')
    parser.add_argument('--stats', action='store_true',
                        help='Show index statistics')
    parser.add_argument('--verbose', '-v',
                        action='store_true', help='Verbose logging')

    args = parser.parse_args()

    # Setup logging
    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    # Create integration instance
    integration = ClaudeCodeIntegration(args.index_path)

    # Handle different modes
    if args.stats:
        integration.show_stats()
    elif args.file_context:
        context = integration.get_file_context(args.file_context)
        if context:
            print(context)
        else:
            print(f"❌ No context found for file: {args.file_context}")
    elif args.similar_files:
        similar = integration.find_similar_files(args.similar_files)
        if similar:
            print(f"📁 Files similar to {args.similar_files}:")
            for i, f in enumerate(similar, 1):
                print(f"  {i}. {f}")
        else:
            print(f"❌ No similar files found for: {args.similar_files}")
    elif args.query:
        if args.search_only:
            integration.search_and_show(
                args.query,
                args.top_k,
                args.file_types
            )
        else:
            # Prepare file types with dots
            file_types = None
            if args.file_types:
                file_types = [f".{ext}" if not ext.startswith('.') else ext
                              for ext in args.file_types]

            integration.run_with_context(
                user_query=args.query,
                context_query=args.context_query,
                top_k=args.top_k,
                file_types=file_types,
                claude_args=args.claude_args,
                interactive=args.interactive
            )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
