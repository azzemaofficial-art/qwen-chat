"""
Advanced Logging System for Trading Advisor Pro v6.0
Features:
- Structured JSON logging for production
- Console logging with colors for development
- Log rotation and compression
- Audit logging for security-sensitive operations
- Performance metrics logging
- Context-aware logging with correlation IDs
"""

import logging
import sys
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import traceback
import uuid
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    def __init__(self, include_caller_info: bool = True):
        super().__init__()
        self.include_caller_info = include_caller_info
    
    def format(self, record: logging.LogRecord) -> str:
        # Add color based on log level
        color = self.COLORS.get(record.levelname, self.RESET)
        levelname = f"{color}{self.BOLD}{record.levelname}{self.RESET}"
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Build message
        message = f"{timestamp} | {levelname}"
        
        if self.include_caller_info:
            message += f" | {record.name}:{record.lineno}"
        
        message += f" | {record.getMessage()}"
        
        # Add exception info if present
        if record.exc_info:
            message += "\n" + traceback.format_exception(*record.exc_info)
        
        return message


class JSONFormatter(logging.Formatter):
    """Structured JSON formatter for production logging"""
    
    def __init__(self, include_caller_info: bool = True):
        super().__init__()
        self.include_caller_info = include_caller_info
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'correlation_id': getattr(record, 'correlation_id', None),
        }
        
        if self.include_caller_info:
            log_data['caller'] = {
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno,
            }
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName', 
                          'levelname', 'levelno', 'lineno', 'module', 'msecs', 
                          'pathname', 'process', 'processName', 'relativeCreated',
                          'stack_info', 'exc_info', 'exc_text', 'thread', 'threadName',
                          'correlation_id']:
                try:
                    json.dumps(value)  # Test if serializable
                    log_data[key] = value
                except (TypeError, ValueError):
                    log_data[key] = str(value)
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': traceback.format_exception(*record.exc_info),
            }
        
        return json.dumps(log_data)


class AuditLogger:
    """Specialized logger for audit trails and security events"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.audit_file = None
    
    def log_action(self, action: str, user: str, resource: str, 
                   details: Optional[Dict[str, Any]] = None,
                   success: bool = True):
        """Log an auditable action"""
        log_data = {
            'event_type': 'AUDIT',
            'action': action,
            'user': user,
            'resource': resource,
            'success': success,
            'timestamp': datetime.utcnow().isoformat(),
            'ip_address': details.get('ip_address') if details else None,
            'session_id': details.get('session_id') if details else None,
        }
        
        if details:
            # Filter out sensitive data
            safe_details = {k: v for k, v in details.items() 
                           if k not in ['password', 'api_key', 'token', 'secret']}
            log_data['details'] = safe_details
        
        level = logging.INFO if success else logging.WARNING
        self.logger.log(level, json.dumps(log_data))
    
    def log_login(self, user: str, success: bool, ip_address: str = None):
        """Log login attempt"""
        self.log_action(
            action='LOGIN',
            user=user,
            resource='authentication_system',
            details={'ip_address': ip_address},
            success=success
        )
    
    def log_trade_execution(self, user: str, symbol: str, side: str, 
                           quantity: float, price: float, order_id: str):
        """Log trade execution for compliance"""
        self.log_action(
            action='TRADE_EXECUTION',
            user=user,
            resource=symbol,
            details={
                'side': side,
                'quantity': quantity,
                'price': price,
                'order_id': order_id,
            },
            success=True
        )
    
    def log_config_change(self, user: str, setting: str, old_value: Any, 
                         new_value: Any):
        """Log configuration changes"""
        self.log_action(
            action='CONFIG_CHANGE',
            user=user,
            resource=setting,
            details={
                'old_value': str(old_value),
                'new_value': str(new_value),
            },
            success=True
        )


class PerformanceLogger:
    """Logger for performance metrics and timing"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.timers: Dict[str, datetime] = {}
    
    def start_timer(self, operation: str, correlation_id: str = None):
        """Start timing an operation"""
        self.timers[operation] = datetime.utcnow()
        self.logger.info(
            f"Operation started: {operation}",
            extra={'correlation_id': correlation_id, 'event_type': 'PERF_START'}
        )
    
    def end_timer(self, operation: str, correlation_id: str = None, 
                  metadata: Dict[str, Any] = None):
        """End timing and log performance metrics"""
        if operation not in self.timers:
            self.logger.warning(f"Timer not found for operation: {operation}")
            return
        
        start_time = self.timers.pop(operation)
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        log_data = {
            'operation': operation,
            'duration_seconds': duration,
            'duration_ms': duration * 1000,
        }
        
        if metadata:
            log_data.update(metadata)
        
        level = logging.WARNING if duration > 1.0 else logging.INFO
        self.logger.log(
            level,
            f"Operation completed: {operation} ({duration*1000:.2f}ms)",
            extra={
                'correlation_id': correlation_id,
                'event_type': 'PERF_END',
                **log_data
            }
        )
        
        return duration


