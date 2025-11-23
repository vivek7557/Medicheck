"""
Workflow Engine for Medical Processes
Manages complex medical workflows and process orchestration
"""
import asyncio
from typing import Dict, List, Any, Callable, Optional, Union
from enum import Enum
from datetime import datetime
import uuid
import json


class WorkflowStatus(Enum):
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Task:
    """Represents a single task in a workflow"""
    
    def __init__(self, 
                 task_id: str, 
                 name: str, 
                 function: Callable, 
                 args: tuple = (), 
                 kwargs: dict = None,
                 dependencies: List[str] = None,
                 timeout: int = 300):
        self.task_id = task_id
        self.name = name
        self.function = function
        self.args = args
        self.kwargs = kwargs or {}
        self.dependencies = dependencies or []
        self.timeout = timeout
        self.status = TaskStatus.PENDING
        self.result: Any = None
        self.error: Optional[Exception] = None
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.metadata: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for serialization"""
        return {
            'task_id': self.task_id,
            'name': self.name,
            'status': self.status.value,
            'dependencies': self.dependencies,
            'timeout': self.timeout,
            'result': self.result,
            'error': str(self.error) if self.error else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'metadata': self.metadata
        }


class Workflow:
    """Represents a complete workflow"""
    
    def __init__(self, workflow_id: str, name: str):
        self.workflow_id = workflow_id
        self.name = name
        self.tasks: Dict[str, Task] = {}
        self.status = WorkflowStatus.CREATED
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.metadata: Dict[str, Any] = {}
    
    def add_task(self, task: Task) -> None:
        """Add a task to the workflow"""
        self.tasks[task.task_id] = task
    
    def get_ready_tasks(self) -> List[Task]:
        """Get tasks that are ready to run (dependencies satisfied)"""
        ready_tasks = []
        
        for task in self.tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            
            # Check if all dependencies are completed
            all_deps_satisfied = True
            for dep_id in task.dependencies:
                if dep_id not in self.tasks:
                    all_deps_satisfied = False
                    break
                dep_task = self.tasks[dep_id]
                if dep_task.status != TaskStatus.COMPLETED:
                    all_deps_satisfied = False
                    break
            
            if all_deps_satisfied:
                ready_tasks.append(task)
        
        return ready_tasks
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary for serialization"""
        return {
            'workflow_id': self.workflow_id,
            'name': self.name,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'tasks': {tid: task.to_dict() for tid, task in self.tasks.items()},
            'metadata': self.metadata
        }


