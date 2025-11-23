"""
Service Mesh for Medical Assistant
Implements service-to-service communication with security and resilience
"""
import asyncio
import json
import uuid
from typing import Dict, Any, Optional, List, Callable, Tuple
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import hmac
import base64
import ssl
from dataclasses import dataclass
import aiohttp
from contextlib import asynccontextmanager


class ServiceType(Enum):
    TRIAGE = "triage"
    DIAGNOSIS = "diagnosis"
    TREATMENT = "treatment"
    RESEARCH = "research"
    DATABASE = "database"
    AUTH = "auth"
    MONITORING = "monitoring"


@dataclass
class ServiceEndpoint:
    """Represents a service endpoint"""
    service_id: str
    service_type: ServiceType
    host: str
    port: int
    ssl_enabled: bool = True
    health_check_path: str = "/health"
    version: str = "1.0.0"
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ServiceMeshRequest:
    """Represents a request in the service mesh"""
    request_id: str
    service_id: str
    endpoint: str
    method: str
    headers: Dict[str, str]
    body: Optional[Dict[str, Any]] = None
    timeout: int = 30
    retries: int = 3
    priority: int = 1  # Higher number = higher priority


@dataclass
class ServiceMeshResponse:
    """Represents a response from the service mesh"""
    request_id: str
    status_code: int
    headers: Dict[str, str]
    body: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class CircuitBreakerState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Tripped, requests failing fast
    HALF_OPEN = "half_open"  # Testing if service is recovered


class CircuitBreaker:
    """Circuit breaker implementation for service resilience"""
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 timeout: int = 60,
                 success_threshold: int = 3):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.success_threshold = success_threshold
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitBreakerState.CLOSED
        self.success_count = 0
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute a function with circuit breaker protection"""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    async def async_call(self, func: Callable, *args, **kwargs):
        """Execute an async function with circuit breaker protection"""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.last_failure_time = None
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.success_count = 0
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit"""
        if self.last_failure_time is None:
            return False
        return (datetime.now() - self.last_failure_time).seconds >= self.timeout


class ServiceRegistry:
    """Registry for service discovery and health monitoring"""
    
    def __init__(self):
        self.services: Dict[str, ServiceEndpoint] = {}
        self.service_health: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def register_service(self, endpoint: ServiceEndpoint):
        """Register a service endpoint"""
        async with self._lock:
            self.services[endpoint.service_id] = endpoint
            self.service_health[endpoint.service_id] = {
                'status': 'unknown',
                'last_check': datetime.now(),
                'failure_count': 0
            }
    
    async def deregister_service(self, service_id: str):
        """Deregister a service"""
        async with self._lock:
            if service_id in self.services:
                del self.services[service_id]
            if service_id in self.service_health:
                del self.service_health[service_id]
    
    def get_service(self, service_id: str) -> Optional[ServiceEndpoint]:
        """Get a service endpoint by ID"""
        return self.services.get(service_id)
    
    def get_services_by_type(self, service_type: ServiceType) -> List[ServiceEndpoint]:
        """Get all services of a specific type"""
        return [endpoint for endpoint in self.services.values() 
                if endpoint.service_type == service_type]
    
    def get_all_services(self) -> List[ServiceEndpoint]:
        """Get all registered services"""
        return list(self.services.values())
    
    async def update_service_health(self, service_id: str, status: str, details: Dict[str, Any] = None):
        """Update service health status"""
        async with self._lock:
            if service_id in self.service_health:
                self.service_health[service_id].update({
                    'status': status,
                    'last_check': datetime.now(),
                    'details': details
                })
    
    def get_healthy_services(self, service_type: ServiceType) -> List[ServiceEndpoint]:
        """Get all healthy services of a specific type"""
        healthy_services = []
        for endpoint in self.get_services_by_type(service_type):
            health_info = self.service_health.get(endpoint.service_id, {})
            if health_info.get('status') == 'healthy':
                healthy_services.append(endpoint)
        return healthy_services


