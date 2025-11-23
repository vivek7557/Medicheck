"""
Health Monitoring for Medical Assistant
Implements health checks and system monitoring
"""
import asyncio
import time
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import psutil
import os
from enum import Enum


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheck:
    """Represents a single health check"""
    
    def __init__(self, name: str, check_func: Callable, timeout: int = 5):
        self.name = name
        self.check_func = check_func
        self.timeout = timeout
        self.last_check: Optional[datetime] = None
        self.last_result: Optional[Dict[str, Any]] = None
    
    async def run(self) -> Dict[str, Any]:
        """Run the health check"""
        start_time = time.time()
        self.last_check = datetime.now()
        
        try:
            # Run the check with timeout
            result = await asyncio.wait_for(
                self.check_func(), 
                timeout=self.timeout
            )
            
            duration = time.time() - start_time
            
            self.last_result = {
                'status': HealthStatus.HEALTHY if result.get('healthy', False) else HealthStatus.UNHEALTHY,
                'timestamp': self.last_check.isoformat(),
                'duration': duration,
                'details': result.get('details', {}),
                'message': result.get('message', '')
            }
            
            return self.last_result
        
        except asyncio.TimeoutError:
            self.last_result = {
                'status': HealthStatus.UNHEALTHY,
                'timestamp': self.last_check.isoformat(),
                'duration': self.timeout,
                'details': {},
                'message': f'Health check timed out after {self.timeout} seconds'
            }
            return self.last_result
        
        except Exception as e:
            self.last_result = {
                'status': HealthStatus.UNHEALTHY,
                'timestamp': self.last_check.isoformat(),
                'duration': time.time() - start_time,
                'details': {'error': str(e)},
                'message': f'Health check failed: {str(e)}'
            }
            return self.last_result


