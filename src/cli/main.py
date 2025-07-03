#!/usr/bin/env python3
"""
Main CLI interface for Claude Codebase Indexer
"""

import argparse
import sys
import logging
from pathlib import Path

from src.indexer.core import CodebaseIndexer
from src.search.engine import SemanticSearchEngine
from src.integration.claude import ClaudeCodeIntegration

def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def cmd_index(args):
    """Index a codebase"""
    setup_logging(args.verbose)
    
    indexer = CodebaseIndexer(args.project_path, args.index_path)
    
    if args.force or not Path(args.index_path).exists():
        print(f"🚀 Indexing codebase: {args.project_path}")
        if hasattr(args, 'dummy') and args.dummy:
            print("🧪 Using dummy embedder for testing")
            indexer.create_index(use_dummy=True)
        else:
            indexer.create_index()
        print("✅ Indexing complete!")
    else:
        print(f"ℹ️  Index already exists at {args.index_path}")
        print("   Use --force to recreate or run 'update' command")

def cmd_search(args):
    """Search the indexed codebase"""
    setup_logging(args.verbose)
    
    if args.interactive:
        engine = SemanticSearchEngine(args.index_path)
        engine.interactive_search()
    else:
        integration = ClaudeCodeIntegration(args.index_path)
        
        if args.file_types:
            file_types = [f".{ext}" if not ext.startswith('.') else ext 
                         for ext in args.file_types]
        else:
            file_types = None
            
        integration.search_and_show(args.query, args.top_k, file_types)

def cmd_claude(args):
    """Run Claude Code with semantic context"""
    setup_logging(args.verbose)
    
    integration = ClaudeCodeIntegration(args.index_path)
    
    # Prepare file types
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

def cmd_stats(args):
    """Show index statistics"""
    setup_logging(args.verbose)
    
    integration = ClaudeCodeIntegration(args.index_path)
    integration.show_stats()

def cmd_similar(args):
    """Find similar files"""
    setup_logging(args.verbose)
    
    integration = ClaudeCodeIntegration(args.index_path)
    similar = integration.find_similar_files(args.file_path, args.top_k)
    
    if similar:
        print(f"📁 Files similar to {args.file_path}:")
        for i, f in enumerate(similar, 1):
            print(f"  {i}. {f}")
    else:
        print(f"❌ No similar files found for: {args.file_path}")

def cmd_update(args):
    """Update existing index"""
    setup_logging(args.verbose)
    
    indexer = CodebaseIndexer(args.project_path, args.index_path)
    
    print(f"🔄 Updating index for: {args.project_path}")
    indexer.update_index(force=args.force)
    print("✅ Update complete!")

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Claude Codebase Indexer - Semantic search for Claude Code',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--index-path', default='./claude_index',
                       help='Path to index directory (default: ./claude_index)')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Index command
    parser_index = subparsers.add_parser('index', help='Index a codebase')
    parser_index.add_argument('project_path', help='Path to project directory')
    parser_index.add_argument('--force', action='store_true', 
                             help='Force recreate existing index')
    parser_index.add_argument('--verbose', '-v', action='store_true', 
                             help='Enable verbose logging')
    parser_index.add_argument('--dummy', action='store_true', 
                             help='Use dummy embedder for testing (no OpenAI API required)')
    parser_index.set_defaults(func=cmd_index)
    
    # Search command
    parser_search = subparsers.add_parser('search', help='Search indexed codebase')
    parser_search.add_argument('query', nargs='?', help='Search query')
    parser_search.add_argument('--top-k', type=int, default=5, 
                              help='Number of results (default: 5)')
    parser_search.add_argument('--file-types', nargs='+', 
                              help='Filter by file extensions')
    parser_search.add_argument('--interactive', '-i', action='store_true',
                              help='Interactive search mode')
    parser_search.add_argument('--verbose', '-v', action='store_true', 
                              help='Enable verbose logging')
    parser_search.set_defaults(func=cmd_search)
    
    # Claude command  
    parser_claude = subparsers.add_parser('claude', help='Run Claude Code with context')
    parser_claude.add_argument('query', help='Your question for Claude')
    parser_claude.add_argument('--context-query', help='Specific context search query')
    parser_claude.add_argument('--top-k', type=int, default=3,
                              help='Number of context chunks (default: 3)')
    parser_claude.add_argument('--file-types', nargs='+',
                              help='Filter context by file extensions')
    parser_claude.add_argument('--claude-args', nargs='*',
                              help='Additional Claude Code arguments')
    parser_claude.add_argument('--interactive', action='store_true',
                              help='Run Claude in interactive mode')
    parser_claude.add_argument('--verbose', '-v', action='store_true', 
                              help='Enable verbose logging')
    parser_claude.set_defaults(func=cmd_claude)
    
    # Stats command
    parser_stats = subparsers.add_parser('stats', help='Show index statistics')
    parser_stats.add_argument('--verbose', '-v', action='store_true', 
                             help='Enable verbose logging')
    parser_stats.set_defaults(func=cmd_stats)
    
    # Similar command
    parser_similar = subparsers.add_parser('similar', help='Find similar files')
    parser_similar.add_argument('file_path', help='File to find similarities for')
    parser_similar.add_argument('--top-k', type=int, default=5,
                               help='Number of similar files (default: 5)')
    parser_similar.add_argument('--verbose', '-v', action='store_true', 
                               help='Enable verbose logging')
    parser_similar.set_defaults(func=cmd_similar)
    
    # Update command
    parser_update = subparsers.add_parser('update', help='Update existing index')
    parser_update.add_argument('project_path', help='Path to project directory')
    parser_update.add_argument('--force', action='store_true',
                              help='Force full reindex')
    parser_update.add_argument('--verbose', '-v', action='store_true', 
                              help='Enable verbose logging')
    parser_update.set_defaults(func=cmd_update)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not hasattr(args, 'func'):
        parser.print_help()
        sys.exit(1)
    
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        if hasattr(args, 'verbose') and args.verbose:
            raise
        else:
            print(f"❌ Error: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()