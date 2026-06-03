import logging
import time
import uuid
import json
from django.urls import resolve
from django.utils.deprecation import MiddlewareMixin
from core.utils.task_logger import correlation_id_var
# Separate loggers for file and console
api_logger = logging.getLogger('core.api')
class APILoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.start_time = time.time()
        
        # Generate Request ID
        request_id = str(uuid.uuid4())
        request.request_id = request_id
        
        # Set correlation ID for async tasks spawned from this request
        correlation_id_var.set(request_id)
        try:
            resolver_match = resolve(request.path)
            view_name = resolver_match.view_name
            func_name = getattr(resolver_match.func, '__name__', 'unknown_func')
            module_name = getattr(resolver_match.func, '__module__', 'unknown_module')
            # filename-method name
            filename = module_name.split('.')[-1]
            api_id = f"{filename}-{func_name}"
        except Exception:
            api_id = "unknown"
            
        request.api_id = api_id
        # Extract body (careful with multipart/form-data)
        body = {}
        if request.content_type == 'application/json':
            try:
                body = json.loads(request.body)
            except Exception:
                body = {'raw_body': request.body.decode('utf-8', errors='replace')}
        elif request.method in ['POST', 'PUT', 'PATCH']:
            body = request.POST.dict()
        else:
            body = request.GET.dict()
            
        # Add a custom attribute to track request body safely for response logging
        request._logged_body = body
        user_id = getattr(request.user, 'id', None) if hasattr(request, 'user') else None
        extra_logs = {
            'is_api': True,
            'log_type': 'REQUEST',
            'request_id': request_id,
            'correlation_id': request_id,
            'api_id': api_id,
            'user_id': user_id,
            'method': request.method,
            'url': request.get_full_path(),
            'body': body
        }
        api_logger.info(f"API Request Started: {request.method} {request.path}", extra=extra_logs)
        
        return None
    def process_response(self, request, response):
        if not hasattr(request, 'start_time'):
            return response
        duration = round((time.time() - request.start_time) * 1000, 2)
        request_id = getattr(request, 'request_id', 'unknown')
        api_id = getattr(request, 'api_id', 'unknown')
        user_id = getattr(request.user, 'id', None) if hasattr(request, 'user') else None
        
        status_code = response.status_code
        
        # Try to parse response content if it's JSON
        response_data = {}
        if response.get('Content-Type') == 'application/json':
            try:
                # response.content is bytes
                response_data = json.loads(response.content.decode('utf-8'))
            except Exception:
                pass
                
        extra_logs = {
            'is_api': True,
            'log_type': 'RESPONSE',
            'request_id': request_id,
            'correlation_id': request_id,
            'api_id': api_id,
            'user_id': user_id,
            'method': request.method,
            'url': request.get_full_path(),
            'status_code': status_code,
            'duration': duration,
            'response_data': response_data
        }
        if status_code >= 400:
            extra_logs['cause'] = response.reason_phrase
            extra_logs['request_data'] = getattr(request, '_logged_body', {})
            
            if status_code >= 500:
                api_logger.error(f"API Error Response: {status_code}", extra=extra_logs)
            else:
                api_logger.warning(f"API Client Error Response: {status_code}", extra=extra_logs)
        else:
            api_logger.info(f"API Response Completed: {status_code}", extra=extra_logs)
        return response
    def process_exception(self, request, exception):
        if not hasattr(request, 'start_time'):
            return None
            
        duration = round((time.time() - request.start_time) * 1000, 2)
        request_id = getattr(request, 'request_id', 'unknown')
        api_id = getattr(request, 'api_id', 'unknown')
        user_id = getattr(request.user, 'id', None) if hasattr(request, 'user') else None
        
        extra_logs = {
            'is_api': True,
            'log_type': 'RESPONSE',
            'request_id': request_id,
            'correlation_id': request_id,
            'api_id': api_id,
            'user_id': user_id,
            'method': request.method,
            'url': request.get_full_path(),
            'status_code': 500,
            'duration': duration,
            'cause': str(exception),
            'request_data': getattr(request, '_logged_body', {}),
            'response_data': {}
        }
        
        api_logger.error(f"API Exception: {str(exception)}", exc_info=True, extra=extra_logs)
        return None

