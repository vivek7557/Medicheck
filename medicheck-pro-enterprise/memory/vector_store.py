"""
Vector Store for Medical Embeddings
This module handles vector embeddings for medical data
"""
import asyncio
import numpy as np
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod


class VectorStore(ABC):
    """Abstract base class for vector stores"""
    
    @abstractmethod
    async def store_embedding(self, id: str, embedding: List[float], metadata: Dict[str, Any]) -> bool:
        """Store an embedding with metadata"""
        pass
    
    @abstractmethod
    async def search_similar(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar embeddings"""
        pass
    
    @abstractmethod
    async def delete_embedding(self, id: str) -> bool:
        """Delete an embedding by ID"""
        pass


class MedicalVectorStore(VectorStore):
    """Implementation of vector store for medical data"""
    
    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        self.embeddings: Dict[str, np.ndarray] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}
    
    async def store_embedding(self, id: str, embedding: List[float], metadata: Dict[str, Any]) -> bool:
        """Store embedding in memory"""
        if len(embedding) != self.dimension:
            raise ValueError(f"Embedding dimension mismatch. Expected {self.dimension}, got {len(embedding)}")
        
        self.embeddings[id] = np.array(embedding)
        self.metadata[id] = metadata
        return True
    
    async def search_similar(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Find similar embeddings using cosine similarity"""
        if len(query_embedding) != self.dimension:
            raise ValueError(f"Query embedding dimension mismatch. Expected {self.dimension}, got {len(query_embedding)}")
        
        query_vec = np.array(query_embedding)
        similarities = []
        
        for id, embedding in self.embeddings.items():
            # Calculate cosine similarity
            similarity = np.dot(query_vec, embedding) / (np.linalg.norm(query_vec) * np.linalg.norm(embedding))
            similarities.append({
                'id': id,
                'similarity': float(similarity),
                'metadata': self.metadata[id]
            })
        
        # Sort by similarity (descending) and return top_k
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:top_k]
    
    async def delete_embedding(self, id: str) -> bool:
        """Delete embedding by ID"""
        if id in self.embeddings:
            del self.embeddings[id]
            if id in self.metadata:
                del self.metadata[id]
            return True
        return False
    
    async def batch_store(self, embeddings_data: List[Dict[str, Any]]) -> bool:
        """Store multiple embeddings at once"""
        for data in embeddings_data:
            await self.store_embedding(
                data['id'], 
                data['embedding'], 
                data.get('metadata', {})
            )
        return True