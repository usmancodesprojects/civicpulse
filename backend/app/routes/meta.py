from typing import Annotated

from fastapi import APIRouter, Depends

from app.config import get_settings
from app.dependencies import get_complaint_service
from app.domain import ProviderMeta
from app.services.complaints import ComplaintService

router = APIRouter(prefix="/api/meta", tags=["metadata"])


@router.get("/providers", response_model=ProviderMeta)
def provider_meta(
    service: Annotated[ComplaintService, Depends(get_complaint_service)],
) -> ProviderMeta:
    return ProviderMeta(
        active_provider=get_settings().triage_provider,
        outcomes=service.triage.outcomes(),
    )
