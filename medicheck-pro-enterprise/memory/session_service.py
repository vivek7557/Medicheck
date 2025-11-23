from typing import Dict, Any, Optional
import asyncio
import uuid
from datetime import datetime, timedelta
from pydantic import BaseModel


class Session(BaseModel):
    """Session model to represent a patient interaction session"""
    session_id: str
    created_at: datetime
    last_accessed: datetime
    data: Dict[str, Any]
    expires_at: Optional[datetime] = None
    active: bool = True


class SessionService:
    """
    In-memory session service for managing patient interaction sessions.
    Handles session creation, retrieval, updates, and expiration.
    """
    
    def __init__(self, default_session_timeout: int = 3600):  # 1 hour default
        self._sessions: Dict[str, Session] = {}
        self.default_session_timeout = default_session_timeout
        self._lock = asyncio.Lock()
    
    async def create_session(self, initial_data: Dict[str, Any] = None) -> str:
        """
        Create a new session with optional initial data.
        """
        async with self._lock:
            session_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            session = Session(
                session_id=session_id,
                created_at=now,
                last_accessed=now,
                data=initial_data or {},
                expires_at=now + timedelta(seconds=self.default_session_timeout)
            )
            
            self._sessions[session_id] = session
            return session_id
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """
        Retrieve a session by ID.
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            
            if session is None:
                return None
            
            # Check if session has expired
            if session.expires_at and datetime.utcnow() > session.expires_at:
                await self.delete_session(session_id)
                return None
            
            # Update last accessed time
            session.last_accessed = datetime.utcnow()
            return session
    
    async def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """
        Update session data by merging with existing data.
        """
        async with self._lock:
            session = await self.get_session(session_id)
            
            if session is None:
                return False
            
            # Merge the new data with existing data
            session.data.update(data)
            session.last_accessed = datetime.utcnow()
            
            # Extend session if needed
            session.expires_at = datetime.utcnow() + timedelta(seconds=self.default_session_timeout)
            
            self._sessions[session_id] = session
            return True
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        """
        async with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False
    
    async def extend_session(self, session_id: str, additional_seconds: int = 0) -> bool:
        """
        Extend a session's expiration time.
        """
        async with self._lock:
            session = await self.get_session(session_id)
            
            if session is None:
                return False
            
            if additional_seconds > 0:
                session.expires_at = datetime.utcnow() + timedelta(seconds=additional_seconds)
            else:
                session.expires_at = datetime.utcnow() + timedelta(seconds=self.default_session_timeout)
            
            session.last_accessed = datetime.utcnow()
            self._sessions[session_id] = session
            return True
    
    async def clear_expired_sessions(self) -> int:
        """
        Remove all expired sessions and return the count of removed sessions.
        """
        async with self._lock:
            now = datetime.utcnow()
            expired_sessions = [
                session_id for session_id, session in self._sessions.items()
                if session.expires_at and now > session.expires_at
            ]
            
            for session_id in expired_sessions:
                del self._sessions[session_id]
            
            return len(expired_sessions)
    
    async def get_all_sessions(self) -> Dict[str, Session]:
        """
        Get all active sessions (non-expired).
        """
        async with self._lock:
            active_sessions = {}
            now = datetime.utcnow()
            
            for session_id, session in self._sessions.items():
                if session.expires_at and now <= session.expires_at:
                    active_sessions[session_id] = session
            
            return active_sessions
    
    async def get_session_count(self) -> int:
        """
        Get the count of active sessions.
        """
        active_sessions = await self.get_all_sessions()
        return len(active_sessions)