class ContextFilter(logging.Filter):
    """Add contextual information to log records"""
    
    def __init__(self, context: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.context = context or {}
    
    def filter(self, record: logging.LogRecord) -> bool:
        # Add correlation ID if not present
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = self.context.get('correlation_id', str(uuid.uuid4()))
        
        # Add other context fields
        for key, value in self.context.items():
            if not hasattr(record, key):
                setattr(record, key, value)
        
        return True


def setup_logging(config=None) -> logging.Logger:
    """
    Setup comprehensive logging system
    
    Args:
        config: Configuration object with logging settings
    
    Returns:
        Configured logger instance
    """
    # Get configuration values
    if config:
        log_level = getattr(config.logging, 'log_level', 'INFO')
        console_output = getattr(config.logging, 'console_output', True)
        file_output = getattr(config.logging, 'file_output', True)
        log_directory = getattr(config.logging, 'log_directory', './logs')
        rotation_max_mb = getattr(config.logging, 'rotation_max_mb', 50)
        backup_count = getattr(config.logging, 'backup_count', 10)
        include_caller_info = getattr(config.logging, 'include_caller_info', True)
    else:
        log_level = 'INFO'
        console_output = True
        file_output = True
        log_directory = './logs'
        rotation_max_mb = 50
        backup_count = 10
        include_caller_info = True
    
    # Create logger
    logger = logging.getLogger('trading_advisor')
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create logs directory
    if file_output:
        log_path = Path(log_directory)
        log_path.mkdir(parents=True, exist_ok=True)
    
    # Console handler with colors
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_formatter = ColoredFormatter(include_caller_info=include_caller_info)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File handler with rotation
    if file_output:
        log_file = Path(log_directory) / 'trading_advisor.log'
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=rotation_max_mb * 1024 * 1024,
            backupCount=backup_count
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = JSONFormatter(include_caller_info=include_caller_info)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Error-specific log file
        error_file = Path(log_directory) / 'errors.log'
        error_handler = RotatingFileHandler(
            error_file,
            maxBytes=rotation_max_mb * 1024 * 1024,
            backupCount=backup_count
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        logger.addHandler(error_handler)
        
        # Audit log file
        audit_file = Path(log_directory) / 'audit.log'
        audit_handler = TimedRotatingFileHandler(
            audit_file,
            when='midnight',
            interval=1,
            backupCount=90  # Keep 90 days of audit logs
        )
        audit_handler.setLevel(logging.INFO)
        audit_formatter = JSONFormatter(include_caller_info=True)
        audit_handler.setFormatter(audit_formatter)
        
        audit_logger = logging.getLogger('trading_advisor.audit')
        audit_logger.setLevel(logging.INFO)
        audit_logger.addHandler(audit_handler)
        audit_logger.propagate = False
    
    # Add context filter
    context_filter = ContextFilter()
    for handler in logger.handlers:
        handler.addFilter(context_filter)
    
    # Log startup message
    logger.info("Trading Advisor Pro v6.0 logging system initialized")
    logger.info(f"Environment: {getattr(config.general, 'environment', 'unknown') if config else 'unknown'}")
    
    return logger


# Global logger instance
logger = None
audit_logger = None
perf_logger = None


def get_logger() -> logging.Logger:
    """Get the global logger instance"""
    global logger
    if logger is None:
        logger = setup_logging()
    return logger


def get_audit_logger() -> AuditLogger:
    """Get the audit logger instance"""
    global audit_logger
    if audit_logger is None:
        audit_logger = AuditLogger(get_logger())
    return audit_logger


def get_perf_logger() -> PerformanceLogger:
    """Get the performance logger instance"""
    global perf_logger
    if perf_logger is None:
        perf_logger = PerformanceLogger(get_logger())
    return perf_logger


# Convenience functions
def log_debug(msg: str, **kwargs):
    get_logger().debug(msg, extra=kwargs)


def log_info(msg: str, **kwargs):
    get_logger().info(msg, extra=kwargs)


def log_warning(msg: str, **kwargs):
    get_logger().warning(msg, extra=kwargs)


def log_error(msg: str, exc_info: bool = False, **kwargs):
    get_logger().error(msg, exc_info=exc_info, extra=kwargs)


def log_critical(msg: str, exc_info: bool = False, **kwargs):
    get_logger().critical(msg, exc_info=exc_info, extra=kwargs)


if __name__ == "__main__":
    # Test logging system
    test_logger = setup_logging()
    test_audit = AuditLogger(test_logger)
    test_perf = PerformanceLogger(test_logger)
    
    test_logger.info("Testing logging system")
    test_logger.debug("Debug message with caller info")
    test_logger.warning("Warning message")
    test_logger.error("Error message", exc_info=False)
    
    test_audit.log_login("test_user", True, "127.0.0.1")
    test_audit.log_trade_execution(
        "test_user", "AAPL", "BUY", 100, 150.50, "ORD-123456"
    )
    
    test_perf.start_timer("test_operation")
    import time
    time.sleep(0.1)
    test_perf.end_timer("test_operation", metadata={'status': 'success'})
    
    print("\nLogging test completed. Check ./logs directory for output files.")
