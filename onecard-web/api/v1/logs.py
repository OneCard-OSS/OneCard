from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any
from crud.logs.log_analyzer import LogAnalyzer
from schemas.logs import LogAnalysisResponse

router = APIRouter(prefix="/api/v1/logs", tags=["logs"])

# 로그 분석기 인스턴스
log_analyzer = LogAnalyzer()


@router.get("/analysis", response_model=LogAnalysisResponse)
async def get_log_analysis(days: int = Query(default=7, ge=1, le=30, description="분석할 일수")):
    """
    로그 분석 결과를 반환합니다.
    
    - **days**: 분석할 기간 (일 단위, 1-30일)
    """
    try:
        analysis_result = log_analyzer.analyze_logs(days=days)
        return analysis_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"로그 분석 중 오류 발생: {str(e)}")


@router.get("/error-trends")
async def get_error_trends(days: int = Query(default=7, ge=1, le=30, description="분석할 일수")) -> Dict[str, Any]:
    """
    에러 트렌드 분석 결과를 반환합니다.
    
    - **days**: 분석할 기간 (일 단위, 1-30일)
    """
    try:
        error_trends = log_analyzer.get_error_trends(days=days)
        return error_trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"에러 트렌드 분석 중 오류 발생: {str(e)}")


@router.get("/dashboard-data")
async def get_dashboard_data(days: int = Query(default=7, ge=1, le=30, description="분석할 일수")) -> Dict[str, Any]:
    """
    대시보드용 종합 데이터를 반환합니다.
    
    - **days**: 분석할 기간 (일 단위, 1-30일)
    """
    try:
        analysis_result = log_analyzer.analyze_logs(days=days)
        error_trends = log_analyzer.get_error_trends(days=days)
        
        return {
            "analysis": analysis_result,
            "error_trends": error_trends,
            "summary": {
                "total_requests": analysis_result.statistics.total_requests,
                "success_rate": analysis_result.statistics.success_rate,
                "error_count": analysis_result.statistics.error_count,
                "average_response_time": analysis_result.statistics.average_response_time
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"대시보드 데이터 조회 중 오류 발생: {str(e)}")
