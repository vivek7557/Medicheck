from typing import Dict, Any, List, Optional
import asyncio
import uuid
from datetime import datetime
from pydantic import BaseModel
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


class Memory(BaseModel):
    """Memory model to represent a stored interaction or fact"""
    memory_id: str
    session_id: str
    agent_id: str
    content: str
    embedding: List[float]
    timestamp: datetime
    metadata: Dict[str, Any]


class MemoryBank:
    """
    Long-term memory storage with vector embeddings for similarity search.
    Uses FAISS for efficient similarity search and Sentence Transformers for embeddings.
    """
    
    def __init__(self, embedding_dim: int = 384):  # Using a smaller dimension for efficiency
        self._memories: Dict[str, Memory] = {}
        self._sessions: Dict[str, List[str]] = {}  # session_id -> list of memory_ids
        self._embedding_dim = embedding_dim
        self._index = faiss.IndexFlatIP(embedding_dim)  # Inner product for cosine similarity
        self._id_to_index: Dict[str, int] = {}  # Maps memory_id to FAISS index
        self._index_to_id: Dict[int, str] = {}  # Maps FAISS index to memory_id
        self._next_index = 0
        self._encoder = SentenceTransformer('all-MiniLM-L6-v2')  # Lightweight model
        self._lock = asyncio.Lock()
    
    async def store_interaction(self, session_id: str, agent_id: str, 
                                input_data: Dict[str, Any], output_data: Dict[str, Any]) -> str:
        """
        Store an interaction between an agent and input/output data.
        """
        async with self._lock:
            # Create content string from input and output
            content = f"Input: {str(input_data)} Output: {str(output_data)}"
            
            # Generate embedding
            embedding = self._encoder.encode([content])[0].tolist()
            
            # Normalize the embedding for cosine similarity
            embedding_np = np.array(embedding).astype('float32')
            faiss.normalize_L2(embedding_np.reshape(1, -1))
            embedding = embedding_np.tolist()[0]
            
            # Create memory
            memory_id = str(uuid.uuid4())
            memory = Memory(
                memory_id=memory_id,
                session_id=session_id,
                agent_id=agent_id,
                content=content,
                embedding=embedding,
                timestamp=datetime.utcnow(),
                metadata={
                    "input_data": input_data,
                    "output_data": output_data,
                    "interaction_type": "agent_interaction"
                }
            )
            
            # Store in memory bank
            self._memories[memory_id] = memory
            
            # Add to session index
            if session_id not in self._sessions:
                self._sessions[session_id] = []
            self._sessions[session_id].append(memory_id)
            
            # Add to FAISS index
            embedding_array = np.array([memory.embedding]).astype('float32')
            self._index.add(embedding_array)
            
            # Update ID mappings
            self._id_to_index[memory_id] = self._next_index
            self._index_to_id[self._next_index] = memory_id
            self._next_index += 1
            
            return memory_id
    
    async def store_fact(self, session_id: str, agent_id: str, 
                         fact: str, metadata: Dict[str, Any] = None) -> str:
        """
        Store a fact or piece of knowledge.
        """
        async with self._lock:
            # Generate embedding for the fact
            embedding = self._encoder.encode([fact])[0].tolist()
            
            # Normalize the embedding for cosine similarity
            embedding_np = np.array(embedding).astype('float32')
            faiss.normalize_L2(embedding_np.reshape(1, -1))
            embedding = embedding_np.tolist()[0]
            
            # Create memory
            memory_id = str(uuid.uuid4())
            memory = Memory(
                memory_id=memory_id,
                session_id=session_id,
                agent_id=agent_id,
                content=fact,
                embedding=embedding,
                timestamp=datetime.utcnow(),
                metadata=metadata or {}
            )
            
            # Store in memory bank
            self._memories[memory_id] = memory
            
            # Add to session index
            if session_id not in self._sessions:
                self._sessions[session_id] = []
            self._sessions[session_id].append(memory_id)
            
            # Add to FAISS index
            embedding_array = np.array([memory.embedding]).astype('float32')
            self._index.add(embedding_array)
            
            # Update ID mappings
            self._id_to_index[memory_id] = self._next_index
            self._index_to_id[self._next_index] = memory_id
            self._next_index += 1
            
            return memory_id
    
    async def search_similar(self, query: str, session_id: str = None, 
                            limit: int = 5) -> List[Memory]:
        """
        Search for memories similar to the query.
        """
        async with self._lock:
            if self._index.ntotal == 0:
                return []
            
            # Generate embedding for query
            query_embedding = self._encoder.encode([query])[0].tolist()
            
            # Normalize the embedding for cosine similarity
            query_embedding_np = np.array(query_embedding).astype('float32')
            faiss.normalize_L2(query_embedding_np.reshape(1, -1))
            query_embedding = query_embedding_np.tolist()[0]
            
            # Search in FAISS
            query_array = np.array([query_embedding]).astype('float32')
            scores, indices = self._index.search(query_array, min(limit * 2, self._index.ntotal))
            
            # Get memory IDs from indices
            similar_memory_ids = []
            for idx in indices[0]:
                if idx in self._index_to_id:
                    memory_id = self._index_to_id[idx]
                    
                    # If session_id is specified, filter by session
                    if session_id is None or self._memories[memory_id].session_id == session_id:
                        similar_memory_ids.append(memory_id)
            
            # Get the actual memories
            similar_memories = []
            for memory_id in similar_memory_ids[:limit]:
                if memory_id in self._memories:
                    similar_memories.append(self._memories[memory_id])
            
            return similar_memories
    
    async def get_session_memories(self, session_id: str) -> List[Memory]:
        """
        Get all memories for a specific session.
        """
        async with self._lock:
            memory_ids = self._sessions.get(session_id, [])
            return [self._memories[mid] for mid in memory_ids if mid in self._memories]
    
    async def get_agent_memories(self, agent_id: str) -> List[Memory]:
        """
        Get all memories associated with a specific agent.
        """
        async with self._lock:
            agent_memories = []
            for memory in self._memories.values():
                if memory.agent_id == agent_id:
                    agent_memories.append(memory)
            return agent_memories
    
    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a specific memory.
        Note: FAISS doesn't support deletion efficiently, so we'll mark as deleted.
        """
        async with self._lock:
            if memory_id in self._memories:
                del self._memories[memory_id]
                
                # Remove from session index
                for session_memory_ids in self._sessions.values():
                    if memory_id in session_memory_ids:
                        session_memory_ids.remove(memory_id)
                
                # Note: We don't actually delete from FAISS index due to limitations
                # In a production system, you might want to recreate the index periodically
                return True
            return False
    
    async def clear_session_memories(self, session_id: str) -> int:
        """
        Clear all memories for a specific session.
        """
        async with self._lock:
            memory_ids = self._sessions.get(session_id, [])
            count = len(memory_ids)
            
            # Delete each memory
            for memory_id in memory_ids:
                await self.delete_memory(memory_id)
            
            # Clear session reference
            if session_id in self._sessions:
                del self._sessions[session_id]
            
            return count
    
    async def get_memory_count(self) -> int:
        """
        Get the total count of memories.
        """
        async with self._lock:
            return len(self._memories)
    
    async def get_relevant_context(self, query: str, session_id: str = None, 
                                  context_limit: int = 10) -> Dict[str, Any]:
        """
        Get relevant context for a query from memory.
        """
        async with self._lock:
            # Search for similar memories
            similar_memories = await self.search_similar(
                query, 
                session_id=session_id, 
                limit=context_limit
            )
            
            # Organize by agent
            context_by_agent = {}
            for memory in similar_memories:
                if memory.agent_id not in context_by_agent:
                    context_by_agent[memory.agent_id] = []
                context_by_agent[memory.agent_id].append({
                    "content": memory.content,
                    "timestamp": memory.timestamp,
                    "metadata": memory.metadata
                })
            
            return {
                "similar_memories": similar_memories,
                "context_by_agent": context_by_agent,
                "total_found": len(similar_memories)
            }