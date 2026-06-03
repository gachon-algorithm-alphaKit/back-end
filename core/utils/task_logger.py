import logging
import time
import uuid
import functools
import contextvars

# Context variable to store correlation ID for async/background tasks tracking
correlation_id_var = contextvars.ContextVar('correlation_id', default=None)

logger = logging.getLogger('core.tasks')

def task_logger(name=None):
    """
    Decorator for logging general tasks.
    Records start/end times, duration, results, and retry count on failure.
    Uses contextvars to maintain sequence across async bounds.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            task_name = name or func.__name__
            
            # Ensure there's a correlation ID. If not, generate one.
            corr_id = correlation_id_var.get()
            if not corr_id:
                corr_id = str(uuid.uuid4())
                correlation_id_var.set(corr_id)

            extra_logs = {'correlation_id': corr_id}
            
            logger.info(f"Task '{task_name}' started", extra=extra_logs)
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                end_time = time.time()
                duration = round((end_time - start_time) * 1000, 2)
                extra_logs['duration'] = duration
                
                logger.info(f"Task '{task_name}' completed successfully", extra=extra_logs)
                return result
                
            except Exception as e:
                end_time = time.time()
                duration = round((end_time - start_time) * 1000, 2)
                extra_logs['duration'] = duration
                
                # Check if it's a retryable task (e.g., Celery task with request.retries)
                retry_count = kwargs.get('retry_count', 0)
                if hasattr(func, 'request') and hasattr(func.request, 'retries'):
                    retry_count = func.request.retries
                
                extra_logs['retry_count'] = retry_count
                
                logger.error(f"Task '{task_name}' failed: {str(e)}", exc_info=True, extra=extra_logs)
                raise

        return wrapper
    return decorator
