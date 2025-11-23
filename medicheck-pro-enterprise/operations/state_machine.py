"""
State Machine for Medical Processes
Manages state transitions in medical workflows
"""
import asyncio
from typing import Dict, List, Any, Callable, Optional, Set
from enum import Enum
from datetime import datetime
import uuid


class MedicalState(Enum):
    """Medical-specific states"""
    PATIENT_INTAKE = "patient_intake"
    TRIAGE = "triage"
    INITIAL_ASSESSMENT = "initial_assessment"
    DIAGNOSIS = "diagnosis"
    TREATMENT_PLANNING = "treatment_planning"
    TREATMENT = "treatment"
    MONITORING = "monitoring"
    FOLLOW_UP = "follow_up"
    DISCHARGE = "discharge"
    EMERGENCY = "emergency"


class Transition:
    """Represents a state transition"""
    
    def __init__(self, 
                 from_state: MedicalState, 
                 to_state: MedicalState, 
                 condition: Optional[Callable] = None,
                 action: Optional[Callable] = None,
                 priority: int = 1):
        self.from_state = from_state
        self.to_state = to_state
        self.condition = condition or (lambda ctx: True)  # Default: always allowed
        self.action = action
        self.priority = priority
        self.transition_id = str(uuid.uuid4())
    
    async def can_transition(self, context: Dict[str, Any]) -> bool:
        """Check if transition is allowed based on condition"""
        try:
            result = self.condition(context)
            if asyncio.iscoroutine(result):
                result = await result
            return bool(result)
        except Exception:
            return False
    
    async def execute_action(self, context: Dict[str, Any]) -> bool:
        """Execute the action associated with this transition"""
        if not self.action:
            return True
        
        try:
            result = self.action(context)
            if asyncio.iscoroutine(result):
                result = await result
            return bool(result)
        except Exception:
            return False


class MedicalStateMachine:
    """State machine for medical processes with HIPAA compliance"""
    
    def __init__(self, patient_id: str, initial_state: MedicalState = MedicalState.PATIENT_INTAKE):
        self.patient_id = patient_id
        self.current_state = initial_state
        self.transitions: Dict[MedicalState, List[Transition]] = {}
        self.state_history: List[Dict[str, Any]] = []
        self.created_at = datetime.now()
        self.metadata: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
        
        # Add default transitions
        self._setup_default_transitions()
    
    def _setup_default_transitions(self):
        """Setup default medical workflow transitions"""
        # Define standard medical workflow transitions
        standard_transitions = [
            (MedicalState.PATIENT_INTAKE, MedicalState.TRIAGE),
            (MedicalState.TRIAGE, MedicalState.INITIAL_ASSESSMENT),
            (MedicalState.INITIAL_ASSESSMENT, MedicalState.DIAGNOSIS),
            (MedicalState.DIAGNOSIS, MedicalState.TREATMENT_PLANNING),
            (MedicalState.TREATMENT_PLANNING, MedicalState.TREATMENT),
            (MedicalState.TREATMENT, MedicalState.MONITORING),
            (MedicalState.MONITORING, MedicalState.FOLLOW_UP),
            (MedicalState.FOLLOW_UP, MedicalState.DISCHARGE),
            # Emergency can transition to any state
            (MedicalState.EMERGENCY, MedicalState.DIAGNOSIS),
            (MedicalState.EMERGENCY, MedicalState.TREATMENT),
        ]
        
        for from_state, to_state in standard_transitions:
            self.add_transition(from_state, to_state)
    
    def add_transition(self, 
                      from_state: MedicalState, 
                      to_state: MedicalState, 
                      condition: Optional[Callable] = None,
                      action: Optional[Callable] = None) -> str:
        """Add a transition between states"""
        transition = Transition(from_state, to_state, condition, action)
        
        if from_state not in self.transitions:
            self.transitions[from_state] = []
        
        self.transitions[from_state].append(transition)
        return transition.transition_id
    
    async def can_transition_to(self, target_state: MedicalState, context: Dict[str, Any] = None) -> bool:
        """Check if we can transition to the target state"""
        if context is None:
            context = {}
        
        context['from_state'] = self.current_state
        context['to_state'] = target_state
        context['patient_id'] = self.patient_id
        
        if self.current_state not in self.transitions:
            return False
        
        for transition in self.transitions[self.current_state]:
            if transition.to_state == target_state:
                if await transition.can_transition(context):
                    return True
        
        return False
    
    async def transition_to(self, target_state: MedicalState, context: Dict[str, Any] = None) -> bool:
        """Transition to the target state"""
        if context is None:
            context = {}
        
        async with self._lock:
            if not await self.can_transition_to(target_state, context):
                return False
            
            # Prepare transition context
            transition_context = {
                **context,
                'from_state': self.current_state,
                'to_state': target_state,
                'patient_id': self.patient_id,
                'timestamp': datetime.now()
            }
            
            # Find the appropriate transition
            for transition in self.transitions[self.current_state]:
                if transition.to_state == target_state and await transition.can_transition(transition_context):
                    # Execute the transition action
                    action_result = await transition.execute_action(transition_context)
                    if not action_result:
                        return False
                    
                    # Log the state change
                    self.state_history.append({
                        'from_state': self.current_state,
                        'to_state': target_state,
                        'timestamp': datetime.now(),
                        'context': {k: v for k, v in transition_context.items() if k != 'patient_id'},  # Exclude patient ID from logs for privacy
                        'transition_id': transition.transition_id
                    })
                    
                    # Update current state
                    self.current_state = target_state
                    return True
        
        return False
    
    def get_available_transitions(self, context: Dict[str, Any] = None) -> List[MedicalState]:
        """Get all states we can transition to from the current state"""
        if context is None:
            context = {}
        
        context['from_state'] = self.current_state
        context['patient_id'] = self.patient_id
        
        available = []
        
        if self.current_state not in self.transitions:
            return available
        
        for transition in self.transitions[self.current_state]:
            if asyncio.run(transition.can_transition(context)):
                available.append(transition.to_state)
        
        return available
    
    def get_state_history(self) -> List[Dict[str, Any]]:
        """Get the history of state changes"""
        return self.state_history.copy()
    
    def is_in_state(self, state: MedicalState) -> bool:
        """Check if the machine is currently in the given state"""
        return self.current_state == state
    
    def force_state_change(self, new_state: MedicalState, reason: str = ""):
        """Force a state change (use with caution, typically for emergencies)"""
        old_state = self.current_state
        self.current_state = new_state
        
        # Log the forced state change
        self.state_history.append({
            'from_state': old_state,
            'to_state': new_state,
            'timestamp': datetime.now(),
            'forced': True,
            'reason': reason
        })
    
    def get_current_state_info(self) -> Dict[str, Any]:
        """Get information about the current state"""
        return {
            'current_state': self.current_state,
            'patient_id': self.patient_id,
            'created_at': self.created_at,
            'time_in_current_state': (datetime.now() - self.created_at) if self.is_first_state() else self.time_in_state(),
            'available_transitions': [s.value for s in self.get_available_transitions()],
            'metadata': self.metadata
        }
    
    def is_first_state(self) -> bool:
        """Check if we're still in the initial state"""
        return len(self.state_history) == 0
    
    def time_in_state(self) -> float:
        """Get the time spent in the current state"""
        if self.is_first_state():
            return (datetime.now() - self.created_at).total_seconds()
        
        last_transition = self.state_history[-1]
        return (datetime.now() - last_transition['timestamp']).total_seconds()


