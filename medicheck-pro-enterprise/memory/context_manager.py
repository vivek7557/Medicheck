"""
Context Manager for Medical Assistant
Handles context engineering, compaction, and optimization
"""
import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class ContextItem:
    """Represents a single context item"""
    id: str
    content: str
    timestamp: datetime
    priority: int = 1  # Higher number means higher priority
    tags: List[str] = None
    metadata: Dict[str, Any] = None


class ContextManager:
    """Manages context for medical conversations"""
    
    def __init__(self, max_context_length: int = 4096, retention_period: timedelta = timedelta(hours=24)):
        self.max_context_length = max_context_length
        self.retention_period = retention_period
        self.context_items: List[ContextItem] = []
        self.context_size = 0
    
    def add_context_item(self, content: str, priority: int = 1, tags: List[str] = None, metadata: Dict[str, Any] = None) -> str:
        """Add a new context item"""
        item_id = f"ctx_{len(self.context_items)}_{int(datetime.now().timestamp())}"
        item = ContextItem(
            id=item_id,
            content=content,
            timestamp=datetime.now(),
            priority=priority,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        self.context_items.append(item)
        self.context_size += len(content)
        
        # Compact if needed
        if self.context_size > self.max_context_length:
            asyncio.create_task(self.compact_context())
        
        return item_id
    
    def get_context_window(self, max_tokens: int = 3000) -> str:
        """Get the current context window, prioritizing important items"""
        # Sort by priority and recency
        sorted_items = sorted(self.context_items, key=lambda x: (x.priority, x.timestamp), reverse=True)
        
        context_parts = []
        current_size = 0
        
        for item in sorted_items:
            item_size = len(item.content)
            if current_size + item_size <= max_tokens:
                context_parts.append(item.content)
                current_size += item_size
            else:
                break
        
        return "\n".join(context_parts)
    
    async def compact_context(self):
        """Compact context by removing older, lower-priority items"""
        # Remove expired items
        cutoff_time = datetime.now() - self.retention_period
        self.context_items = [item for item in self.context_items if item.timestamp > cutoff_time]
        
        # If still too large, remove lowest priority items
        if self.context_size > self.max_context_length:
            # Sort by priority (ascending) and timestamp (ascending) to remove oldest low-priority items
            self.context_items.sort(key=lambda x: (x.priority, x.timestamp))
            
            # Remove items until we're under the limit
            while self.context_size > self.max_context_length and len(self.context_items) > 0:
                removed_item = self.context_items.pop(0)
                self.context_size -= len(removed_item.content)
    
    def update_item_priority(self, item_id: str, new_priority: int):
        """Update the priority of a context item"""
        for item in self.context_items:
            if item.id == item_id:
                item.priority = new_priority
                break
    
    def tag_item(self, item_id: str, tags: List[str]):
        """Add tags to a context item"""
        for item in self.context_items:
            if item.id == item_id:
                item.tags.extend(tags)
                break
    
    def search_by_tags(self, tags: List[str]) -> List[ContextItem]:
        """Find context items by tags"""
        result = []
        for item in self.context_items:
            if any(tag in item.tags for tag in tags):
                result.append(item)
        return result
    
    def clear_context(self):
        """Clear all context items"""
        self.context_items = []
        self.context_size = 0


class MedicalContextManager(ContextManager):
    """Medical-specific context manager with HIPAA compliance"""
    
    def __init__(self, max_context_length: int = 4096, retention_period: timedelta = timedelta(hours=24)):
        super().__init__(max_context_length, retention_period)
        self.patient_context: Dict[str, Any] = {}
    
    def set_patient_context(self, patient_id: str, patient_data: Dict[str, Any]):
        """Set patient-specific context"""
        self.patient_context = {
            'patient_id': patient_id,
            'data': patient_data,
            'timestamp': datetime.now()
        }
    
    def get_patient_context(self) -> Dict[str, Any]:
        """Get patient-specific context"""
        return self.patient_context
    
    def add_medical_context(self, content: str, category: str, priority: int = 1):
        """Add medical context with category"""
        tags = [category]
        if category in ['symptoms', 'diagnosis', 'treatment', 'allergies', 'medications']:
            # Medical categories get higher priority
            priority = max(priority, 3)
        
        return self.add_context_item(content, priority, tags)
    
    def get_medical_context_summary(self) -> str:
        """Get a summary of medical context"""
        categories = ['symptoms', 'diagnosis', 'treatment', 'allergies', 'medications']
        summary_parts = []
        
        for category in categories:
            items = self.search_by_tags([category])
            if items:
                category_items = [f"  - {item.content}" for item in items]
                summary_parts.append(f"{category.title()}:\n" + "\n".join(category_items))
        
        return "\n\n".join(summary_parts) if summary_parts else "No specific medical context available."