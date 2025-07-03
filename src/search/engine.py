#!/usr/bin/env python3
"""
Semantic search engine for Claude Code integration
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any

from llama_index.core import load_index_from_storage
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.schema import NodeWithScore

logger = logging.getLogger(__name__)

class SemanticSearchEngine:
    """Semantic search engine for code repositories"""
    
    def __init__(self, index_path: str = "./claude_index"):
        self.index_path = Path(index_path)
        self.index = None
        self.metadata = None
        
    def load_index(self) -> bool:
        """Load the persisted index and metadata"""
        if not self.index_path.exists():
            logger.error(f"Index not found at {self.index_path}")
            return False
            
        try:
            # Load metadata
            metadata_path = self.index_path / 'metadata.json'
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    self.metadata = json.load(f)
            
            # Set up embedding model based on metadata
            embed_model = None
            if self.metadata and self.metadata.get('use_dummy', False):
                from src.indexer.dummy_embedder import DummyEmbedding
                embed_model = DummyEmbedding()
            
            # Load index
            storage_context = StorageContext.from_defaults(
                persist_dir=str(self.index_path)
            )
            
            if embed_model:
                self.index = load_index_from_storage(storage_context, embed_model=embed_model)
            else:
                self.index = load_index_from_storage(storage_context)
            
            logger.info(f"Loaded index from {self.index_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return False
    
    def search(self, query: str, top_k: int = 5, score_threshold: float = 0.0) -> List[Dict[str, Any]]:
        """Search for relevant code chunks"""
        if not self.index:
            if not self.load_index():
                raise RuntimeError("Could not load search index")
        
        # Get retriever
        retriever = self.index.as_retriever(
            similarity_top_k=top_k,
            score_threshold=score_threshold
        )
        
        # Retrieve relevant nodes
        nodes = retriever.retrieve(query)
        
        # Format results
        results = []
        for i, node in enumerate(nodes):
            metadata = node.metadata or {}
            
            result = {
                'rank': i + 1,
                'score': getattr(node, 'score', 0.0),
                'content': node.text,
                'file_path': metadata.get('file_path', 'unknown'),
                'file_type': metadata.get('file_type', ''),
                'file_name': metadata.get('file_name', ''),
                'file_size': metadata.get('file_size', 0)
            }
            results.append(result)
        
        return results
    
    def search_by_file_type(self, query: str, file_extensions: List[str], 
                           top_k: int = 5) -> List[Dict[str, Any]]:
        """Search within specific file types"""
        all_results = self.search(query, top_k * 2)  # Get more to filter
        
        # Filter by file extensions
        filtered_results = [
            result for result in all_results
            if result['file_type'].lower() in [ext.lower() for ext in file_extensions]
        ]
        
        return filtered_results[:top_k]
    
    def format_for_claude(self, results: List[Dict[str, Any]], query: str) -> str:
        """Format search results for Claude Code consumption"""
        if not results:
            return f"# No results found for: '{query}'"
        
        output_lines = [
            f"# Semantic Search Results for: '{query}'",
            f"Found {len(results)} relevant code sections:\n"
        ]
        
        for result in results:
            file_path = result['file_path']
            file_type = result['file_type'].lstrip('.')
            score = result.get('score', 0.0)
            
            output_lines.extend([
                f"## Result {result['rank']}: {file_path}",
                f"*Relevance Score: {score:.3f}*\n",
                f"```{file_type}",
                result['content'],
                "```\n"
            ])
        
        return "\n".join(output_lines)
    
    def get_file_summary(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get summary information about a specific file"""
        if not self.index:
            if not self.load_index():
                return None
        
        # Search for content from specific file
        results = self.search(f"file:{file_path}", top_k=20)
        
        if not results:
            return None
        
        # Aggregate information about the file
        total_chunks = len([r for r in results if r['file_path'] == file_path])
        file_content = "\n".join([r['content'] for r in results if r['file_path'] == file_path])
        
        return {
            'file_path': file_path,
            'total_chunks': total_chunks,
            'content_preview': file_content[:1000] + "..." if len(file_content) > 1000 else file_content,
            'file_type': results[0]['file_type'] if results else 'unknown'
        }
    
    def get_similar_files(self, file_path: str, top_k: int = 5) -> List[str]:
        """Find files similar to the given file"""
        # Get content from the target file
        file_summary = self.get_file_summary(file_path)
        
        if not file_summary:
            return []
        
        # Search using the file's content
        preview = file_summary['content_preview']
        results = self.search(preview, top_k * 2)
        
        # Extract unique file paths, excluding the original
        similar_files = []
        seen_files = {file_path}
        
        for result in results:
            result_file = result['file_path']
            if result_file not in seen_files:
                similar_files.append(result_file)
                seen_files.add(result_file)
                
            if len(similar_files) >= top_k:
                break
        
        return similar_files
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the loaded index"""
        if not self.metadata:
            return {}
        
        return {
            'project_path': self.metadata.get('project_path'),
            'num_documents': self.metadata.get('num_documents', 0),
            'num_chunks': self.metadata.get('num_chunks', 0),
            'supported_extensions': self.metadata.get('supported_extensions', []),
            'created_at': self.metadata.get('created_at'),
            'embedding_model': self.metadata.get('embedding_model')
        }
    
    def interactive_search(self):
        """Interactive search mode for testing"""
        if not self.index:
            if not self.load_index():
                print("❌ Could not load search index")
                return
        
        stats = self.get_index_stats()
        print(f"🔍 Claude Code Semantic Search")
        print(f"📁 Project: {stats.get('project_path', 'Unknown')}")
        print(f"📊 {stats.get('num_documents', 0)} files, {stats.get('num_chunks', 0)} chunks indexed")
        print("Type 'quit' to exit, 'help' for commands\n")
        
        while True:
            try:
                query = input("🤖 Search query > ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    break
                elif query.lower() == 'help':
                    print("\nCommands:")
                    print("  <query>                - Semantic search")
                    print("  file:<path>           - Search specific file")
                    print("  type:<ext> <query>    - Search by file type (e.g., 'type:py authentication')")
                    print("  similar:<path>        - Find similar files")
                    print("  stats                 - Show index statistics")
                    print("  quit                  - Exit\n")
                    continue
                elif query.lower() == 'stats':
                    stats = self.get_index_stats()
                    for key, value in stats.items():
                        print(f"  {key}: {value}")
                    print()
                    continue
                elif not query:
                    continue
                
                # Handle special commands
                if query.startswith('type:'):
                    parts = query.split(' ', 1)
                    if len(parts) == 2:
                        file_ext = parts[0].split(':', 1)[1]
                        search_query = parts[1]
                        results = self.search_by_file_type(search_query, [f".{file_ext}"])
                    else:
                        print("Usage: type:<extension> <query>")
                        continue
                elif query.startswith('similar:'):
                    file_path = query.split(':', 1)[1]
                    similar = self.get_similar_files(file_path)
                    print(f"\nSimilar files to {file_path}:")
                    for i, f in enumerate(similar, 1):
                        print(f"  {i}. {f}")
                    print()
                    continue
                else:
                    results = self.search(query)
                
                # Display results
                if results:
                    formatted = self.format_for_claude(results, query)
                    print("\n" + "="*60)
                    print("📎 Copy this to Claude Code:")
                    print("="*60)
                    print(formatted)
                    print("="*60 + "\n")
                else:
                    print(f"❌ No results found for: '{query}'\n")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}\n")