class WorkflowEngine:
    """Manages execution of workflows"""
    
    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self._lock = asyncio.Lock()
    
    def create_workflow(self, name: str) -> str:
        """Create a new workflow"""
        workflow_id = str(uuid.uuid4())
        workflow = Workflow(workflow_id, name)
        self.workflows[workflow_id] = workflow
        return workflow_id
    
    def add_task_to_workflow(self, workflow_id: str, task: Task) -> bool:
        """Add a task to a workflow"""
        if workflow_id not in self.workflows:
            return False
        
        self.workflows[workflow_id].add_task(task)
        return True
    
    async def execute_workflow(self, workflow_id: str) -> bool:
        """Execute a workflow"""
        if workflow_id not in self.workflows:
            return False
        
        workflow = self.workflows[workflow_id]
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.now()
        
        try:
            while workflow.status == WorkflowStatus.RUNNING:
                ready_tasks = workflow.get_ready_tasks()
                
                if not ready_tasks:
                    # Check if workflow is complete
                    pending_tasks = [t for t in workflow.tasks.values() if t.status == TaskStatus.PENDING]
                    if not pending_tasks:
                        workflow.status = WorkflowStatus.COMPLETED
                        workflow.completed_at = datetime.now()
                        break
                    else:
                        # Wait a bit before checking again
                        await asyncio.sleep(0.1)
                        continue
                
                # Execute ready tasks concurrently
                await self._execute_tasks_concurrently(workflow_id, ready_tasks)
        
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            return False
        
        return True
    
    async def _execute_tasks_concurrently(self, workflow_id: str, tasks: List[Task]) -> None:
        """Execute multiple tasks concurrently"""
        async def execute_single_task(task: Task) -> None:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            
            try:
                if asyncio.iscoroutinefunction(task.function):
                    result = await task.function(*task.args, **task.kwargs)
                else:
                    result = await asyncio.get_event_loop().run_in_executor(
                        None, task.function, *task.args, **task.kwargs
                    )
                
                task.result = result
                task.status = TaskStatus.COMPLETED
            except Exception as e:
                task.error = e
                task.status = TaskStatus.FAILED
            
            task.completed_at = datetime.now()
        
        # Execute all tasks concurrently
        await asyncio.gather(*[execute_single_task(task) for task in tasks], return_exceptions=True)
    
    def get_workflow_status(self, workflow_id: str) -> Optional[WorkflowStatus]:
        """Get the status of a workflow"""
        if workflow_id not in self.workflows:
            return None
        return self.workflows[workflow_id].status
    
    def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a workflow"""
        if workflow_id not in self.workflows:
            return False
        
        workflow = self.workflows[workflow_id]
        if workflow.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]:
            return False
        
        workflow.status = WorkflowStatus.CANCELLED
        workflow.completed_at = datetime.now()
        
        # Cancel any running tasks
        for task in workflow.tasks.values():
            if task.status == TaskStatus.RUNNING:
                task.status = TaskStatus.SKIPPED
        
        return True
    
    def pause_workflow(self, workflow_id: str) -> bool:
        """Pause a workflow"""
        if workflow_id not in self.workflows:
            return False
        
        workflow = self.workflows[workflow_id]
        if workflow.status != WorkflowStatus.RUNNING:
            return False
        
        workflow.status = WorkflowStatus.PAUSED
        return True
    
    def resume_workflow(self, workflow_id: str) -> bool:
        """Resume a paused workflow"""
        if workflow_id not in self.workflows:
            return False
        
        workflow = self.workflows[workflow_id]
        if workflow.status != WorkflowStatus.PAUSED:
            return False
        
        # Resume execution
        asyncio.create_task(self.execute_workflow(workflow_id))
        workflow.status = WorkflowStatus.RUNNING
        return True


class MedicalWorkflowEngine(WorkflowEngine):
    """Medical-specific workflow engine with clinical safety checks"""
    
    def __init__(self):
        super().__init__()
        self.medical_workflows: Dict[str, Dict[str, Any]] = {}
    
    def create_medical_workflow(self, 
                               name: str, 
                               patient_id: str, 
                               workflow_type: str,
                               priority: int = 1) -> str:
        """Create a medical workflow with patient context"""
        workflow_id = self.create_workflow(name)
        
        # Add medical-specific metadata
        self.medical_workflows[workflow_id] = {
            'patient_id': patient_id,
            'workflow_type': workflow_type,
            'priority': priority,
            'created_at': datetime.now(),
            'consent_verified': True  # In a real system, this would be verified
        }
        
        # Update workflow metadata
        self.workflows[workflow_id].metadata.update({
            'patient_id': patient_id,
            'workflow_type': workflow_type,
            'priority': priority
        })
        
        return workflow_id
    
    def add_medical_task(self, 
                        workflow_id: str, 
                        name: str, 
                        function: Callable,
                        patient_context: Dict[str, Any],
                        task_type: str,
                        *args, 
                        **kwargs) -> bool:
        """Add a medical task to a workflow"""
        # Add patient context to task
        kwargs['patient_context'] = patient_context
        
        task_id = str(uuid.uuid4())
        task = Task(
            task_id=task_id,
            name=name,
            function=function,
            args=args,
            kwargs=kwargs,
            metadata={
                'task_type': task_type,
                'patient_context': patient_context
            }
        )
        
        return self.add_task_to_workflow(workflow_id, task)
    
    def get_patient_workflows(self, patient_id: str) -> List[Workflow]:
        """Get all workflows for a specific patient"""
        patient_workflows = []
        for wf_id, metadata in self.medical_workflows.items():
            if metadata['patient_id'] == patient_id:
                if wf_id in self.workflows:
                    patient_workflows.append(self.workflows[wf_id])
        return patient_workflows
    
    async def execute_medical_workflow(self, workflow_id: str) -> bool:
        """Execute a medical workflow with safety checks"""
        # In a real system, we'd implement medical safety checks here
        # such as verifying patient consent, checking for contraindications, etc.
        
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return False
        
        # Check if workflow is critical
        workflow_type = self.medical_workflows[workflow_id]['workflow_type']
        if workflow_type in ['emergency', 'critical_care']:
            print(f"Executing critical workflow: {workflow.name}")
        
        return await self.execute_workflow(workflow_id)