class ServiceMesh:
    """Main service mesh implementation"""
    
    def __init__(self):
        self.registry = ServiceRegistry()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.request_timeout = 30
        self.max_retries = 3
        self._http_session: Optional[aiohttp.ClientSession] = None
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """Initialize the service mesh"""
        if self._http_session is None:
            self._http_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.request_timeout)
            )
    
    async def cleanup(self):
        """Clean up resources"""
        if self._http_session:
            await self._http_session.close()
    
    async def register_service(self, endpoint: ServiceEndpoint):
        """Register a service endpoint"""
        await self.registry.register_service(endpoint)
        # Create circuit breaker for this service
        self.circuit_breakers[endpoint.service_id] = CircuitBreaker()
    
    async def make_request(self, 
                          service_id: str, 
                          endpoint: str, 
                          method: str = 'GET',
                          body: Optional[Dict[str, Any]] = None,
                          headers: Optional[Dict[str, str]] = None,
                          timeout: int = 30,
                          retries: int = 3) -> ServiceMeshResponse:
        """Make a request to a service through the mesh"""
        if not self._http_session:
            await self.initialize()
        
        service = self.registry.get_service(service_id)
        if not service:
            raise ValueError(f"Service {service_id} not found in registry")
        
        # Get or create circuit breaker for this service
        circuit_breaker = self.circuit_breakers.get(service_id)
        if not circuit_breaker:
            circuit_breaker = CircuitBreaker()
            self.circuit_breakers[service_id] = circuit_breaker
        
        request_id = str(uuid.uuid4())
        
        # Prepare headers
        headers = headers or {}
        headers['X-Request-ID'] = request_id
        headers['Content-Type'] = 'application/json'
        
        # Add security headers
        headers['X-Service-Mesh'] = 'true'
        headers['X-Service-Version'] = service.version
        
        # Make the actual request with retries and circuit breaker
        last_exception = None
        
        for attempt in range(retries + 1):
            try:
                # Use circuit breaker
                response = await circuit_breaker.async_call(
                    self._make_http_request,
                    service, endpoint, method, headers, body, timeout
                )
                
                # Update service health
                await self.registry.update_service_health(service_id, 'healthy')
                
                return response
                
            except Exception as e:
                last_exception = e
                
                # Update service health on failure
                await self.registry.update_service_health(
                    service_id, 'unhealthy', {'error': str(e), 'attempt': attempt + 1}
                )
                
                if attempt < retries:
                    # Wait before retry with exponential backoff
                    await asyncio.sleep(2 ** attempt)
                else:
                    # All retries exhausted
                    raise last_exception
    
    async def _make_http_request(self,
                                service: ServiceEndpoint,
                                endpoint: str,
                                method: str,
                                headers: Dict[str, str],
                                body: Optional[Dict[str, Any]],
                                timeout: int) -> ServiceMeshResponse:
        """Make the actual HTTP request"""
        url = f"{'https' if service.ssl_enabled else 'http'}://{service.host}:{service.port}{endpoint}"
        
        async with self._http_session.request(
            method=method,
            url=url,
            headers=headers,
            json=body,
            timeout=aiohttp.ClientTimeout(total=timeout)
        ) as response:
            response_body = None
            if response.content_type == 'application/json':
                try:
                    response_body = await response.json()
                except:
                    pass  # Ignore JSON parsing errors
            
            return ServiceMeshResponse(
                request_id=headers.get('X-Request-ID', ''),
                status_code=response.status,
                headers=dict(response.headers),
                body=response_body
            )
    
    def get_service_health(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Get health information for a service"""
        return self.registry.service_health.get(service_id)
    
    def get_all_service_health(self) -> Dict[str, Dict[str, Any]]:
        """Get health information for all services"""
        return self.registry.service_health.copy()


class MedicalServiceMesh(ServiceMesh):
    """Medical-specific service mesh with additional security and compliance features"""
    
    def __init__(self):
        super().__init__()
        self.encryption_keys: Dict[str, str] = {}
        self.audit_log: List[Dict[str, Any]] = []
        self.patient_access_log: Dict[str, List[Dict[str, Any]]] = {}  # patient_id -> access log
        self.security_policies: Dict[str, Any] = self._default_security_policies()
    
    def _default_security_policies(self) -> Dict[str, Any]:
        """Define default security policies"""
        return {
            'encryption_required': True,
            'authentication_required': True,
            'audit_logging_required': True,
            'patient_data_masking': True,
            'access_control': {
                'triage': ['diagnosis', 'treatment'],
                'diagnosis': ['treatment', 'research'],
                'treatment': ['database'],
                'research': ['database']
            }
        }
    
    async def register_medical_service(self, endpoint: ServiceEndpoint, encryption_key: Optional[str] = None):
        """Register a medical service with additional security"""
        await self.register_service(endpoint)
        
        # Store encryption key if provided
        if encryption_key:
            self.encryption_keys[endpoint.service_id] = encryption_key
    
    async def make_medical_request(self,
                                  service_id: str,
                                  endpoint: str,
                                  method: str = 'GET',
                                  body: Optional[Dict[str, Any]] = None,
                                  headers: Optional[Dict[str, str]] = None,
                                  patient_id: Optional[str] = None,
                                  require_auth: bool = True,
                                  encrypt_body: bool = True) -> ServiceMeshResponse:
        """Make a medical request with additional security and compliance"""
        # Add security headers
        headers = headers or {}
        
        if require_auth:
            headers['Authorization'] = await self._generate_auth_token(service_id)
        
        # Encrypt body if required and contains patient data
        if encrypt_body and body and self._contains_patient_data(body):
            body = await self._encrypt_body(body, service_id)
            headers['X-Encrypted'] = 'true'
        
        # Add patient context if provided
        if patient_id:
            headers['X-Patient-ID'] = patient_id
            headers['X-Patient-Access'] = 'true'
        
        # Add compliance headers
        headers['X-Compliance'] = 'HIPAA'
        headers['X-Trace-ID'] = str(uuid.uuid4())
        
        # Make the request
        response = await self.make_request(
            service_id=service_id,
            endpoint=endpoint,
            method=method,
            body=body,
            headers=headers
        )
        
        # Log the request for audit purposes
        await self._log_medical_request(
            service_id=service_id,
            endpoint=endpoint,
            method=method,
            patient_id=patient_id,
            request_headers=headers,
            response_status=response.status_code
        )
        
        return response
    
    def _contains_patient_data(self, data: Dict[str, Any]) -> bool:
        """Check if data contains patient information"""
        patient_data_keywords = [
            'patient', 'medical', 'diagnosis', 'treatment', 'prescription',
            'symptoms', 'vitals', 'allergies', 'medications', 'condition'
        ]
        
        data_str = json.dumps(data, default=str).lower()
        return any(keyword in data_str for keyword in patient_data_keywords)
    
    async def _encrypt_body(self, body: Dict[str, Any], service_id: str) -> Dict[str, Any]:
        """Encrypt request body using service-specific key"""
        encryption_key = self.encryption_keys.get(service_id)
        if not encryption_key:
            raise ValueError(f"No encryption key found for service {service_id}")
        
        # Simple encryption for demonstration (in real implementation, use proper encryption)
        body_str = json.dumps(body)
        encrypted_str = base64.b64encode(
            hmac.new(
                encryption_key.encode('utf-8'),
                body_str.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        return {'encrypted_data': encrypted_str, 'original_keys': list(body.keys())}
    
    async def _generate_auth_token(self, service_id: str) -> str:
        """Generate authentication token for service-to-service communication"""
        token_data = {
            'service_id': service_id,
            'timestamp': datetime.now().isoformat(),
            'token_id': str(uuid.uuid4())
        }
        
        # Sign the token
        token_str = json.dumps(token_data, sort_keys=True)
        signature = base64.b64encode(
            hmac.new(
                'medical_mesh_secret_key'.encode('utf-8'),
                token_str.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        return f"Bearer {signature}.{base64.b64encode(token_str.encode('utf-8')).decode('utf-8')}"
    
    async def _log_medical_request(self,
                                  service_id: str,
                                  endpoint: str,
                                  method: str,
                                  patient_id: Optional[str],
                                  request_headers: Dict[str, str],
                                  response_status: int):
        """Log medical request for audit and compliance"""
        log_entry = {
            'log_id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'service_id': service_id,
            'endpoint': endpoint,
            'method': method,
            'response_status': response_status,
            'has_patient_data': patient_id is not None,
            'patient_id_hash': hashlib.sha256(patient_id.encode()).hexdigest() if patient_id else None,
            'trace_id': request_headers.get('X-Trace-ID'),
            'compliance_check': request_headers.get('X-Compliance') == 'HIPAA'
        }
        
        self.audit_log.append(log_entry)
        
        # Log patient-specific access
        if patient_id:
            if patient_id not in self.patient_access_log:
                self.patient_access_log[patient_id] = []
            self.patient_access_log[patient_id].append(log_entry)
        
        # Keep audit log size manageable
        if len(self.audit_log) > 10000:  # Keep last 10k entries
            self.audit_log = self.audit_log[-5000:]  # Keep 5k after trim
    
    def get_patient_access_log(self, patient_id: str) -> List[Dict[str, Any]]:
        """Get access log for a specific patient"""
        return self.patient_access_log.get(patient_id, []).copy()
    
    def get_compliance_report(self) -> Dict[str, Any]:
        """Get compliance and audit information"""
        return {
            'total_requests': len(self.audit_log),
            'patient_requests': len([log for log in self.audit_log if log['has_patient_data']]),
            'compliant_requests': len([log for log in self.audit_log if log['compliance_check']]),
            'timestamp': datetime.now().isoformat()
        }
    
    async def route_request_by_specialty(self, 
                                       specialty: ServiceType, 
                                       endpoint: str, 
                                       method: str = 'GET',
                                       body: Optional[Dict[str, Any]] = None,
                                       headers: Optional[Dict[str, str]] = None,
                                       patient_id: Optional[str] = None) -> Optional[ServiceMeshResponse]:
        """Route request to appropriate service based on medical specialty"""
        services = self.registry.get_healthy_services(specialty)
        
        if not services:
            raise ValueError(f"No healthy services available for specialty: {specialty}")
        
        # Load balancing: select service with least load (simplified)
        selected_service = min(services, key=lambda s: self._get_service_load(s.service_id))
        
        return await self.make_medical_request(
            service_id=selected_service.service_id,
            endpoint=endpoint,
            method=method,
            body=body,
            headers=headers,
            patient_id=patient_id
        )
    
    def _get_service_load(self, service_id: str) -> int:
        """Get approximate load for a service (simplified implementation)"""
        # In a real implementation, this would track actual service load
        # For now, return a static value
        return 0


# Global service mesh instance
medical_service_mesh = MedicalServiceMesh()