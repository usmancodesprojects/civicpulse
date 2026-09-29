from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain import Category, ComplaintCreate, Priority, Status, TriageResult
from app.models import Complaint


class ComplaintRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        complaint_id: UUID,
        data: ComplaintCreate,
        triage: TriageResult,
        triaged_by: str,
        latency_ms: int,
    ) -> Complaint:
        complaint = Complaint(
            id=complaint_id,
            text=data.text,
            location=data.location,
            reporter_contact=data.reporter_contact,
            category=triage.category,
            priority=triage.priority,
            ai_summary=triage.summary,
            triaged_by=triaged_by,
            triage_latency_ms=latency_ms,
        )
        self.session.add(complaint)
        self.session.commit()
        self.session.refresh(complaint)
        return complaint

    def get(self, complaint_id: UUID) -> Complaint | None:
        return self.session.get(Complaint, complaint_id)

    def list(
        self,
        *,
        category: Category | None,
        priority: Priority | None,
        status: Status | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Complaint], int]:
        filters = []
        if category:
            filters.append(Complaint.category == category)
        if priority:
            filters.append(Complaint.priority == priority)
        if status:
            filters.append(Complaint.status == status)
        total = (
            self.session.scalar(select(func.count()).select_from(Complaint).where(*filters)) or 0
        )
        statement = (
            select(Complaint)
            .where(*filters)
            .order_by(Complaint.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.session.scalars(statement)), total

    def update_status(self, complaint: Complaint, status: Status) -> Complaint:
        complaint.status = status
        self.session.add(complaint)
        self.session.commit()
        self.session.refresh(complaint)
        return complaint

    def stats(self) -> dict[str, object]:
        category_rows = self.session.execute(
            select(Complaint.category, func.count()).group_by(Complaint.category)
        ).all()
        priority_rows = self.session.execute(
            select(Complaint.priority, func.count()).group_by(Complaint.priority)
        ).all()
        total = self.session.scalar(select(func.count()).select_from(Complaint)) or 0
        by_category = {category.value: 0 for category in Category}
        by_priority = {priority.value: 0 for priority in Priority}
        by_category.update({category.value: count for category, count in category_rows})
        by_priority.update({priority.value: count for priority, count in priority_rows})
        return {"by_category": by_category, "by_priority": by_priority, "total": total}

    def exists(self, complaint_id: UUID) -> bool:
        return self.session.get(Complaint, complaint_id) is not None
