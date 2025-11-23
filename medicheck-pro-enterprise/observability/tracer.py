"""
Distributed Tracing for Medical Assistant
Implements tracing for multi-agent workflows with HIPAA compliance
"""
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
import json
import time


class SpanKind(Enum):
    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class SpanStatus(Enum):
    UNSET = "unset"
    OK = "ok"
    ERROR = "error"


class Span:
    """Represents a single trace span"""
    
    def __init__(self, 
                 name: str, 
                 trace_id: str, 
                 parent_span_id: Optional[str] = None,
                 kind: SpanKind = SpanKind.INTERNAL):
        self.span_id = str(uuid.uuid4())
        self.name = name
        self.trace_id = trace_id
        self.parent_span_id = parent_span_id
        self.kind = kind
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.status = SpanStatus.UNSET
        self.attributes: Dict[str, Any] = {}
        self.events: List[Dict[str, Any]] = []
        self.links: List[Dict[str, Any]] = []
        self.error_message: Optional[str] = None
    
    def set_attribute(self, key: str, value: Any):
        """Set an attribute on the span"""
        self.attributes[key] = value
    
    def add_event(self, name: str, timestamp: Optional[float] = None, attributes: Dict[str, Any] = None):
        """Add an event to the span"""
        if timestamp is None:
            timestamp = time.time()
        
        event = {
            'name': name,
            'timestamp': timestamp,
            'attributes': attributes or {}
        }
        self.events.append(event)
    
    def add_link(self, trace_id: str, span_id: str, attributes: Dict[str, Any] = None):
        """Add a link to another span"""
        link = {
            'trace_id': trace_id,
            'span_id': span_id,
            'attributes': attributes or {}
        }
        self.links.append(link)
    
    def set_status(self, status: SpanStatus, message: Optional[str] = None):
        """Set the status of the span"""
        self.status = status
        if message:
            self.error_message = message
    
    def end(self):
        """End the span"""
        self.end_time = time.time()
    
    def duration(self) -> float:
        """Get the duration of the span in seconds"""
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary for serialization"""
        return {
            'span_id': self.span_id,
            'name': self.name,
            'trace_id': self.trace_id,
            'parent_span_id': self.parent_span_id,
            'kind': self.kind.value,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration(),
            'status': self.status.value,
            'error_message': self.error_message,
            'attributes': self.attributes,
            'events': self.events,
            'links': self.links
        }


class TraceContext:
    """Represents the tracing context for a request"""
    
    def __init__(self, trace_id: Optional[str] = None):
        self.trace_id = trace_id or str(uuid.uuid4())
        self.spans: List[Span] = []
        self.current_span: Optional[Span] = None
    
    def start_span(self, name: str, kind: SpanKind = SpanKind.INTERNAL) -> Span:
        """Start a new span"""
        parent_span_id = self.current_span.span_id if self.current_span else None
        span = Span(name, self.trace_id, parent_span_id, kind)
        
        self.spans.append(span)
        previous_span = self.current_span
        self.current_span = span
        
        return span, previous_span
    
    def end_span(self, span: Span, previous_span: Optional[Span] = None):
        """End a span"""
        span.end()
        self.current_span = previous_span
    
    def get_trace_summary(self) -> Dict[str, Any]:
        """Get a summary of the trace"""
        total_duration = sum(span.duration() for span in self.spans)
        error_count = sum(1 for span in self.spans if span.status == SpanStatus.ERROR)
        
        return {
            'trace_id': self.trace_id,
            'span_count': len(self.spans),
            'total_duration': total_duration,
            'error_count': error_count,
            'start_time': min(span.start_time for span in self.spans) if self.spans else None,
            'end_time': max(span.end_time or time.time() for span in self.spans) if self.spans else None
        }


class MedicalTracer:
    """HIPAA-compliant tracer for medical workflows"""
    
    def __init__(self, service_name: str = "medical_assistant"):
        self.service_name = service_name
        self.traces: Dict[str, TraceContext] = {}
        self.max_traces = 1000  # Limit memory usage
        self._lock = asyncio.Lock()
    
    def start_trace(self, trace_id: Optional[str] = None) -> TraceContext:
        """Start a new trace"""
        async with self._lock:
            trace_context = TraceContext(trace_id)
            self.traces[trace_context.trace_id] = trace_context
            
            # Limit the number of stored traces
            if len(self.traces) > self.max_traces:
                # Remove oldest traces
                oldest_trace_ids = sorted(
                    self.traces.keys(), 
                    key=lambda x: min(span.start_time for span in self.traces[x].spans)
                )[:-self.max_traces+1]
                
                for trace_id in oldest_trace_ids:
                    del self.traces[trace_id]
            
            return trace_context
    
    def get_trace(self, trace_id: str) -> Optional[TraceContext]:
        """Get a trace by ID"""
        return self.traces.get(trace_id)
    
    def get_trace_spans(self, trace_id: str) -> List[Dict[str, Any]]:
        """Get all spans for a trace as dictionaries"""
        trace_context = self.get_trace(trace_id)
        if not trace_context:
            return []
        
        return [span.to_dict() for span in trace_context.spans]
    
    def get_all_traces_summary(self) -> List[Dict[str, Any]]:
        """Get summaries of all traces"""
        return [trace.get_trace_summary() for trace in self.traces.values()]
    
    async def export_trace(self, trace_id: str, exporter_func) -> bool:
        """Export a trace using the provided exporter function"""
        trace_context = self.get_trace(trace_id)
        if not trace_context:
            return False
        
        try:
            await exporter_func(trace_context)
            return True
        except Exception:
            return False


class MedicalSpan:
    """Context manager for creating spans in medical workflows"""
    
    def __init__(self, tracer: MedicalTracer, name: str, kind: SpanKind = SpanKind.INTERNAL, trace_id: Optional[str] = None):
        self.tracer = tracer
        self.name = name
        self.kind = kind
        self.trace_id = trace_id
        self.trace_context: Optional[TraceContext] = None
        self.span: Optional[Span] = None
        self.previous_span: Optional[Span] = None
    
    async def __aenter__(self):
        """Enter the async context"""
        if self.trace_id:
            # Try to get existing trace
            self.trace_context = self.tracer.get_trace(self.trace_id)
            if not self.trace_context:
                # Create new trace with provided ID
                self.trace_context = self.tracer.start_trace(self.trace_id)
        else:
            # Start new trace
            self.trace_context = self.tracer.start_trace()
        
        self.span, self.previous_span = self.trace_context.start_span(self.name, self.kind)
        return self.span
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context"""
        if self.span:
            if exc_type is not None:
                self.span.set_status(SpanStatus.ERROR, str(exc_val))
            else:
                self.span.set_status(SpanStatus.OK)
            
            self.trace_context.end_span(self.span, self.previous_span)


