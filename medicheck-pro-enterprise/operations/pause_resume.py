"""
Pause/Resume Operations for Long-Running Medical Tasks
Handles pausing and resuming of long-running operations in medical workflows
"""
import asyncio
import json
import pickle
from typing import Dict, Any, Callable, Optional, List
from enum import Enum
from datetime import datetime
import uuid


class OperationStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OperationState:
    """Represents the state of a long-running operation"""
    
    def __init__(self, operation_id: str, name: str, target_func: Callable, args: tuple = (), kwargs: dict = None):
        self.operation_id = operation_id
        self.name = name
        self.target_func = target_func
        self.args = args
        self.kwargs = kwargs or {}
        self.status = OperationStatus.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.paused_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Any = None
        self.error: Optional[Exception] = None
        self.progress: float = 0.0
        self.metadata: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert operation state to dictionary for serialization"""
        return {
            'operation_id': self.operation_id,
            'name': self.name,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'paused_at': self.paused_at.isoformat() if self.paused_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'progress': self.progress,
            'result': self.result,
            'error': str(self.error) if self.error else None,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], target_func: Callable = None) -> 'OperationState':
        """Create operation state from dictionary"""
        op = cls(
            operation_id=data['operation_id'],
            name=data['name'],
            target_func=target_func,
            args=data.get('args', ()),
            kwargs=data.get('kwargs', {})
        )
        op.status = OperationStatus(data['status'])
        op.created_at = datetime.fromisoformat(data['created_at'])
        op.started_at = datetime.fromisoformat(data['started_at']) if data['started_at'] else None
        op.paused_at = datetime.fromisoformat(data['paused_at']) if data['paused_at'] else None
        op.completed_at = datetime.fromisoformat(data['completed_at']) if data['completed_at'] else None
        op.progress = data['progress']
        op.result = data['result']
        op.error = data['error']
        op.metadata = data['metadata']
        return op


class PauseResumeManager:
    """Manages pause/resume functionality for long-running operations"""
    
    def __init__(self):
        self.operations: Dict[str, OperationState] = {}
        self._lock = asyncio.Lock()
    
    def create_operation(self, name: str, target_func: Callable, *args, **kwargs) -> str:
        """Create a new operation"""
        operation_id = str(uuid.uuid4())
        operation = OperationState(operation_id, name, target_func, args, kwargs)
        self.operations[operation_id] = operation
        return operation_id
    
    async def start_operation(self, operation_id: str) -> bool:
        """Start an operation"""
        async with self._lock:
            if operation_id not in self.operations:
                return False
            
            operation = self.operations[operation_id]
            if operation.status != OperationStatus.PENDING:
                return False
            
            operation.status = OperationStatus.RUNNING
            operation.started_at = datetime.now()
            
            # Run the operation in the background
            asyncio.create_task(self._execute_operation(operation_id))
            return True
    
    async def _execute_operation(self, operation_id: str):
        """Execute the operation"""
        operation = self.operations[operation_id]
        
        try:
            # Execute the target function
            if asyncio.iscoroutinefunction(operation.target_func):
                result = await operation.target_func(*operation.args, **operation.kwargs)
            else:
                result = operation.target_func(*operation.args, **operation.kwargs)
            
            # Update operation state
            operation.result = result
            operation.progress = 1.0
            operation.status = OperationStatus.COMPLETED
            operation.completed_at = datetime.now()
        
        except Exception as e:
            operation.error = e
            operation.status = OperationStatus.FAILED
    
    async def pause_operation(self, operation_id: str) -> bool:
        """Pause an operation"""
        async with self._lock:
            if operation_id not in self.operations:
                return False
            
            operation = self.operations[operation_id]
            if operation.status != OperationStatus.RUNNING:
                return False
            
            operation.status = OperationStatus.PAUSED
            operation.paused_at = datetime.now()
            return True
    
    async def resume_operation(self, operation_id: str) -> bool:
        """Resume a paused operation"""
        async with self._lock:
            if operation_id not in self.operations:
                return False
            
            operation = self.operations[operation_id]
            if operation.status != OperationStatus.PAUSED:
                return False
            
            operation.status = OperationStatus.RUNNING
            operation.paused_at = None
            
            # Resume the operation in the background
            asyncio.create_task(self._execute_operation(operation_id))
            return True
    
    async def cancel_operation(self, operation_id: str) -> bool:
        """Cancel an operation"""
        async with self._lock:
            if operation_id not in self.operations:
                return False
            
            operation = self.operations[operation_id]
            if operation.status in [OperationStatus.COMPLETED, OperationStatus.FAILED, OperationStatus.CANCELLED]:
                return False
            
            operation.status = OperationStatus.CANCELLED
            operation.completed_at = datetime.now()
            return True
    
    def get_operation_status(self, operation_id: str) -> Optional[OperationState]:
        """Get the status of an operation"""
        return self.operations.get(operation_id)
    
    def get_all_operations(self) -> List[OperationState]:
        """Get all operations"""
        return list(self.operations.values())
    
    async def save_operation_state(self, operation_id: str, filepath: str) -> bool:
        """Save operation state to file"""
        if operation_id not in self.operations:
            return False
        
        operation = self.operations[operation_id]
        try:
            with open(filepath, 'wb') as f:
                pickle.dump(operation, f)
            return True
        except Exception:
            return False
    
    async def load_operation_state(self, filepath: str, operation_id: str, target_func: Callable) -> bool:
        """Load operation state from file"""
        try:
            with open(filepath, 'rb') as f:
                operation = pickle.load(f)
            
            # Update the target function
            operation.target_func = target_func
            operation.operation_id = operation_id
            
            self.operations[operation_id] = operation
            return True
        except Exception:
            return False


class MedicalPauseResumeManager(PauseResumeManager):
    """Medical-specific pause/resume manager with additional safety checks"""
    
    def __init__(self):
        super().__init__()
        self.medical_operations: Dict[str, Dict[str, Any]] = {}
    
    def create_medical_operation(self, 
                                name: str, 
                                target_func: Callable, 
                                patient_id: str,
                                operation_type: str,
                                *args, 
                                **kwargs) -> str:
        """Create a medical operation with patient context"""
        operation_id = super().create_operation(name, target_func, *args, **kwargs)
        
        # Add medical-specific metadata
        self.medical_operations[operation_id] = {
            'patient_id': patient_id,
            'operation_type': operation_type,
            'created_at': datetime.now(),
            'consent_given': True  # In a real system, this would be verified
        }
        
        # Update the operation metadata
        self.operations[operation_id].metadata.update({
            'patient_id': patient_id,
            'operation_type': operation_type
        })
        
        return operation_id
    
    async def pause_medical_operation(self, operation_id: str) -> bool:
        """Pause a medical operation with safety checks"""
        # Check if operation is critical and should not be paused
        operation = self.get_operation_status(operation_id)
        if not operation:
            return False
        
        # In a real system, we'd check if this is a critical operation
        # that shouldn't be paused for patient safety
        is_critical = operation.metadata.get('operation_type') in ['emergency_procedure', 'life_support', 'critical_monitoring']
        
        if is_critical:
            # Log critical operation pause attempt
            print(f"WARNING: Attempt to pause critical operation {operation_id}")
            return False
        
        return await self.pause_operation(operation_id)
    
    def get_patient_operations(self, patient_id: str) -> List[OperationState]:
        """Get all operations for a specific patient"""
        patient_ops = []
        for op_id, metadata in self.medical_operations.items():
            if metadata['patient_id'] == patient_id:
                if op_id in self.operations:
                    patient_ops.append(self.operations[op_id])
        return patient_ops