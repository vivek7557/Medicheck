"""
Metrics Collection for Medical Assistant
Implements Prometheus-compatible metrics for monitoring
"""
import time
import asyncio
from typing import Dict, Any, Optional, Union, List
from enum import Enum
from datetime import datetime
import json
import re


class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class BaseMetric:
    """Base class for all metrics"""
    
    def __init__(self, name: str, description: str, labels: Optional[List[str]] = None):
        self.name = name
        self.description = description
        self.labels = labels or []
        self.type = MetricType.GAUGE  # Default type
    
    def get_value(self) -> Union[int, float, Dict[str, Any]]:
        """Get the current value of the metric"""
        raise NotImplementedError


class Counter(BaseMetric):
    """Counter metric that only goes up"""
    
    def __init__(self, name: str, description: str, labels: Optional[List[str]] = None):
        super().__init__(name, description, labels)
        self.type = MetricType.COUNTER
        self._value = 0.0
        self._lock = asyncio.Lock()
    
    async def inc(self, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment the counter"""
        async with self._lock:
            self._value += value
    
    def get_value(self) -> float:
        return self._value


class Gauge(BaseMetric):
    """Gauge metric that can go up and down"""
    
    def __init__(self, name: str, description: str, labels: Optional[List[str]] = None):
        super().__init__(name, description, labels)
        self.type = MetricType.GAUGE
        self._value = 0.0
        self._lock = asyncio.Lock()
    
    async def set(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Set the gauge value"""
        async with self._lock:
            self._value = value
    
    async def inc(self, value: float = 1.0):
        """Increment the gauge"""
        async with self._lock:
            self._value += value
    
    async def dec(self, value: float = 1.0):
        """Decrement the gauge"""
        async with self._lock:
            self._value -= value
    
    def get_value(self) -> float:
        return self._value


class Histogram(BaseMetric):
    """Histogram metric for measuring distributions"""
    
    def __init__(self, name: str, description: str, labels: Optional[List[str]] = None, buckets: Optional[List[float]] = None):
        super().__init__(name, description, labels)
        self.type = MetricType.HISTOGRAM
        self.buckets = buckets or [0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0]
        self._sum = 0.0
        self._count = 0
        self._buckets_counts = {bucket: 0 for bucket in self.buckets}
        self._buckets_counts[float('inf')] = 0  # +Inf bucket
        self._lock = asyncio.Lock()
    
    async def observe(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Observe a value"""
        async with self._lock:
            self._sum += value
            self._count += 1
            
            # Update bucket counts
            for bucket in self.buckets:
                if value <= bucket:
                    self._buckets_counts[bucket] += 1
            self._buckets_counts[float('inf')] += 1  # Always increment +Inf bucket
    
    def get_value(self) -> Dict[str, Any]:
        return {
            'sum': self._sum,
            'count': self._count,
            'buckets': self._buckets_counts
        }


class Summary(BaseMetric):
    """Summary metric for quantiles"""
    
    def __init__(self, name: str, description: str, labels: Optional[List[str]] = None):
        super().__init__(name, description, labels)
        self.type = MetricType.SUMMARY
        self._values = []
        self._lock = asyncio.Lock()
    
    async def observe(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Observe a value"""
        async with self._lock:
            self._values.append(value)
            # Keep only the last 1000 values to prevent memory issues
            if len(self._values) > 1000:
                self._values = self._values[-1000:]
    
    def get_value(self) -> Dict[str, Any]:
        if not self._values:
            return {'count': 0, 'sum': 0.0, 'quantiles': {}}
        
        sorted_values = sorted(self._values)
        count = len(sorted_values)
        sum_val = sum(sorted_values)
        
        # Calculate quantiles (simplified)
        quantiles = {}
        for q in [0.5, 0.9, 0.95, 0.99]:
            idx = int(q * (count - 1))
            quantiles[f'q{int(q*100)}'] = sorted_values[idx] if sorted_values else 0.0
        
        return {
            'count': count,
            'sum': sum_val,
            'quantiles': quantiles
        }


class MedicalMetricsRegistry:
    """Registry for all medical metrics"""
    
    def __init__(self):
        self.metrics: Dict[str, BaseMetric] = {}
        self._lock = asyncio.Lock()
    
    async def register(self, metric: BaseMetric):
        """Register a new metric"""
        async with self._lock:
            if metric.name in self.metrics:
                raise ValueError(f"Metric {metric.name} already registered")
            self.metrics[metric.name] = metric
    
    async def get_metric(self, name: str) -> Optional[BaseMetric]:
        """Get a metric by name"""
        return self.metrics.get(name)
    
    def get_all_metrics(self) -> Dict[str, BaseMetric]:
        """Get all metrics"""
        return self.metrics.copy()
    
    def to_prometheus_format(self) -> str:
        """Export metrics in Prometheus text format"""
        result = []
        
        for name, metric in self.metrics.items():
            # Add comment with description
            result.append(f"# HELP {name} {metric.description}")
            result.append(f"# TYPE {name} {metric.type.value}")
            
            # Format the metric value
            value = metric.get_value()
            if isinstance(value, (int, float)):
                result.append(f"{name} {value}")
            elif isinstance(value, dict):
                if metric.type == MetricType.HISTOGRAM:
                    # Histogram format
                    for bucket, count in value['buckets'].items():
                        if bucket == float('inf'):
                            result.append(f"{name}_bucket{{le=\"+Inf\"}} {count}")
                        else:
                            result.append(f"{name}_bucket{{le=\"{bucket}\"}} {count}")
                    result.append(f"{name}_count {value['count']}")
                    result.append(f"{name}_sum {value['sum']}")
                elif metric.type == MetricType.SUMMARY:
                    # Summary format
                    result.append(f"{name}_count {value['count']}")
                    result.append(f"{name}_sum {value['sum']}")
                    for quantile, val in value['quantiles'].items():
                        q_val = quantile.replace('q', '').replace('p', '')
                        result.append(f"{name}_quantile{{quantile=\"{q_val}\"}} {val}")
            result.append("")
        
        return "\n".join(result)


class MedicalMetricsCollector:
    """Collects and manages medical-specific metrics"""
    
    def __init__(self):
        self.registry = MedicalMetricsRegistry()
        self._setup_default_metrics()
    
    def _setup_default_metrics(self):
        """Setup default medical metrics"""
        # Agent metrics
        asyncio.create_task(self.registry.register(
            Counter("agent_requests_total", "Total number of requests to agents", ["agent", "type"])
        ))
        asyncio.create_task(self.registry.register(
            Histogram("agent_request_duration_seconds", "Duration of agent requests", ["agent"], [0.1, 0.5, 1.0, 2.0, 5.0])
        ))
        asyncio.create_task(self.registry.register(
            Counter("agent_errors_total", "Total number of agent errors", ["agent", "error_type"])
        ))
        
        # Patient metrics
        asyncio.create_task(self.registry.register(
            Counter("patient_interactions_total", "Total number of patient interactions", ["interaction_type"])
        ))
        asyncio.create_task(self.registry.register(
            Gauge("active_patients", "Number of currently active patients")
        ))
        
        # System metrics
        asyncio.create_task(self.registry.register(
            Gauge("system_uptime_seconds", "System uptime in seconds")
        ))
        asyncio.create_task(self.registry.register(
            Counter("system_errors_total", "Total number of system errors", ["error_type"])
        ))
        
        # Memory metrics
        asyncio.create_task(self.registry.register(
            Gauge("memory_usage_bytes", "Current memory usage in bytes")
        ))
        asyncio.create_task(self.registry.register(
            Gauge("vector_store_size", "Current size of vector store")
        ))
    
    async def increment_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        metric = await self.registry.get_metric(name)
        if metric and isinstance(metric, Counter):
            await metric.inc(value, labels)
    
    async def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set a gauge metric"""
        metric = await self.registry.get_metric(name)
        if metric and isinstance(metric, Gauge):
            await metric.set(value, labels)
    
    async def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Observe a value in a histogram"""
        metric = await self.registry.get_metric(name)
        if metric and isinstance(metric, Histogram):
            await metric.observe(value, labels)
    
    async def observe_summary(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Observe a value in a summary"""
        metric = await self.registry.get_metric(name)
        if metric and isinstance(metric, Summary):
            await metric.observe(value, labels)
    
    def get_prometheus_metrics(self) -> str:
        """Get metrics in Prometheus format"""
        return self.registry.to_prometheus_format()
    
    async def start_uptime_counter(self):
        """Start tracking system uptime"""
        start_time = time.time()
        
        async def update_uptime():
            while True:
                uptime = time.time() - start_time
                await self.set_gauge("system_uptime_seconds", uptime)
                await asyncio.sleep(60)  # Update every minute
        
        asyncio.create_task(update_uptime())


class AgentMetricsCollector(MedicalMetricsCollector):
    """Metrics collector specialized for multi-agent systems"""
    
    def __init__(self):
        super().__init__()
        self.agent_start_times: Dict[str, float] = {}
    
    async def record_agent_request(self, agent_name: str, request_type: str, duration: float, success: bool = True):
        """Record an agent request"""
        # Increment request counter
        await self.increment_counter(
            "agent_requests_total", 
            1.0, 
            {"agent": agent_name, "type": request_type}
        )
        
        # Record duration
        await self.observe_histogram(
            "agent_request_duration_seconds",
            duration,
            {"agent": agent_name}
        )
        
        # Record error if not successful
        if not success:
            await self.increment_counter(
                "agent_errors_total",
                1.0,
                {"agent": agent_name, "error_type": "request_failed"}
            )
    
    async def record_medical_action(self, action_type: str, agent_name: str, success: bool = True):
        """Record a medical action"""
        await self.increment_counter(
            "patient_interactions_total",
            1.0,
            {"interaction_type": action_type}
        )
        
        if not success:
            await self.increment_counter(
                "agent_errors_total",
                1.0,
                {"agent": agent_name, "error_type": f"medical_action_failed_{action_type}"}
            )
    
    async def record_vector_store_operation(self, operation: str, size_change: int = 0):
        """Record a vector store operation"""
        await self.increment_counter(
            f"vector_store_{operation}_total",
            1.0
        )
        
        if size_change != 0:
            current_size = (await self.registry.get_metric("vector_store_size")).get_value() if await self.registry.get_metric("vector_store_size") else 0
            await self.set_gauge("vector_store_size", current_size + size_change)


# Global metrics collector
medical_metrics = AgentMetricsCollector()