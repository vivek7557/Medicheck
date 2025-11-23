"""
Agent-to-Agent Protocol for Medical Assistant
Implements secure communication between medical agents
"""
import asyncio
import json
import uuid
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from enum import Enum
import hashlib
import hmac
import base64


class MessageType(Enum):
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


class MessagePriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class A2AMessage:
    """Represents a message in the Agent-to-Agent protocol"""
    
    def __init__(self, 
                 msg_type: MessageType,
                 content: Dict[str, Any],
                 sender_id: str,
                 recipient_id: str,
                 correlation_id: Optional[str] = None,
                 priority: MessagePriority = MessagePriority.NORMAL,
                 ttl: int = 300):  # 5 minutes default TTL
        self.message_id = str(uuid.uuid4())
        self.msg_type = msg_type
        self.content = content
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.priority = priority
        self.created_at = datetime.now()
        self.expires_at = self.created_at.timestamp() + ttl
        self.metadata: Dict[str, Any] = {}
        self.signature: Optional[str] = None
    
    def sign(self, secret_key: str):
        """Sign the message with HMAC"""
        message_str = f"{self.message_id}{self.sender_id}{self.recipient_id}{json.dumps(self.content, sort_keys=True)}"
        self.signature = base64.b64encode(
            hmac.new(
                secret_key.encode('utf-8'),
                message_str.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
    
    def verify_signature(self, secret_key: str) -> bool:
        """Verify the message signature"""
        if not self.signature:
            return False
        
        message_str = f"{self.message_id}{self.sender_id}{self.recipient_id}{json.dumps(self.content, sort_keys=True)}"
        expected_signature = base64.b64encode(
            hmac.new(
                secret_key.encode('utf-8'),
                message_str.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        return hmac.compare_digest(self.signature, expected_signature)
    
    def is_expired(self) -> bool:
        """Check if the message has expired"""
        return datetime.now().timestamp() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            'message_id': self.message_id,
            'msg_type': self.msg_type.value,
            'content': self.content,
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'correlation_id': self.correlation_id,
            'priority': self.priority.value,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at,
            'metadata': self.metadata,
            'signature': self.signature
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'A2AMessage':
        """Create message from dictionary"""
        msg = cls(
            msg_type=MessageType(data['msg_type']),
            content=data['content'],
            sender_id=data['sender_id'],
            recipient_id=data['recipient_id'],
            correlation_id=data['correlation_id'],
            priority=MessagePriority(data['priority']),
            ttl=int(data['expires_at'] - datetime.now().timestamp())
        )
        msg.message_id = data['message_id']
        msg.created_at = datetime.fromisoformat(data['created_at'])
        msg.metadata = data.get('metadata', {})
        msg.signature = data.get('signature')
        return msg


class A2AMessageHandler:
    """Handles incoming and outgoing A2A messages"""
    
    def __init__(self, agent_id: str, secret_key: str):
        self.agent_id = agent_id
        self.secret_key = secret_key
        self.handlers: Dict[str, Callable] = {}
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self._lock = asyncio.Lock()
    
    def register_handler(self, message_type: str, handler_func: Callable):
        """Register a handler for a specific message type"""
        self.handlers[message_type] = handler_func
    
    async def send_message(self, 
                          recipient_id: str, 
                          content: Dict[str, Any], 
                          msg_type: MessageType = MessageType.REQUEST,
                          priority: MessagePriority = MessagePriority.NORMAL,
                          correlation_id: Optional[str] = None) -> Optional[A2AMessage]:
        """Send a message to another agent"""
        message = A2AMessage(
            msg_type=msg_type,
            content=content,
            sender_id=self.agent_id,
            recipient_id=recipient_id,
            correlation_id=correlation_id,
            priority=priority
        )
        
        # Sign the message
        message.sign(self.secret_key)
        
        # If this is a request, create a future to wait for response
        if msg_type == MessageType.REQUEST:
            future = asyncio.Future()
            self.pending_requests[message.correlation_id] = future
            
            # Clean up future after timeout
            asyncio.create_task(self._cleanup_future(message.correlation_id, future))
        
        # In a real implementation, this would send via a message broker
        # For now, we'll simulate by calling the recipient's handler directly
        try:
            response = await self._simulate_send(message)
            return response
        except Exception as e:
            # Handle error and return error message
            error_msg = A2AMessage(
                msg_type=MessageType.ERROR,
                content={'error': str(e), 'original_message_id': message.message_id},
                sender_id=self.agent_id,
                recipient_id=recipient_id,
                correlation_id=message.correlation_id
            )
            error_msg.sign(self.secret_key)
            return error_msg
    
    async def _simulate_send(self, message: A2AMessage) -> Optional[A2AMessage]:
        """Simulate sending a message (in real implementation, this would use a message broker)"""
        # This is a simplified simulation - in reality, this would send through a message broker
        # For this example, we'll assume there's a global registry of agents
        if message.recipient_id in A2AProtocol.agent_registry:
            recipient_handler = A2AProtocol.agent_registry[message.recipient_id]
            return await recipient_handler.handle_incoming_message(message)
        else:
            raise Exception(f"Recipient agent {message.recipient_id} not found")
    
    async def handle_incoming_message(self, message: A2AMessage) -> Optional[A2AMessage]:
        """Handle an incoming message"""
        # Verify signature
        if not message.verify_signature(self.secret_key):
            raise Exception("Invalid message signature")
        
        # Check if expired
        if message.is_expired():
            raise Exception("Message expired")
        
        # Handle based on message type
        if message.msg_type == MessageType.REQUEST:
            # Find appropriate handler
            action = message.content.get('action')
            if action and action in self.handlers:
                try:
                    result = await self.handlers[action](message.content)
                    # Send response
                    response = A2AMessage(
                        msg_type=MessageType.RESPONSE,
                        content={'result': result, 'original_request_id': message.message_id},
                        sender_id=self.agent_id,
                        recipient_id=message.sender_id,
                        correlation_id=message.correlation_id
                    )
                    response.sign(self.secret_key)
                    return response
                except Exception as e:
                    error_response = A2AMessage(
                        msg_type=MessageType.ERROR,
                        content={'error': str(e), 'original_request_id': message.message_id},
                        sender_id=self.agent_id,
                        recipient_id=message.sender_id,
                        correlation_id=message.correlation_id
                    )
                    error_response.sign(self.secret_key)
                    return error_response
            else:
                error_response = A2AMessage(
                    msg_type=MessageType.ERROR,
                    content={'error': f'No handler for action: {action}', 'original_request_id': message.message_id},
                    sender_id=self.agent_id,
                    recipient_id=message.sender_id,
                    correlation_id=message.correlation_id
                )
                error_response.sign(self.secret_key)
                return error_response
        
        elif message.msg_type == MessageType.RESPONSE:
            # Fulfill the pending request future
            correlation_id = message.correlation_id
            if correlation_id in self.pending_requests:
                future = self.pending_requests[correlation_id]
                if not future.done():
                    future.set_result(message)
                del self.pending_requests[correlation_id]
            return None  # Responses don't need to be sent back
        
        elif message.msg_type == MessageType.NOTIFICATION:
            # Handle notification - just process and acknowledge
            action = message.content.get('action')
            if action and action in self.handlers:
                await self.handlers[action](message.content)
            
            # Send acknowledgment
            ack = A2AMessage(
                msg_type=MessageType.RESPONSE,
                content={'status': 'received', 'original_message_id': message.message_id},
                sender_id=self.agent_id,
                recipient_id=message.sender_id,
                correlation_id=message.correlation_id
            )
            ack.sign(self.secret_key)
            return ack
        
        elif message.msg_type == MessageType.ERROR:
            # Handle error - log and possibly notify
            print(f"Received error message: {message.content}")
            return None
    
    async def _cleanup_future(self, correlation_id: str, future: asyncio.Future):
        """Clean up pending request future after timeout"""
        await asyncio.sleep(30)  # 30 second timeout
        if not future.done():
            future.set_exception(asyncio.TimeoutError(f"Request {correlation_id} timed out"))
            if correlation_id in self.pending_requests:
                del self.pending_requests[correlation_id]


class A2AProtocol:
    """Main A2A Protocol implementation"""
    
    # Global registry of agents
    agent_registry: Dict[str, A2AMessageHandler] = {}
    
    def __init__(self, agent_id: str, secret_key: str):
        self.agent_id = agent_id
        self.secret_key = secret_key
        self.message_handler = A2AMessageHandler(agent_id, secret_key)
        
        # Register this agent in the global registry
        A2AProtocol.agent_registry[agent_id] = self.message_handler
    
    def register_handler(self, message_type: str, handler_func: Callable):
        """Register a handler for specific message types"""
        self.message_handler.register_handler(message_type, handler_func)
    
    async def send_request(self, 
                          recipient_id: str, 
                          action: str, 
                          data: Dict[str, Any],
                          priority: MessagePriority = MessagePriority.NORMAL) -> Optional[Dict[str, Any]]:
        """Send a request to another agent and wait for response"""
        message = await self.message_handler.send_message(
            recipient_id=recipient_id,
            content={'action': action, **data},
            msg_type=MessageType.REQUEST,
            priority=priority
        )
        
        if message and message.msg_type == MessageType.RESPONSE:
            return message.content
        elif message and message.msg_type == MessageType.ERROR:
            raise Exception(f"Remote agent error: {message.content.get('error')}")
        else:
            raise Exception("Request failed or timed out")
    
    async def send_notification(self, 
                               recipient_id: str, 
                               action: str, 
                               data: Dict[str, Any]) -> bool:
        """Send a notification to another agent (fire and forget)"""
        try:
            await self.message_handler.send_message(
                recipient_id=recipient_id,
                content={'action': action, **data},
                msg_type=MessageType.NOTIFICATION
            )
            return True
        except Exception:
            return False
    
    def get_supported_actions(self) -> List[str]:
        """Get list of supported actions"""
        return list(self.message_handler.handlers.keys())


class MedicalA2AProtocol(A2AProtocol):
    """Medical-specific A2A protocol with additional safety and compliance features"""
    
    def __init__(self, agent_id: str, secret_key: str, compliance_mode: bool = True):
        super().__init__(agent_id, secret_key)
        self.compliance_mode = compliance_mode
        self.message_log: List[A2AMessage] = []
        self._setup_medical_handlers()
    
    def _setup_medical_handlers(self):
        """Setup default medical-specific handlers"""
        self.register_handler('patient_info_request', self._handle_patient_info_request)
        self.register_handler('diagnosis_consult', self._handle_diagnosis_consult)
        self.register_handler('treatment_recommendation', self._handle_treatment_recommendation)
        self.register_handler('drug_interaction_check', self._handle_drug_interaction_check)
    
    async def _handle_patient_info_request(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Handle patient information request"""
        patient_id = content.get('patient_id')
        if not patient_id:
            raise ValueError("Patient ID is required")
        
        # In a real implementation, this would fetch from a secure patient database
        # For simulation, return dummy data
        return {
            'patient_id': patient_id,
            'status': 'info_fetched',
            'data': {
                'age': 45,
                'gender': 'M',
                'allergies': ['penicillin'],
                'current_medications': ['metformin', 'lisinopril']
            }
        }
    
    async def _handle_diagnosis_consult(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Handle diagnosis consultation request"""
        symptoms = content.get('symptoms', [])
        patient_context = content.get('patient_context', {})
        
        # In a real implementation, this would perform actual diagnosis
        # For simulation, return possible conditions
        possible_conditions = [
            'viral_upper_respiratory_infection',
            'allergic_reaction',
            'mild_asthma_exacerbation'
        ][:min(2, len(symptoms))]  # Limit to 2 possibilities
        
        return {
            'consultation_id': str(uuid.uuid4()),
            'possible_conditions': possible_conditions,
            'confidence_levels': [0.7, 0.65] if len(possible_conditions) > 1 else [0.75],
            'recommended_tests': ['physical_examination', 'chest_xray'] if symptoms else [],
            'next_steps': ['monitor_symptoms', 'follow_up_if_worsening']
        }
    
    async def _handle_treatment_recommendation(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Handle treatment recommendation request"""
        condition = content.get('condition')
        patient_context = content.get('patient_context', {})
        
        # In a real implementation, this would use clinical decision support
        # For simulation, return standard recommendations
        if condition == 'hypertension':
            recommendations = [
                {'type': 'medication', 'name': 'lisinopril', 'dosage': '10mg daily'},
                {'type': 'lifestyle', 'recommendation': 'reduce sodium intake'},
                {'type': 'lifestyle', 'recommendation': 'increase physical activity'}
            ]
        else:
            recommendations = [
                {'type': 'general', 'recommendation': 'rest and hydration'},
                {'type': 'follow_up', 'recommendation': 'monitor symptoms'}
            ]
        
        return {
            'treatment_plan_id': str(uuid.uuid4()),
            'recommendations': recommendations,
            'precautions': ['monitor_for_adverse_effects', 'follow_up_appointment'],
            'estimated_timeline': '2-4 weeks for initial improvement'
        }
    
    async def _handle_drug_interaction_check(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Handle drug interaction check request"""
        medications = content.get('medications', [])
        
        # In a real implementation, this would check against a drug interaction database
        # For simulation, return known interactions
        known_interactions = {
            ('warfarin', 'ibuprofen'): {'severity': 'high', 'risk': 'increased_bleeding'},
            ('lisinopril', 'potassium'): {'severity': 'moderate', 'risk': 'hyperkalemia'},
            ('simvastatin', 'gemfibrozil'): {'severity': 'high', 'risk': 'rhabdomyolysis'}
        }
        
        interactions = []
        for i, med1 in enumerate(medications):
            for med2 in medications[i+1:]:
                pair = tuple(sorted([med1.lower(), med2.lower()]))
                if pair in known_interactions:
                    interaction = known_interactions[pair]
                    interactions.append({
                        'medication1': med1,
                        'medication2': med2,
                        'severity': interaction['severity'],
                        'risk': interaction['risk']
                    })
        
        return {
            'interaction_check_id': str(uuid.uuid4()),
            'interactions_found': interactions,
            'safe_combinations': len(medications) * (len(medications) - 1) // 2 - len(interactions),
            'recommendations': ['consult_pharmacist' if interactions else 'no_known_interactions']
        }
    
    async def send_medical_request(self, 
                                  recipient_id: str, 
                                  action: str, 
                                  data: Dict[str, Any],
                                  priority: MessagePriority = MessagePriority.NORMAL,
                                  require_compliance: bool = True) -> Optional[Dict[str, Any]]:
        """Send a medical-specific request with compliance checking"""
        if require_compliance and self.compliance_mode:
            # Add compliance metadata
            data['compliance_check'] = True
            data['timestamp'] = datetime.now().isoformat()
            data['origin_agent'] = self.agent_id
        
        # Log the request for audit purposes
        if self.compliance_mode:
            self._log_medical_request(recipient_id, action, data)
        
        return await self.send_request(recipient_id, action, data, priority)
    
    def _log_medical_request(self, recipient_id: str, action: str, data: Dict[str, Any]):
        """Log medical requests for compliance and audit"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'from_agent': self.agent_id,
            'to_agent': recipient_id,
            'action': action,
            'data_keys': list(data.keys()),  # Don't log sensitive data, just keys
            'compliance_mode': self.compliance_mode
        }
        
        # In a real system, this would go to a secure audit log
        print(f"Medical A2A request logged: {log_entry}")
    
    def get_compliance_report(self) -> Dict[str, Any]:
        """Get compliance and audit information"""
        return {
            'agent_id': self.agent_id,
            'compliance_mode': self.compliance_mode,
            'total_requests_handled': len(self.message_log),
            'timestamp': datetime.now().isoformat()
        }


# Global protocol registry
protocol_registry: Dict[str, MedicalA2AProtocol] = {}