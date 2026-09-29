from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.dependencies import get_stats_service
from app.domain import StatsResponse
from app.services.stats import StatsService

router = APIRouter(prefix="/api/stats", tags=["statistics"])


@router.get("", response_model=StatsResponse)
def get_stats(
    response: Response, service: Annotated[StatsService, Depends(get_stats_service)]
) -> StatsResponse:
    stats, cache_state = service.get()
    response.headers["X-Cache"] = cache_state
    return stats
