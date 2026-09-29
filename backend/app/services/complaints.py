from uuid import UUID, uuid4

from redis import Redis

from app.domain import (
    VALID_TRANSITIONS,
    Category,
    ComplaintCreate,
    ComplaintPage,
    ComplaintRead,
    Priority,
    Status,
)
from app.repositories.complaints import ComplaintRepository
from app.services.triage import TriageService


class ComplaintNotFoundError(LookupError):
    pass


class InvalidTransitionError(ValueError):
    pass


class ComplaintService:
    def __init__(
        self, repository: ComplaintRepository, triage: TriageService, redis: Redis
    ) -> None:
        self.repository = repository
        self.triage = triage
        self.redis = redis

    def create(self, data: ComplaintCreate) -> ComplaintRead:
        complaint_id = uuid4()
        decision = self.triage.triage(complaint_id, data.text, data.location)
        complaint = self.repository.create(
            complaint_id, data, decision.result, decision.provider, decision.latency_ms
        )
        self.redis.delete("stats:v1")
        return self._read(complaint)

    def get(self, complaint_id: UUID) -> ComplaintRead:
        complaint = self.repository.get(complaint_id)
        if complaint is None:
            raise ComplaintNotFoundError(str(complaint_id))
        return self._read(complaint)

    def list(
        self,
        *,
        category: Category | None,
        priority: Priority | None,
        status: Status | None,
        page: int,
        page_size: int,
    ) -> ComplaintPage:
        rows, total = self.repository.list(
            category=category, priority=priority, status=status, page=page, page_size=page_size
        )
        return ComplaintPage(
            items=[self._read(row) for row in rows], total=total, page=page, page_size=page_size
        )

    def update_status(self, complaint_id: UUID, target: Status) -> ComplaintRead:
        complaint = self.repository.get(complaint_id)
        if complaint is None:
            raise ComplaintNotFoundError(str(complaint_id))
        allowed = VALID_TRANSITIONS[complaint.status]
        if target not in allowed:
            raise InvalidTransitionError(
                f"Invalid status transition: {complaint.status.value} -> {target.value}"
            )
        updated = self.repository.update_status(complaint, target)
        self.redis.delete("stats:v1")
        return self._read(updated)

    @staticmethod
    def _read(complaint: object) -> ComplaintRead:
        result = ComplaintRead.model_validate(complaint)
        return result.model_copy(
            update={"allowed_transitions": sorted(VALID_TRANSITIONS[result.status])}
        )
