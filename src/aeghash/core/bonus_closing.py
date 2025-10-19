"""Closing workflow for confirming pending bonus entries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Mapping, Optional, Sequence

from aeghash.core.repositories import BonusEntryRecord, BonusRepository


@dataclass(slots=True)
class BonusClosingJob:
    job_id: str
    closing_date: datetime
    started_at: datetime
    completed_at: Optional[datetime]
    total_entries: int = 0
    confirmed_entries: int = 0
    retry_entries: int = 0
    failed_entries: int = 0
    summary: Mapping[str, object] | None = None


class BonusClosingError(RuntimeError):
    """Raised when closing job encounters fatal errors."""


class BonusClosingService:
    """Confirm pending bonus entries and schedule retries."""

    def __init__(
        self,
        repository: BonusRepository,
        *,
        wallet_creditor,
        now_factory: callable | None = None,
        id_factory: callable | None = None,
        retry_backoff_minutes: int = 10,
        max_retries: int = 5,
    ) -> None:
        self._repository = repository
        self._wallet_creditor = wallet_creditor
        self._now = now_factory or (lambda: datetime.now(UTC))
        self._id_factory = id_factory or (lambda: self._now().strftime("closing-%Y%m%d%H%M%S"))
        self._retry_delay = timedelta(minutes=retry_backoff_minutes)
        self._max_retries = max_retries

    def run_closing(self) -> BonusClosingJob:
        job = BonusClosingJob(
            job_id=str(self._id_factory()),
            closing_date=self._now().date(),
            started_at=self._now(),
            completed_at=None,
        )

        entries = self._repository.list_pending(limit=500)
        job.total_entries = len(entries)

        for entry in entries:
            try:
                self._credit_wallet(entry)
            except Exception as exc:  # pragma: no cover - failure path
                self._schedule_retry(entry, reason=str(exc))
                job.retry_entries += 1
            else:
                job.confirmed_entries += 1

        job.completed_at = self._now()
        job.summary = {
            "job_id": job.job_id,
            "closing_date": str(job.closing_date),
            "total_entries": job.total_entries,
            "confirmed": job.confirmed_entries,
            "retry": job.retry_entries,
            "failed": job.failed_entries,
            "duration_ms": int((job.completed_at - job.started_at).total_seconds() * 1000),
        }
        return job

    # ------------------------------------------------------------------ helpers

    def _credit_wallet(self, entry: BonusEntryRecord) -> None:
        payload = {
            "user_id": entry.user_id,
            "amount": entry.bonus_amount,
            "metadata": dict(entry.metadata),
        }
        self._wallet_creditor(payload)
        self._repository.mark_confirmed(entry.bonus_id)

    def _schedule_retry(self, entry: BonusEntryRecord, *, reason: str) -> None:
        metadata = dict(entry.metadata)
        retry_count = int(metadata.get("retry_count", 0)) + 1
        metadata["retry_count"] = retry_count
        metadata["last_error"] = reason
        if retry_count >= self._max_retries:
            metadata["status"] = "failed"
            self._repository.mark_failed(entry.bonus_id, metadata)
        else:
            retry_after = self._now() + self._retry_delay
            metadata["retry_after"] = retry_after.isoformat()
            self._repository.schedule_retry(entry.bonus_id, retry_after, metadata)
