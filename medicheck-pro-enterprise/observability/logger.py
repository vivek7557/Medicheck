"""
Structured Logging for Medical Assistant
Implements HIPAA-compliant logging with structured format
"""
import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
import traceback
import os


class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MedicalLogRecord:
    """Represents a medical log record with HIPAA compliance"""
    
    def __init__(self, 
                 level: LogLevel, 
                 message: str, 
                 module: str, 
                 function: str,
                 patient_id: Optional[str] = None,
                 agent_id: Optional[str] = None,
                 session_id: Optional[str] = None,
                 extra_data: Dict[str, Any] = None):
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self.level = level.value
        self.message = message
        self.module = module
        self.function = function
        self.patient_id = patient_id  # May be None for non-patient logs
        self.agent_id = agent_id
        self.session_id = session_id
        self.extra_data = extra_data or {}
        self.log_id = f"log_{int(datetime.utcnow().timestamp())}_{id(self)}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert log record to dictionary"""
        # For HIPAA compliance, don't include patient_id in logs if present
        log_dict = {
            'timestamp': self.timestamp,
            'log_id': self.log_id,
            'level': self.level,
            'message': self.message,
            'module': self.module,
            'function': self.function,
            'agent_id': self.agent_id,
            'session_id': self.session_id,
            'extra_data': self.extra_data
        }
        
        # Only include patient reference indicator, not the actual ID
        if self.patient_id:
            log_dict['has_patient_data'] = True
        
        return log_dict
    
    def to_json(self) -> str:
        """Convert log record to JSON string"""
        return json.dumps(self.to_dict())


class MedicalLogger:
    """HIPAA-compliant medical logger"""
    
    def __init__(self, name: str, log_file: Optional[str] = None):
        self.name = name
        self.log_file = log_file or f"medical_assistant_{datetime.now().strftime('%Y%m%d')}.log"
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup the underlying logger"""
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent adding multiple handlers
        if not self.logger.handlers:
            # Create formatter
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            
            # File handler
            if self.log_file:
                file_handler = logging.FileHandler(self.log_file)
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
    
    def _log(self, 
             level: LogLevel, 
             message: str, 
             module: str, 
             function: str,
             patient_id: Optional[str] = None,
             agent_id: Optional[str] = None,
             session_id: Optional[str] = None,
             extra_data: Dict[str, Any] = None,
             exc_info: bool = False):
        """Internal logging method"""
        try:
            # Create log record
            log_record = MedicalLogRecord(
                level=level,
                message=message,
                module=module,
                function=function,
                patient_id=patient_id,
                agent_id=agent_id,
                session_id=session_id,
                extra_data=extra_data
            )
            
            # Log to underlying logger
            log_msg = log_record.to_json()
            if exc_info:
                self.logger.log(getattr(logging, level.value.upper()), log_msg, exc_info=True)
            else:
                self.logger.log(getattr(logging, level.value.upper()), log_msg)
        
        except Exception as e:
            # Fallback logging in case of error in our logging system
            fallback_msg = f"LOG_ERROR: {str(e)} - Original message: {message}"
            self.logger.error(fallback_msg)
    
    def debug(self, 
              message: str, 
              module: str = "", 
              function: str = "",
              patient_id: Optional[str] = None,
              agent_id: Optional[str] = None,
              session_id: Optional[str] = None,
              extra_data: Dict[str, Any] = None):
        """Log debug message"""
        self._log(LogLevel.DEBUG, message, module, function, patient_id, agent_id, session_id, extra_data)
    
    def info(self, 
             message: str, 
             module: str = "", 
             function: str = "",
             patient_id: Optional[str] = None,
             agent_id: Optional[str] = None,
             session_id: Optional[str] = None,
             extra_data: Dict[str, Any] = None):
        """Log info message"""
        self._log(LogLevel.INFO, message, module, function, patient_id, agent_id, session_id, extra_data)
    
    def warning(self, 
                message: str, 
                module: str = "", 
                function: str = "",
                patient_id: Optional[str] = None,
                agent_id: Optional[str] = None,
                session_id: Optional[str] = None,
                extra_data: Dict[str, Any] = None):
        """Log warning message"""
        self._log(LogLevel.WARNING, message, module, function, patient_id, agent_id, session_id, extra_data)
    
    def error(self, 
              message: str, 
              module: str = "", 
              function: str = "",
              patient_id: Optional[str] = None,
              agent_id: Optional[str] = None,
              session_id: Optional[str] = None,
              extra_data: Dict[str, Any] = None,
              exc_info: bool = False):
        """Log error message"""
        self._log(LogLevel.ERROR, message, module, function, patient_id, agent_id, session_id, extra_data, exc_info)
    
    def critical(self, 
                 message: str, 
                 module: str = "", 
                 function: str = "",
                 patient_id: Optional[str] = None,
                 agent_id: Optional[str] = None,
                 session_id: Optional[str] = None,
                 extra_data: Dict[str, Any] = None,
                 exc_info: bool = False):
        """Log critical message"""
        self._log(LogLevel.CRITICAL, message, module, function, patient_id, agent_id, session_id, extra_data, exc_info)


class AuditLogger(MedicalLogger):
    """Specialized logger for audit trails"""
    
    def __init__(self, name: str = "audit", log_file: Optional[str] = None):
        super().__init__(name, log_file or f"audit_trail_{datetime.now().strftime('%Y%m%d')}.log")
    
    def log_access(self, 
                   user_id: str, 
                   action: str, 
                   resource: str, 
                   patient_id: Optional[str] = None,
                   success: bool = True,
                   ip_address: Optional[str] = None):
        """Log access to medical resources"""
        extra_data = {
            'user_id': user_id,
            'action': action,
            'resource': resource,
            'success': success
        }
        
        if ip_address:
            extra_data['ip_address'] = ip_address
        
        self.info(
            f"Access {'granted' if success else 'denied'}: {action} on {resource}",
            module="access_control",
            function="check_access",
            patient_id=patient_id,
            extra_data=extra_data
        )
    
    def log_medical_action(self, 
                           action: str, 
                           agent_id: str, 
                           patient_id: str, 
                           details: Dict[str, Any],
                           outcome: str = "success"):
        """Log medical actions for audit trail"""
        extra_data = {
            'agent_id': agent_id,
            'action': action,
            'details': details,
            'outcome': outcome
        }
        
        self.info(
            f"Medical action performed: {action}",
            module="medical_assistant",
            function=action,
            patient_id=patient_id,
            agent_id=agent_id,
            extra_data=extra_data
        )
    
    def log_consent_action(self, 
                           patient_id: str, 
                           action: str, 
                           consent_type: str,
                           granted: bool):
        """Log consent-related actions"""
        extra_data = {
            'action': action,
            'consent_type': consent_type,
            'granted': granted
        }
        
        self.info(
            f"Consent {action}: {consent_type} ({'granted' if granted else 'denied'})",
            module="consent_management",
            function=action,
            patient_id=patient_id,
            extra_data=extra_data
        )


# Global loggers
medical_logger = MedicalLogger("medical_assistant")
audit_logger = AuditLogger()