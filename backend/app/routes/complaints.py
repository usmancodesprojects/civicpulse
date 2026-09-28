from ipaddress import ip_address
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from app.config import get_settings
from app.dependencies import get_complaint_service, get_rate_limiter
from app.domain import (
    Category,
    ComplaintCreate,
    ComplaintPage,
    ComplaintRead,
    Priority,
    Status,
    StatusUpdate,
)
from app.services.complaints import ComplaintNotFoundError, ComplaintService, InvalidTransitionError
from app.services.rate_limit import RateLimiter, RateLimitExceededError

router = APIRouter(prefix="/api/complaints", tags=["complaints"])


@router.post("", response_model=ComplaintRead, status_code=status.HTTP_201_CREATED)
def create_complaint(
    payload: ComplaintCreate,
    request: Request,
    response: Response,
    service: Annotated[ComplaintService, Depends(get_complaint_service)],
    limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
) -> ComplaintRead:
    client_ip = request.client.host if request.client else "unknown"
    if get_settings().trust_proxy_headers:
        forwarded_ip = request.headers.get("X-Real-IP", "")
        try:
            client_ip = str(ip_address(forwarded_ip))
        except ValueError:
            pass
    try:
        limiter.check(client_ip)
    except RateLimitExceededError as exc:
        response.headers["Retry-After"] = str(exc.retry_after)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Complaint submission rate limit exceeded",
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc
    return service.create(payload)


@router.get("/{complaint_id}", response_model=ComplaintRead)
def get_complaint(
    complaint_id: UUID, service: Annotated[ComplaintService, Depends(get_complaint_service)]
) -> ComplaintRead:
    try:
        return service.get(complaint_id)
    except ComplaintNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Complaint not found") from exc


@router.get("", response_model=ComplaintPage)
def list_complaints(
    service: Annotated[ComplaintService, Depends(get_complaint_service)],
    category: Category | None = None,
    priority: Priority | None = None,
    status_filter: Annotated[Status | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ComplaintPage:
    return service.list(
        category=category, priority=priority, status=status_filter, page=page, page_size=page_size
    )


@router.patch("/{complaint_id}/status", response_model=ComplaintRead)
def update_status(
    complaint_id: UUID,
    payload: StatusUpdate,
    service: Annotated[ComplaintService, Depends(get_complaint_service)],
) -> ComplaintRead:
    try:
        return service.update_status(complaint_id, payload.status)
    except ComplaintNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Complaint not found") from exc
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
