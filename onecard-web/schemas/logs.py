from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class LogLevel(str, Enum):
    ERROR = "ERROR"
    INFO = "INFO"
    WARNING = "WARNING"
    DEBUG = "DEBUG"


class LogEntry(BaseModel):
    timestamp: datetime
    level: LogLevel
    message: str
    pathname: str
    lineno: int
    taskName: Optional[str] = None
    service_name: Optional[str] = None
    client_id: Optional[str] = None
    emp_no: Optional[str] = None
    status: Optional[str] = None
    error_message: Optional[str] = None
    endpoint: Optional[str] = None
    response_time_ms: Optional[float] = None


class LogStatistics(BaseModel):
    total_requests: int
    success_count: int
    error_count: int
    warning_count: int
    success_rate: float
    average_response_time: Optional[float] = None
    top_endpoints: List[Dict[str, Any]]
    error_distribution: Dict[str, int]
    hourly_requests: List[Dict[str, Any]]
    daily_requests: List[Dict[str, Any]]
    status_distribution: Dict[str, int]
    service_usage: Dict[str, int]


class LogAnalysisResponse(BaseModel):
    statistics: LogStatistics
    recent_errors: List[LogEntry]
    performance_metrics: Dict[str, Any]
