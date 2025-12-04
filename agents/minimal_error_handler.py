"""
Minimal Error Handler - Fail Fast, Log Clearly.

This replaces the overly complex error handling with a minimal approach:
1. Log errors clearly
2. Fail fast (don't mask issues)
3. No excessive try-except blocks
4. Let errors propagate when appropriate

Philosophy: "Errors should be visible, not hidden"
"""

import logging
import time
from typing import Dict, List, Optional, Any, Callable
from functools import wraps

logger = logging.getLogger(__name__)


class ErrorContext:
    """Context for error tracking"""
    
    def __init__(self, operation: str):
        self.operation = operation
        self.start_time = time.time()
    
    def __enter__(self):
        logger.debug(f"Starting: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type is None:
            logger.debug(f"Completed: {self.operation} ({duration:.2f}s)")
        else:
            logger.error(
                f"Failed: {self.operation} ({duration:.2f}s) - "
                f"{exc_type.__name__}: {exc_val}"
            )
        
        # Don't suppress exception
        return False


def log_errors(operation: str = None):
    """
    Decorator to log errors without suppressing them.
    
    Args:
        operation: Operation description
    """
    def decorator(func: Callable) -> Callable:
        op_name = operation or func.__name__
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"Error in {op_name}: {type(e).__name__}: {str(e)}",
                    exc_info=True
                )
                raise  # Re-raise, don't suppress
        
        return wrapper
    
    return decorator


def safe_call(
    func: Callable,
    *args,
    default: Any = None,
    error_msg: str = None,
    **kwargs
) -> Any:
    """
    Call function with error logging but return default on failure.
    
    Use sparingly - only when you truly want to continue on error.
    
    Args:
        func: Function to call
        *args: Positional arguments
        default: Default value on error
        error_msg: Custom error message
        **kwargs: Keyword arguments
    
    Returns:
        Function result or default
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        msg = error_msg or f"Error calling {func.__name__}"
        logger.error(f"{msg}: {type(e).__name__}: {str(e)}")
        return default


def validate_required(value: Any, name: str, expected_type: type = None) -> Any:
    """
    Validate required value.
    
    Args:
        value: Value to validate
        name: Name for error message
        expected_type: Expected type (optional)
    
    Returns:
        Value if valid
    
    Raises:
        ValueError: If value is None or empty
        TypeError: If value is wrong type
    """
    if value is None:
        raise ValueError(f"{name} is required but was None")
    
    if expected_type and not isinstance(value, expected_type):
        raise TypeError(
            f"{name} must be {expected_type.__name__}, "
            f"got {type(value).__name__}"
        )
    
    # Check for empty strings/lists/dicts
    if hasattr(value, '__len__') and len(value) == 0:
        raise ValueError(f"{name} is required but was empty")
    
    return value


def validate_optional(
    value: Any,
    name: str,
    expected_type: type,
    default: Any = None
) -> Any:
    """
    Validate optional value with type checking.
    
    Args:
        value: Value to validate
        name: Name for error message
        expected_type: Expected type
        default: Default if None
    
    Returns:
        Value or default
    """
    if value is None:
        return default
    
    if not isinstance(value, expected_type):
        logger.warning(
            f"{name} should be {expected_type.__name__}, "
            f"got {type(value).__name__}, using default"
        )
        return default
    
    return value


class ValidationError(Exception):
    """Validation error with clear message"""
    pass


class AgentExecutionError(Exception):
    """Agent execution error"""
    pass


class TimeoutError(Exception):
    """Operation timeout"""
    pass


def fail_fast(condition: bool, message: str) -> None:
    """
    Fail fast if condition is False.
    
    Args:
        condition: Condition to check
        message: Error message
    
    Raises:
        ValidationError: If condition is False
    """
    if not condition:
        raise ValidationError(message)


def log_and_continue(error: Exception, context: str) -> None:
    """
    Log error and continue (use sparingly).
    
    Args:
        error: Exception to log
        context: Context description
    """
    logger.warning(
        f"Non-fatal error in {context}: {type(error).__name__}: {str(error)}"
    )


# Minimal retry logic (only for network errors)
def retry_on_network_error(
    func: Callable,
    max_retries: int = 2,
    delay: float = 1.0
) -> Any:
    """
    Retry function only on network errors.
    
    Args:
        func: Function to retry
        max_retries: Maximum retries
        delay: Delay between retries
    
    Returns:
        Function result
    
    Raises:
        Last exception if all retries fail
    """
    import requests
    
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except (requests.RequestException, ConnectionError, TimeoutError) as e:
            last_error = e
            if attempt < max_retries:
                logger.warning(
                    f"Network error (attempt {attempt + 1}/{max_retries + 1}): {e}"
                )
                time.sleep(delay * (2 ** attempt))  # Exponential backoff
            else:
                logger.error(f"All retries failed: {e}")
    
    raise last_error


# Context manager for timing operations
class Timer:
    """Simple timer context manager"""
    
    def __init__(self, operation: str):
        self.operation = operation
        self.start_time = None
        self.duration = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration = time.time() - self.start_time
        
        if exc_type is None:
            logger.info(f"{self.operation} completed in {self.duration:.2f}s")
        else:
            logger.error(
                f"{self.operation} failed after {self.duration:.2f}s: "
                f"{exc_type.__name__}"
            )
        
        return False  # Don't suppress exceptions