class AgentTracer(MedicalTracer):
    """Tracer specialized for multi-agent medical systems"""
    
    def __init__(self, service_name: str = "medical_agents"):
        super().__init__(service_name)
        self.agent_spans: Dict[str, List[str]] = {}  # agent_id -> [span_ids]
    
    def record_agent_span(self, agent_id: str, span_id: str):
        """Record that an agent was involved in a span"""
        if agent_id not in self.agent_spans:
            self.agent_spans[agent_id] = []
        self.agent_spans[agent_id].append(span_id)
    
    def get_agent_traces(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all traces involving a specific agent"""
        if agent_id not in self.agent_spans:
            return []
        
        trace_ids = set()
        for span_id in self.agent_spans[agent_id]:
            for trace_id, trace_ctx in self.traces.items():
                if any(span.span_id == span_id for span in trace_ctx.spans):
                    trace_ids.add(trace_id)
        
        result = []
        for trace_id in trace_ids:
            trace_ctx = self.get_trace(trace_id)
            if trace_ctx:
                result.append({
                    'trace': trace_ctx.get_trace_summary(),
                    'spans': [span.to_dict() for span in trace_ctx.spans]
                })
        
        return result
    
    async def trace_agent_execution(self, 
                                   agent_id: str, 
                                   operation: str, 
                                   execute_func, 
                                   *args, 
                                   trace_id: Optional[str] = None, 
                                   **kwargs):
        """Execute a function with tracing for agent operations"""
        async with MedicalSpan(self, f"{agent_id}.{operation}", trace_id=trace_id) as span:
            # Record agent involvement
            self.record_agent_span(agent_id, span.span_id)
            
            # Add agent-specific attributes
            span.set_attribute("agent.id", agent_id)
            span.set_attribute("operation", operation)
            
            try:
                result = await execute_func(*args, **kwargs)
                span.set_attribute("result.status", "success")
                return result
            except Exception as e:
                span.set_attribute("result.status", "error")
                span.set_attribute("error.message", str(e))
                span.set_status(SpanStatus.ERROR, str(e))
                raise


# Global tracer instance
medical_tracer = AgentTracer()