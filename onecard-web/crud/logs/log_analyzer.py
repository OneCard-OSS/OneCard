import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from collections import Counter, defaultdict
from schemas.logs import LogEntry, LogStatistics, LogAnalysisResponse
import re


class LogAnalyzer:
    def __init__(self, log_file_name: str = "api_access_log.jsonl"):

        current_path = os.path.dirname(os.path.abspath(__file__))
        project_root = current_path

        while not (os.path.isdir(os.path.join(project_root, 'onecard-api')) or os.path.isdir(os.path.join(project_root, 'onecard-web'))):
            parent_path = os.path.dirname(project_root)
            if parent_path == project_root: 
                raise FileNotFoundError("Project root could not be determined. Ensure 'onecard-api' or 'onecard-web' directory exists.")
            project_root = parent_path

        self.log_file_path = os.path.join(project_root, 'logs', log_file_name)
        print(f"Log file path dynamically set to: {self.log_file_path}") 
    
    def parse_log_file(self) -> List[LogEntry]:
        """JSONL 로그 파일을 파싱하여 LogEntry 객체 리스트로 반환"""
        log_entries = []
        
        try:
            if not os.path.exists(self.log_file_path):
                print(f"Warning: Log file not found at {self.log_file_path}")
                return log_entries
                
            with open(self.log_file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    try:
                        log_data = json.loads(line.strip())
                       
                        log_data['timestamp'] = datetime.fromisoformat(log_data['timestamp'])
                        log_entry = LogEntry(**log_data)
                        log_entries.append(log_entry)
                    except (json.JSONDecodeError, ValueError, TypeError) as e:
                       
                        continue
        except Exception as e:
            print(f"로그 파일 읽기 실패: {e}")
            
        return log_entries
    
    def analyze_logs(self, days: int = 7) -> LogAnalysisResponse:
        """로그를 분석하여 통계 정보 반환"""
        log_entries = self.parse_log_file()
        
        # 최근 N일 데이터만 필터링
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_logs = [log for log in log_entries if log.timestamp >= cutoff_date]
        
        # 기본 통계
        total_requests = len(recent_logs)
        success_count = len([log for log in recent_logs if log.level == "INFO" and log.status == "success"])
        error_count = len([log for log in recent_logs if log.level == "ERROR"])
        warning_count = len([log for log in recent_logs if log.level == "WARNING"])
        
        success_rate = (success_count / total_requests * 100) if total_requests > 0 else 0
        
        # 응답 시간 분석
        response_times = [log.response_time_ms for log in recent_logs if log.response_time_ms is not None]
        average_response_time = sum(response_times) / len(response_times) if response_times else None
        
        # 엔드포인트 분석
        endpoint_counter = Counter([log.endpoint for log in recent_logs if log.endpoint])
        top_endpoints = [{"endpoint": endpoint, "count": count} 
                        for endpoint, count in endpoint_counter.most_common(10)]
        
        # 에러 분포
        error_messages = [log.error_message for log in recent_logs if log.error_message]
        error_distribution = dict(Counter(error_messages))
        
        # 시간별 요청 분석
        hourly_requests = self._get_hourly_requests(recent_logs)
        daily_requests = self._get_daily_requests(recent_logs)
        
        # 상태 분포
        status_counter = Counter([log.status for log in recent_logs if log.status])
        status_distribution = dict(status_counter)
        
        # 서비스 사용량
        service_counter = Counter([log.service_name for log in recent_logs if log.service_name])
        service_usage = dict(service_counter)
        
        # 최근 에러들
        recent_errors = [log for log in recent_logs if log.level == "ERROR"][:10]
        
        # 성능 메트릭
        performance_metrics = {
            "max_response_time": max(response_times) if response_times else 0,
            "min_response_time": min(response_times) if response_times else 0,
            "p95_response_time": self._calculate_percentile(response_times, 95) if response_times else 0,
            "p99_response_time": self._calculate_percentile(response_times, 99) if response_times else 0,
        }
        
        statistics = LogStatistics(
            total_requests=total_requests,
            success_count=success_count,
            error_count=error_count,
            warning_count=warning_count,
            success_rate=round(success_rate, 2),
            average_response_time=round(average_response_time, 2) if average_response_time else None,
            top_endpoints=top_endpoints,
            error_distribution=error_distribution,
            hourly_requests=hourly_requests,
            daily_requests=daily_requests,
            status_distribution=status_distribution,
            service_usage=service_usage
        )
        
        return LogAnalysisResponse(
            statistics=statistics,
            recent_errors=recent_errors,
            performance_metrics=performance_metrics
        )
    
    def _get_hourly_requests(self, logs: List[LogEntry]) -> List[Dict[str, Any]]:
        """시간별 요청 수 계산"""
        hourly_count = defaultdict(int)
        
        for log in logs:
            hour_key = log.timestamp.strftime("%Y-%m-%d %H:00")
            hourly_count[hour_key] += 1
        
        return [{"hour": hour, "count": count} 
                for hour, count in sorted(hourly_count.items())]
    
    def _get_daily_requests(self, logs: List[LogEntry]) -> List[Dict[str, Any]]:
        """일별 요청 수 계산"""
        daily_count = defaultdict(int)
        
        for log in logs:
            day_key = log.timestamp.strftime("%Y-%m-%d")
            daily_count[day_key] += 1
        
        return [{"date": date, "count": count} 
                for date, count in sorted(daily_count.items())]
    
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """백분위수 계산"""
        if not values:
            return 0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        if index >= len(sorted_values):
            index = len(sorted_values) - 1
        return sorted_values[index]
    
    def get_error_trends(self, days: int = 7) -> Dict[str, Any]:
        """에러 트렌드 분석"""
        log_entries = self.parse_log_file()
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_logs = [log for log in log_entries if log.timestamp >= cutoff_date]
        
        error_logs = [log for log in recent_logs if log.level == "ERROR"]
        
        # 시간별 에러 발생량
        error_by_hour = defaultdict(int)
        for log in error_logs:
            hour_key = log.timestamp.strftime("%Y-%m-%d %H:00")
            error_by_hour[hour_key] += 1
        
        # 에러 타입별 분류
        error_types = defaultdict(int)
        for log in error_logs:
            if "connection failed" in log.message.lower():
                error_types["Connection Error"] += 1
            elif "status code" in log.message.lower():
                error_types["HTTP Error"] += 1
            elif "validation error" in log.message.lower():
                error_types["Validation Error"] += 1
            elif "unexpected error" in log.message.lower():
                error_types["Unexpected Error"] += 1
            else:
                error_types["Other"] += 1
        
        return {
            "error_by_hour": [{"hour": hour, "count": count} 
                             for hour, count in sorted(error_by_hour.items())],
            "error_types": dict(error_types),
            "total_errors": len(error_logs)
        }