class EmergencyStateMachine(MedicalStateMachine):
    """State machine with emergency capabilities"""
    
    def __init__(self, patient_id: str, initial_state: MedicalState = MedicalState.PATIENT_INTAKE):
        super().__init__(patient_id, initial_state)
        self.emergency_transitions = set()
        self._setup_emergency_transitions()
    
    def _setup_emergency_transitions(self):
        """Setup transitions that can occur in emergency situations"""
        # In emergency, we can go directly to diagnosis or treatment
        emergency_transitions = [
            (MedicalState.EMERGENCY, MedicalState.DIAGNOSIS),
            (MedicalState.EMERGENCY, MedicalState.TREATMENT),
            (MedicalState.TRIAGE, MedicalState.EMERGENCY),
            (MedicalState.INITIAL_ASSESSMENT, MedicalState.EMERGENCY),
            (MedicalState.DIAGNOSIS, MedicalState.EMERGENCY),
            (MedicalState.TREATMENT, MedicalState.EMERGENCY),
        ]
        
        for from_state, to_state in emergency_transitions:
            self.add_emergency_transition(from_state, to_state)
    
    def add_emergency_transition(self, from_state: MedicalState, to_state: MedicalState) -> str:
        """Add an emergency transition that bypasses normal conditions"""
        def emergency_condition(ctx):
            # Allow emergency transition if current state is emergency or target is emergency
            return ctx.get('is_emergency', False) or from_state == MedicalState.EMERGENCY
        
        transition_id = self.add_transition(from_state, to_state, condition=emergency_condition)
        self.emergency_transitions.add(transition_id)
        return transition_id
    
    async def trigger_emergency(self, context: Dict[str, Any] = None) -> bool:
        """Trigger emergency state"""
        if context is None:
            context = {}
        
        context['is_emergency'] = True
        return await self.transition_to(MedicalState.EMERGENCY, context)
    
    def is_emergency_state(self) -> bool:
        """Check if the current state is an emergency"""
        return self.current_state == MedicalState.EMERGENCY