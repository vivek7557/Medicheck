"""
Message Bus for Medical Assistant
Implements a publish-subscribe message bus for agent communication
"""
import asyncio
import json
import uuid
from typing import Dict, Any, Optional, List, Callable, Set
from datetime import datetime
from enum import Enum
import hashlib
import hmac
import base64
from dataclasses import dataclass


class MessageBusChannel(Enum):
    TRIAGE = "triage"
    DIAGNOSIS = "diagnosis"
    TREATMENT = "treatment"
    RESEARCH = "research"
    SYSTEM = "system"
    EMERGENCY = "emergency"


@dataclass
class BusMessage:
    """Represents a message in the message bus"""
    message_id: str
    channel: MessageBusChannel
    content: Dict[str, Any]
    sender_id: str
    timestamp: datetime
    priority: int = 1  # Higher number = higher priority
    expiration: Optional[datetime] = None
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            'message_id': self.message_id,
            'channel': self.channel.value,
            'content': self.content,
            'sender_id': self.sender_id,
            'timestamp': self.timestamp.isoformat(),
            'priority': self.priority,
            'expiration': self.expiration.isoformat() if self.expiration else None,
            'correlation_id': self.correlation_id,
            'reply_to': self.reply_to,
            'metadata': self.metadata or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BusMessage':
        """Create message from dictionary"""
        return cls(
            message_id=data['message_id'],
            channel=MessageBusChannel(data['channel']),
            content=data['content'],
            sender_id=data['sender_id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            priority=data.get('priority', 1),
            expiration=datetime.fromisoformat(data['expiration']) if data.get('expiration') else None,
            correlation_id=data.get('correlation_id'),
            reply_to=data.get('reply_to'),
            metadata=data.get('metadata')
        )


class MessageFilter:
    """Filter for message subscription"""
    
    def __init__(self, 
                 channel: Optional[MessageBusChannel] = None,
                 sender_id: Optional[str] = None,
                 content_filter: Optional[Callable[[Dict[str, Any]], bool]] = None):
        self.channel = channel
        self.sender_id = sender_id
        self.content_filter = content_filter
    
    def matches(self, message: BusMessage) -> bool:
        """Check if message matches the filter"""
        if self.channel and message.channel != self.channel:
            return False
        if self.sender_id and message.sender_id != self.sender_id:
            return False
        if self.content_filter and not self.content_filter(message.content):
            return False
        return True


class MessageSubscriber:
    """Represents a message subscriber"""
    
    def __init__(self, subscriber_id: str, handler: Callable[[BusMessage], None]):
        self.subscriber_id = subscriber_id
        self.handler = handler
        self.active = True
        self.last_heartbeat = datetime.now()
    
    def heartbeat(self):
        """Update heartbeat to show subscriber is active"""
        self.last_heartbeat = datetime.now()
    
    def is_active(self, timeout_seconds: int = 300) -> bool:  # 5 minutes default
        """Check if subscriber is still active"""
        return (datetime.now() - self.last_heartbeat).seconds < timeout_seconds


class MessageBus:
    """Publish-subscribe message bus for agent communication"""
    
    def __init__(self):
        self.channels: Dict[MessageBusChannel, List[BusMessage]] = {channel: [] for channel in MessageBusChannel}
        self.subscribers: Dict[str, List[MessageSubscriber]] = {channel: [] for channel in MessageBusChannel}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self._lock = asyncio.Lock()
        self.running = False
    
    async def start(self):
        """Start the message bus"""
        self.running = True
        asyncio.create_task(self._message_processor())
    
    async def stop(self):
        """Stop the message bus"""
        self.running = False
    
    async def _message_processor(self):
        """Background task to process messages"""
        while self.running:
            try:
                # Get message from queue
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                
                # Publish to appropriate channel
                await self._publish_to_channel(message)
                
                # Clean up expired messages
                await self._cleanup_expired_messages()
                
                # Clean up inactive subscribers
                await self._cleanup_inactive_subscribers()
                
            except asyncio.TimeoutError:
                continue  # Check if still running
    
    async def publish(self, 
                     channel: MessageBusChannel, 
                     content: Dict[str, Any], 
                     sender_id: str,
                     priority: int = 1,
                     expiration_seconds: Optional[int] = None,
                     correlation_id: Optional[str] = None,
                     reply_to: Optional[str] = None) -> str:
        """Publish a message to a channel"""
        message = BusMessage(
            message_id=str(uuid.uuid4()),
            channel=channel,
            content=content,
            sender_id=sender_id,
            timestamp=datetime.now(),
            priority=priority,
            expiration=datetime.now() + timedelta(seconds=expiration_seconds) if expiration_seconds else None,
            correlation_id=correlation_id,
            reply_to=reply_to
        )
        
        await self.message_queue.put(message)
        return message.message_id
    
    async def _publish_to_channel(self, message: BusMessage):
        """Publish message to channel and notify subscribers"""
        async with self._lock:
            # Add to channel
            self.channels[message.channel].append(message)
            
            # Notify subscribers
            for subscriber in self.subscribers[message.channel]:
                if subscriber.active and subscriber.is_active():
                    try:
                        # Run subscriber handler in background to avoid blocking
                        asyncio.create_task(subscriber.handler(message))
                        subscriber.heartbeat()
                    except Exception as e:
                        print(f"Error in subscriber {subscriber.subscriber_id}: {e}")
    
    async def subscribe(self, 
                       filter_obj: MessageFilter, 
                       handler: Callable[[BusMessage], None]) -> str:
        """Subscribe to messages with a filter"""
        subscriber_id = str(uuid.uuid4())
        subscriber = MessageSubscriber(subscriber_id, handler)
        
        # Add to all relevant channels
        channels_to_subscribe = [filter_obj.channel] if filter_obj.channel else MessageBusChannel
        for channel in channels_to_subscribe:
            self.subscribers[channel].append(subscriber)
        
        return subscriber_id
    
    async def unsubscribe(self, subscriber_id: str):
        """Unsubscribe from messages"""
        async with self._lock:
            for channel_subscribers in self.subscribers.values():
                channel_subscribers[:] = [s for s in channel_subscribers if s.subscriber_id != subscriber_id]
    
    async def request_reply(self, 
                           channel: MessageBusChannel,
                           content: Dict[str, Any],
                           sender_id: str,
                           timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Send a request and wait for a reply"""
        correlation_id = str(uuid.uuid4())
        reply_future = asyncio.Future()
        
        # Subscribe to replies with this correlation ID
        def reply_handler(message: BusMessage):
            if message.correlation_id == correlation_id and message.sender_id != sender_id:
                if not reply_future.done():
                    reply_future.set_result(message.content)
        
        # Add temporary subscriber
        temp_subscriber_id = await self.subscribe(
            MessageFilter(channel=channel, content_filter=lambda x: x.get('correlation_id') == correlation_id),
            reply_handler
        )
        
        # Send request
        await self.publish(
            channel=channel,
            content={**content, 'correlation_id': correlation_id, 'message_type': 'request'},
            sender_id=sender_id
        )
        
        try:
            # Wait for reply
            result = await asyncio.wait_for(reply_future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            return None
        finally:
            # Clean up temporary subscriber
            await self.unsubscribe(temp_subscriber_id)
    
    async def _cleanup_expired_messages(self):
        """Remove expired messages from channels"""
        now = datetime.now()
        async with self._lock:
            for channel in MessageBusChannel:
                self.channels[channel] = [
                    msg for msg in self.channels[channel] 
                    if not msg.expiration or msg.expiration > now
                ]
    
    async def _cleanup_inactive_subscribers(self):
        """Remove inactive subscribers"""
        async with self._lock:
            for channel in MessageBusChannel:
                self.subscribers[channel] = [
                    sub for sub in self.subscribers[channel] 
                    if sub.is_active()
                ]


from datetime import timedelta

class MedicalMessageBus(MessageBus):
    """Medical-specific message bus with HIPAA compliance and emergency handling"""
    
    def __init__(self):
        super().__init__()
        self.emergency_queue: asyncio.Queue = asyncio.Queue()
        self.audit_log: List[Dict[str, Any]] = []
        self.patient_contexts: Dict[str, Dict[str, Any]] = {}  # patient_id -> context
    
    async def publish_medical_message(self,
                                    channel: MessageBusChannel,
                                    content: Dict[str, Any],
                                    sender_id: str,
                                    patient_id: Optional[str] = None,
                                    priority: int = 1,
                                    requires_compliance: bool = True) -> str:
        """Publish a medical message with compliance checking"""
        # Add compliance metadata if required
        if requires_compliance:
            content['compliance_metadata'] = {
                'timestamp': datetime.now().isoformat(),
                'sender_id': sender_id,
                'requires_acknowledgment': True
            }
        
        # Add patient context if provided
        if patient_id:
            content['patient_context'] = self.patient_contexts.get(patient_id, {})
            content['patient_id'] = patient_id
        
        # Handle emergency messages specially
        if channel == MessageBusChannel.EMERGENCY:
            message_id = await self._publish_emergency_message(content, sender_id)
        else:
            message_id = await self.publish(channel, content, sender_id, priority)
        
        # Log for audit trail
        await self._log_medical_message(message_id, channel, content, sender_id)
        
        return message_id
    
    async def _publish_emergency_message(self, content: Dict[str, Any], sender_id: str) -> str:
        """Handle emergency message publication with priority processing"""
        message = BusMessage(
            message_id=str(uuid.uuid4()),
            channel=MessageBusChannel.EMERGENCY,
            content=content,
            sender_id=sender_id,
            timestamp=datetime.now(),
            priority=10,  # Highest priority
            expiration=datetime.now() + timedelta(minutes=5)  # 5 minute expiration for emergencies
        )
        
        # Put in emergency queue for immediate processing
        await self.emergency_queue.put(message)
        
        # Also add to regular channel
        async with self._lock:
            self.channels[MessageBusChannel.EMERGENCY].append(message)
            
            # Notify emergency subscribers
            for subscriber in self.subscribers[MessageBusChannel.EMERGENCY]:
                if subscriber.active and subscriber.is_active():
                    try:
                        asyncio.create_task(subscriber.handler(message))
                        subscriber.heartbeat()
                    except Exception as e:
                        print(f"Error in emergency subscriber {subscriber.subscriber_id}: {e}")
        
        return message.message_id
    
    async def subscribe_medical(self,
                               filter_obj: MessageFilter,
                               handler: Callable[[BusMessage], None],
                               requires_compliance: bool = True) -> str:
        """Subscribe to medical messages with compliance checking"""
        async def compliance_handler(message: BusMessage):
            # Check compliance if required
            if requires_compliance:
                if 'compliance_metadata' not in message.content:
                    print(f"Non-compliant message received from {message.sender_id}")
                    return  # Skip non-compliant messages
            
            # Process the message
            await handler(message)
        
        return await self.subscribe(filter_obj, compliance_handler)
    
    async def _log_medical_message(self, message_id: str, channel: MessageBusChannel, 
                                 content: Dict[str, Any], sender_id: str):
        """Log medical message for audit trail"""
        log_entry = {
            'log_id': str(uuid.uuid4()),
            'message_id': message_id,
            'channel': channel.value,
            'sender_id': sender_id,
            'timestamp': datetime.now().isoformat(),
            'has_patient_data': 'patient_id' in content or 'patient_context' in content,
            'message_type': content.get('message_type', 'standard'),
            'compliance_check': 'compliance_metadata' in content
        }
        
        self.audit_log.append(log_entry)
        
        # Keep audit log size manageable
        if len(self.audit_log) > 10000:  # Keep last 10k entries
            self.audit_log = self.audit_log[-5000:]  # Keep 5k after trim
    
    def get_audit_trail(self, 
                       patient_id: Optional[str] = None,
                       start_time: Optional[datetime] = None,
                       end_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get audit trail filtered by criteria"""
        filtered_logs = self.audit_log.copy()
        
        if patient_id:
            # This would require patient_id to be stored in the log entry
            # For now, we'll return all logs as patient_id is not stored in this example
            pass
        
        if start_time:
            filtered_logs = [log for log in filtered_logs 
                           if datetime.fromisoformat(log['timestamp']) >= start_time]
        
        if end_time:
            filtered_logs = [log for log in filtered_logs 
                           if datetime.fromisoformat(log['timestamp']) <= end_time]
        
        return filtered_logs
    
    def set_patient_context(self, patient_id: str, context: Dict[str, Any]):
        """Set patient context for medical messages"""
        self.patient_contexts[patient_id] = context
    
    def get_patient_context(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get patient context"""
        return self.patient_contexts.get(patient_id)
    
    async def broadcast_patient_update(self, patient_id: str, update_type: str, data: Dict[str, Any]):
        """Broadcast a patient update to all relevant agents"""
        content = {
            'patient_id': patient_id,
            'update_type': update_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        # Send to relevant channels based on update type
        if update_type in ['vitals', 'symptoms', 'emergency']:
            channel = MessageBusChannel.EMERGENCY
        elif update_type in ['diagnosis', 'condition_change']:
            channel = MessageBusChannel.DIAGNOSIS
        elif update_type in ['medication_change', 'treatment_update']:
            channel = MessageBusChannel.TREATMENT
        else:
            channel = MessageBusChannel.SYSTEM
        
        return await self.publish_medical_message(
            channel=channel,
            content=content,
            sender_id="system",
            patient_id=patient_id
        )
    
    def get_message_statistics(self) -> Dict[str, Any]:
        """Get statistics about message bus usage"""
        total_messages = sum(len(messages) for messages in self.channels.values())
        active_subscribers = sum(
            len([s for s in subs if s.active and s.is_active()]) 
            for subs in self.subscribers.values()
        )
        
        channel_counts = {
            channel.value: len(messages) 
            for channel, messages in self.channels.items()
        }
        
        return {
            'total_messages': total_messages,
            'active_subscribers': active_subscribers,
            'channel_distribution': channel_counts,
            'audit_log_size': len(self.audit_log),
            'timestamp': datetime.now().isoformat()
        }


# Global message bus instance
medical_message_bus = MedicalMessageBus()