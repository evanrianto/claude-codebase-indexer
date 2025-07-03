#!/usr/bin/env python3
"""
Standalone search CLI for quick queries
"""

import argparse
import sys
from pathlib import Path

from src.search.engine import SemanticSearchEngine

def main():
    """Quick search CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Quick semantic search of indexed codebase'
    )
    
    parser.add_argument('query', nargs='?', help='Search query')
    parser.add_argument('--index-path', default='./claude_index',
                       help='Path to index directory')
    parser.add_argument('--top-k', type=int, default=5,
                       help='Number of results')
    parser.add_argument('--file-types', nargs='+',
                       help='Filter by file extensions (py, js, etc.)')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Interactive mode')
    parser.add_argument('--score-threshold', type=float, default=0.0,
                       help='Minimum relevance score')
    parser.add_argument('--format', choices=['claude', 'simple'], default='claude',
                       help='Output format')
    
    args = parser.parse_args()
    
    # Check if index exists
    if not Path(args.index_path).exists():
        print(f"❌ Index not found at {args.index_path}")
        print("Run 'python -m src.cli.main index <project_path>' first")
        sys.exit(1)
    
    engine = SemanticSearchEngine(args.index_path)
    
    if args.interactive or not args.query:
        engine.interactive_search()
    else:
        if not engine.load_index():
            print("❌ Could not load search index")
            sys.exit(1)
        
        # Perform search
        if args.file_types:
            file_types = [f".{ext}" if not ext.startswith('.') else ext 
                         for ext in args.file_types]
            results = engine.search_by_file_type(
                args.query, file_types, args.top_k
            )
        else:
            results = engine.search(
                args.query, args.top_k, args.score_threshold
            )
        
        # Display results
        if not results:
            print(f"❌ No results found for: '{args.query}'")
            sys.exit(1)
        
        if args.format == 'claude':
            output = engine.format_for_claude(results, args.query)
            print(output)
        else:
            print(f"Results for: '{args.query}'\n")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['file_path']} (score: {result.get('score', 0):.3f})")
                print(f"   {result['content'][:100]}...")
                print()

if __name__ == "__main__":
    main()