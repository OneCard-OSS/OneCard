import logging
import json
import sys
import os
from datetime import datetime

class JsonFormatter(logging.Formatter):
    """
    Format logs in JSON format by extending Formatter in Python logging module 
    """ 
    def format(self, record):
        log_record = {
            "timestamp" : datetime.fromtimestamp(record.created).isoformat(),
            "level" : record.levelname,
            "message" : record.getMessage(),
            "pathname" : record.pathname,
            "lineno" : record.lineno
        }
        # Merge all additional information passed as extra in record.__dict__
        for key, value in record.__dict__.items():
            if key not in log_record and key not in ['args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename', 'funcName', 'levelname', 'levelno', 'lineno', 'module', 'msecs', 'message', 'msg', 'name', 'pathname', 'process', 'processName', 'relativeCreated', 'stack_info', 'thread', 'threadName']:
                log_record[key] = value
        
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_record)

class EndPointAdapter(logging.LoggerAdapter):
    """
    Adapter that automatically adds endpoint information to the log
    """
    def process(self, msg, kwargs):
        extra = kwargs.pop('extra', {})
        extra.update(self.extra)
        kwargs['extra'] = extra
        return msg, kwargs
    
def setup_logging():
    """
    Set up logs to be written to a file in JSON format 
    """
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
    log_file = "api_access_log"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_path = os.path.join(log_dir, log_file)
        
    logging.getLogger().handlers.clear()
        
    file_handler = logging.FileHandler(log_path, mode='a')
    file_handler.setLevel(logging.INFO)
        
    formatter = JsonFormatter()
    file_handler.setFormatter(formatter)
        
    logger = logging.getLogger()
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)
        
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.propagate = False
    uvicorn_logger.addHandler(logging.StreamHandler(sys.stdout))