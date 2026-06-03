import json
import logging
import re
from datetime import datetime

# Define fields to mask
SENSITIVE_FIELDS = ['password', 'ssn', 'card_number', 'personal_info', 'token', 'refresh', 'access']
MASK_STRING = '***MASKED***'

def mask_sensitive_data(data):
    """
    Recursively mask sensitive data in dictionaries or lists.
    If the data is a JSON string, try to parse, mask, and return as dict.
    """
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except (ValueError, TypeError):
            return data

    if isinstance(data, dict):
        masked_data = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in SENSITIVE_FIELDS):
                masked_data[key] = MASK_STRING
            else:
                masked_data[key] = mask_sensitive_data(value)
        return masked_data
    elif isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]
    
    return data

class JsonFormatter(logging.Formatter):
    """
    Custom formatter to output JSON logs.
    """
    def format(self, record):
        log_record = {
            'timestamp': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'logger_name': record.name,
            'message': record.getMessage(),
        }

        # Add custom fields if they exist in the record
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
        if hasattr(record, 'api_id'):
            log_record['api_id'] = record.api_id
        if hasattr(record, 'duration'):
            log_record['duration_ms'] = record.duration
        if hasattr(record, 'correlation_id'):
            log_record['correlation_id'] = record.correlation_id

        # Merge in any extra dict passed via `extra={...}`
        if hasattr(record, 'extra_data') and isinstance(record.extra_data, dict):
            masked_extra = mask_sensitive_data(record.extra_data)
            log_record.update(masked_extra)

        # Include exception traceback if present
        if record.exc_info:
            log_record['exc_info'] = self.formatException(record.exc_info)

        return json.dumps(log_record, ensure_ascii=False)

class TerminalFormatter(logging.Formatter):
    """
    Custom formatter for terminal output (API requests/responses).
    """
    COLORS = {
        'DEBUG': '\033[94m',      # Blue
        'INFO': '\033[92m',       # Green
        'WARNING': '\033[93m',    # Yellow
        'ERROR': '\033[91m',      # Red
        'CRITICAL': '\033[1;91m', # Bold Red
        'RESET': '\033[0m'        # Reset
    }

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Check if it's an API log
        is_api = hasattr(record, 'is_api') and record.is_api
        
        if is_api:
            log_type = getattr(record, 'log_type', 'UNKNOWN')
            
            if log_type == 'REQUEST':
                method = getattr(record, 'method', 'UNKNOWN')
                url = getattr(record, 'url', 'UNKNOWN')
                body = mask_sensitive_data(getattr(record, 'body', {}))
                
                output = (f"{color}[API REQUEST]{reset} {method} {url}\n"
                          f"    Body/Params: {json.dumps(body, ensure_ascii=False)}")
                return output
                
            elif log_type == 'RESPONSE':
                status_code = getattr(record, 'status_code', 0)
                message = record.getMessage()
                response_data = mask_sensitive_data(getattr(record, 'response_data', {}))
                
                # Change color to red if status is 4xx or 5xx
                if status_code >= 400:
                    color = self.COLORS['ERROR']
                
                if status_code >= 400:
                    cause = getattr(record, 'cause', 'Unknown')
                    request_data = mask_sensitive_data(getattr(record, 'request_data', {}))
                    output = (f"{color}[API ERROR]{reset} {status_code} - {message}\n"
                              f"    Cause: {cause}\n"
                              f"    Request Data: {json.dumps(request_data, ensure_ascii=False)}")
                else:
                    output = (f"{color}[API RESPONSE]{reset} {status_code} - {message}\n"
                              f"    Response: {json.dumps(response_data, ensure_ascii=False)[:500]}" # Truncate long responses
                              f"{'...' if len(json.dumps(response_data)) > 500 else ''}")
                return output

        # Default formatting for non-API logs
        timestamp = self.formatTime(record, self.datefmt)
        msg = record.getMessage()
        
        output = f"{color}[{record.levelname}]{reset} {timestamp} | {record.name} | {msg}"
        
        if hasattr(record, 'correlation_id'):
            output += f" [corr_id: {record.correlation_id}]"
            
        if record.exc_info:
            output += f"\n{self.formatException(record.exc_info)}"
            
        return output
