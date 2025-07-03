#!/usr/bin/env python3
"""
Semantic codebase indexer for Claude Code integration
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Document, load_index_from_storage
from llama_index.core.node_parser import CodeSplitter
from llama_index.vector_stores.faiss import FaissVectorStore
from llama_index.core.storage.storage_context import StorageContext
from llama_index.embeddings.openai import OpenAIEmbedding
import faiss
import pandas as pd

logger = logging.getLogger(__name__)

class CodebaseIndexer:
    """Semantic indexer for code repositories"""
    
    def __init__(self, project_path: str, index_path: str = "./claude_index"):
        self.project_path = Path(project_path)
        self.index_path = Path(index_path)
        self.supported_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', 
            '.h', '.hpp', '.cs', '.php', '.rb', '.go', '.rs', '.swift',
            '.kt', '.scala', '.sh', '.sql', '.yaml', '.yml', '.json',
            '.md', '.txt', '.rst', '.toml', '.cfg', '.ini'
        }
        
        # Directories to skip during indexing
        self.skip_dirs = {
            'node_modules', '.git', '__pycache__', '.pytest_cache',
            'venv', 'env', '.venv', 'dist', 'build', '.next',
            'target', 'bin', 'obj', '.mypy_cache', 'coverage',
            '.tox', '.nox', 'htmlcov'
        }
        
    def should_index_file(self, file_path: Path) -> bool:
        """Determine if a file should be indexed"""
        if file_path.suffix.lower() not in self.supported_extensions:
            return False
            
        # Check if any parent directory should be skipped
        if any(part in self.skip_dirs for part in file_path.parts):
            return False
            
        # Skip very large files (>1MB)
        try:
            if file_path.stat().st_size > 1024 * 1024:
                logger.warning(f"Skipping large file: {file_path}")
                return False
        except OSError:
            return False
            
        return True
    
    def load_documents(self) -> List[Document]:
        """Load and filter documents from the project"""
        documents = []
        
        logger.info(f"Scanning project directory: {self.project_path}")
        
        for file_path in self.project_path.rglob('*'):
            if file_path.is_file() and self.should_index_file(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    # Skip empty files
                    if not content.strip():
                        continue
                        
                    # Create relative path for metadata
                    rel_path = file_path.relative_to(self.project_path)
                    
                    doc = Document(
                        text=content,
                        metadata={
                            'file_path': str(rel_path),
                            'file_type': file_path.suffix,
                            'file_name': file_path.name,
                            'file_size': len(content)
                        }
                    )
                    documents.append(doc)
                    
                except Exception as e:
                    logger.warning(f"Could not read {file_path}: {e}")
                    
        logger.info(f"Loaded {len(documents)} documents")
        return documents
    
    def create_index(self, embedding_model: str = "text-embedding-ada-002", use_dummy: bool = False) -> VectorStoreIndex:
        """Create and persist the vector index"""
        logger.info(f"Creating index for {self.project_path}")
        
        documents = self.load_documents()
        if not documents:
            raise ValueError("No documents found to index")
        
        # Use simple text splitter for reliability
        from llama_index.core.node_parser import SimpleNodeParser
        splitter = SimpleNodeParser.from_defaults(
            chunk_size=1000,
            chunk_overlap=100
        )
        
        nodes = splitter.get_nodes_from_documents(documents)
        logger.info(f"Created {len(nodes)} semantic chunks")
        
        # Set up embedding model
        if use_dummy:
            from .dummy_embedder import DummyEmbedding
            embed_model = DummyEmbedding()
            dimension = 384  # Dummy embedding dimension
        else:
            embed_model = OpenAIEmbedding(model=embedding_model)
            dimension = 1536  # OpenAI embedding dimension
        
        # Create vector store (use simple storage for testing)
        if use_dummy:
            # Use in-memory storage for dummy embedder
            storage_context = StorageContext.from_defaults()
        else:
            # Use FAISS for production
            faiss_index = faiss.IndexFlatL2(dimension)
            vector_store = FaissVectorStore(faiss_index=faiss_index)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        # Build index
        logger.info("Building vector index...")
        index = VectorStoreIndex(
            nodes, 
            storage_context=storage_context,
            embed_model=embed_model
        )
        
        # Create index directory
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        # Persist index
        index.storage_context.persist(persist_dir=str(self.index_path))
        
        # Save metadata
        metadata = {
            'project_path': str(self.project_path),
            'index_path': str(self.index_path),
            'num_documents': len(documents),
            'num_chunks': len(nodes),
            'supported_extensions': list(self.supported_extensions),
            'embedding_model': embedding_model if not use_dummy else 'dummy',
            'embedding_dimension': dimension,
            'use_dummy': use_dummy,
            'created_at': str(pd.Timestamp.now())
        }
        
        with open(self.index_path / 'metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Index created successfully at {self.index_path}")
        return index
    
    def update_index(self, force: bool = False) -> VectorStoreIndex:
        """Update existing index or create new one"""
        if self.index_path.exists() and not force:
            logger.info("Index already exists. Use force=True to recreate.")
            return self.load_existing_index()
        
        return self.create_index()
    
    def load_existing_index(self) -> Optional[VectorStoreIndex]:
        """Load an existing index from disk"""
        if not self.index_path.exists():
            return None
            
        try:
            storage_context = StorageContext.from_defaults(
                persist_dir=str(self.index_path)
            )
            index = load_index_from_storage(storage_context)
            logger.info(f"Loaded existing index from {self.index_path}")
            return index
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return None