#!/usr/bin/env python3
"""
Dummy embedder for testing without OpenAI API
"""

import numpy as np
from llama_index.core.embeddings import BaseEmbedding

class DummyEmbedding(BaseEmbedding):
    """Simple dummy embedder for testing without requiring external APIs"""
    
    def _get_text_embedding(self, text: str) -> list[float]:
        # Create a simple hash-based embedding with fixed dimension
        hash_val = hash(text)
        np.random.seed(abs(hash_val) % (2**32))
        embedding = np.random.normal(0, 1, 384)  # Fixed dimension
        return embedding.tolist()
    
    def _get_query_embedding(self, query: str) -> list[float]:
        return self._get_text_embedding(query)
    
    async def _aget_query_embedding(self, query: str) -> list[float]:
        return self._get_text_embedding(query)
    
    async def _aget_text_embedding(self, text: str) -> list[float]:
        return self._get_text_embedding(text)