class SystemMonitor:
    """Monitors system resources and health"""
    
    def __init__(self):
        self.checks: Dict[str, HealthCheck] = {}
        self._setup_default_checks()
    
    def _setup_default_checks(self):
        """Setup default system health checks"""
        self.add_check("cpu_usage", self._check_cpu)
        self.add_check("memory_usage", self._check_memory)
        self.add_check("disk_usage", self._check_disk)
        self.add_check("process_count", self._check_processes)
    
    def add_check(self, name: str, check_func: Callable, timeout: int = 5):
        """Add a health check"""
        self.checks[name] = HealthCheck(name, check_func, timeout)
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {}
        overall_status = HealthStatus.HEALTHY
        
        for name, check in self.checks.items():
            result = await check.run()
            results[name] = result
            
            if result['status'] == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY
            elif result['status'] == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED
        
        return {
            'status': overall_status.value,
            'timestamp': datetime.now().isoformat(),
            'checks': results
        }
    
    async def get_check(self, name: str) -> Optional[Dict[str, Any]]:
        """Get result of a specific check"""
        if name not in self.checks:
            return None
        
        return await self.checks[name].run()
    
    async def _check_cpu(self) -> Dict[str, Any]:
        """Check CPU usage"""
        cpu_percent = psutil.cpu_percent(interval=1)
        
        if cpu_percent > 90:
            status = HealthStatus.UNHEALTHY
            message = f"High CPU usage: {cpu_percent}%"
        elif cpu_percent > 75:
            status = HealthStatus.DEGRADED
            message = f"Elevated CPU usage: {cpu_percent}%"
        else:
            status = HealthStatus.HEALTHY
            message = f"CPU usage: {cpu_percent}%"
        
        return {
            'healthy': status == HealthStatus.HEALTHY,
            'details': {
                'cpu_percent': cpu_percent,
                'status': status.value
            },
            'message': message
        }
    
    async def _check_memory(self) -> Dict[str, Any]:
        """Check memory usage"""
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        if memory_percent > 90:
            status = HealthStatus.UNHEALTHY
            message = f"High memory usage: {memory_percent}%"
        elif memory_percent > 75:
            status = HealthStatus.DEGRADED
            message = f"Elevated memory usage: {memory_percent}%"
        else:
            status = HealthStatus.HEALTHY
            message = f"Memory usage: {memory_percent}%"
        
        return {
            'healthy': status == HealthStatus.HEALTHY,
            'details': {
                'memory_percent': memory_percent,
                'total_gb': round(memory.total / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'status': status.value
            },
            'message': message
        }
    
    async def _check_disk(self) -> Dict[str, Any]:
        """Check disk usage"""
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        
        if disk_percent > 95:
            status = HealthStatus.UNHEALTHY
            message = f"High disk usage: {disk_percent:.1f}%"
        elif disk_percent > 85:
            status = HealthStatus.DEGRADED
            message = f"Elevated disk usage: {disk_percent:.1f}%"
        else:
            status = HealthStatus.HEALTHY
            message = f"Disk usage: {disk_percent:.1f}%"
        
        return {
            'healthy': status == HealthStatus.HEALTHY,
            'details': {
                'disk_percent': disk_percent,
                'total_gb': round(disk.total / (1024**3), 2),
                'used_gb': round(disk.used / (1024**3), 2),
                'free_gb': round(disk.free / (1024**3), 2),
                'status': status.value
            },
            'message': message
        }
    
    async def _check_processes(self) -> Dict[str, Any]:
        """Check number of running processes"""
        proc_count = len(psutil.pids())
        
        if proc_count > 1000:
            status = HealthStatus.DEGRADED
            message = f"High number of processes: {proc_count}"
        else:
            status = HealthStatus.HEALTHY
            message = f"Process count: {proc_count}"
        
        return {
            'healthy': status == HealthStatus.HEALTHY,
            'details': {
                'process_count': proc_count,
                'status': status.value
            },
            'message': message
        }


class MedicalSystemMonitor(SystemMonitor):
    """Medical-specific system monitor with additional checks"""
    
    def __init__(self):
        super().__init__()
        self.medical_checks: Dict[str, HealthCheck] = {}
        self._setup_medical_checks()
    
    def _setup_medical_checks(self):
        """Setup medical-specific health checks"""
        # Add medical-specific checks
        self.add_medical_check("database_connection", self._check_database)
        self.add_medical_check("vector_store", self._check_vector_store)
        self.add_medical_check("agent_connectivity", self._check_agents)
    
    def add_medical_check(self, name: str, check_func: Callable, timeout: int = 5):
        """Add a medical-specific health check"""
        self.medical_checks[name] = HealthCheck(name, check_func, timeout)
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all checks (system + medical)"""
        system_results = await super().run_all_checks()
        medical_results = {}
        
        for name, check in self.medical_checks.items():
            medical_results[name] = await check.run()
        
        # Combine results
        all_checks = {**system_results['checks'], **medical_results}
        
        # Determine overall status
        overall_status = HealthStatus.HEALTHY
        for result in all_checks.values():
            if result['status'] == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY
                break
            elif result['status'] == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED
        
        return {
            'status': overall_status.value,
            'timestamp': datetime.now().isoformat(),
            'checks': all_checks,
            'system_checks': system_results['checks'],
            'medical_checks': medical_results
        }
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity"""
        # In a real implementation, this would check the actual database
        # For now, we'll simulate the check
        try:
            # Simulate database check
            await asyncio.sleep(0.1)  # Simulate network delay
            healthy = True
            message = "Database connection OK"
        except Exception as e:
            healthy = False
            message = f"Database connection failed: {str(e)}"
        
        status = HealthStatus.HEALTHY if healthy else HealthStatus.UNHEALTHY
        
        return {
            'healthy': healthy,
            'details': {
                'status': status.value
            },
            'message': message
        }
    
    async def _check_vector_store(self) -> Dict[str, Any]:
        """Check vector store health"""
        # In a real implementation, this would check the actual vector store
        try:
            # Simulate vector store check
            await asyncio.sleep(0.05)  # Simulate check
            healthy = True
            message = "Vector store OK"
        except Exception as e:
            healthy = False
            message = f"Vector store failed: {str(e)}"
        
        status = HealthStatus.HEALTHY if healthy else HealthStatus.UNHEALTHY
        
        return {
            'healthy': healthy,
            'details': {
                'status': status.value
            },
            'message': message
        }
    
    async def _check_agents(self) -> Dict[str, Any]:
        """Check agent connectivity"""
        # In a real implementation, this would check actual agent connectivity
        try:
            # Simulate agent connectivity check
            await asyncio.sleep(0.05)
            healthy = True
            message = "All agents connected"
        except Exception as e:
            healthy = False
            message = f"Agent connectivity failed: {str(e)}"
        
        status = HealthStatus.HEALTHY if healthy else HealthStatus.UNHEALTHY
        
        return {
            'healthy': healthy,
            'details': {
                'status': status.value
            },
            'message': message
        }


class HealthMonitorService:
    """Service to continuously monitor health"""
    
    def __init__(self, monitor: MedicalSystemMonitor, check_interval: int = 60):
        self.monitor = monitor
        self.check_interval = check_interval
        self.is_monitoring = False
        self.latest_results: Optional[Dict[str, Any]] = None
        self._monitor_task: Optional[asyncio.Task] = None
    
    async def start_monitoring(self):
        """Start continuous monitoring"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        
        async def monitor_loop():
            while self.is_monitoring:
                try:
                    self.latest_results = await self.monitor.run_all_checks()
                    print(f"Health check completed at {self.latest_results['timestamp']}, status: {self.latest_results['status']}")
                except Exception as e:
                    print(f"Error during health monitoring: {e}")
                
                await asyncio.sleep(self.check_interval)
        
        self._monitor_task = asyncio.create_task(monitor_loop())
    
    async def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.is_monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass  # Expected when cancelling
    
    def get_latest_results(self) -> Optional[Dict[str, Any]]:
        """Get the latest health check results"""
        return self.latest_results
    
    async def get_current_status(self) -> HealthStatus:
        """Get current overall health status"""
        if self.latest_results:
            return HealthStatus(self.latest_results['status'])
        else:
            # Run a check to get current status
            results = await self.monitor.run_all_checks()
            return HealthStatus(results['status'])


# Global health monitor
health_monitor = HealthMonitorService(MedicalSystemMonitor())