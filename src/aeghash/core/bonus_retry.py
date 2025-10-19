"""Retry processing for failed bonus credit attempts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Callable, Mapping

from aeghash.core.repositories import BonusEntryRecord, BonusRepository, BonusRetryRecord


@dataclass(slots=True)
class BonusRetryResult:
    """Summary of a retry processing run."""

    processed: int = 0
    succeeded: int = 0
    rescheduled: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)


class BonusRetryService:
    """Process queued bonus retries with exponential backoff."""

    def __init__(
        self,
        repository: BonusRepository,
        *,
        wallet_creditor: Callable[[Mapping[str, object]], None],
        now_factory: Callable[[], datetime] | None = None,
        base_delay_minutes: int = 15,
        backoff_factor: int = 2,
        max_retries: int = 5,
    ) -> None:
        self._repository = repository
        self._wallet_creditor = wallet_creditor
        self._now = now_factory or (lambda: datetime.now(UTC))
        self._base_delay = base_delay_minutes
        self._backoff_factor = max(backoff_factor, 1)
        self._max_retries = max_retries

    def process(self, *, limit: int = 100) -> BonusRetryResult:
        """Process queued retry records that are due."""
        now = self._now()
        candidates = self._repository.list_retry_candidates(now=now, limit=limit)
        result = BonusRetryResult(processed=len(candidates))

        for candidate in candidates:
            started_at = self._now()
            self._repository.mark_retry_started(candidate.queue_id, started_at=started_at)
            entry = self._repository.get_entry(candidate.bonus_id)
            if entry is None:
                self._repository.mark_retry_failed(
                    candidate.queue_id,
                    failed_at=self._now(),
                    metadata={"reason": "bonus_entry_missing"},
                )
                result.failed += 1
                result.errors.append(f"bonus entry '{candidate.bonus_id}' missing")
                continue

            try:
                self._credit_wallet(entry)
            except Exception as exc:  # pragma: no cover - defensive
                self._handle_failure(entry, candidate, str(exc), result)
            else:
                completed_at = self._now()
                self._repository.mark_confirmed(entry.bonus_id)
                self._repository.mark_retry_completed(candidate.queue_id, completed_at=completed_at)
                result.succeeded += 1
        return result

    # ------------------------------------------------------------------ helpers

    def _credit_wallet(self, entry: BonusEntryRecord) -> None:
        payload: Mapping[str, object] = {
            "user_id": entry.user_id,
            "amount": entry.bonus_amount,
            "metadata": dict(entry.metadata),
        }
        self._wallet_creditor(payload)

    def _handle_failure(
        self,
        entry: BonusEntryRecord,
        candidate: BonusRetryRecord,
        reason: str,
        result: BonusRetryResult,
    ) -> None:
        next_retry_count = max(candidate.retry_count, int(entry.metadata.get("retry_count", 0))) + 1
        metadata = dict(entry.metadata)
        metadata["retry_count"] = next_retry_count
        metadata["last_error"] = reason

        if next_retry_count >= self._max_retries:
            metadata["status"] = "failed"
            self._repository.mark_failed(entry.bonus_id, metadata)
            self._repository.mark_retry_failed(candidate.queue_id, failed_at=self._now(), metadata=metadata)
            result.failed += 1
            result.errors.append(reason)
            return

        retry_after = self._now() + self._compute_delay(next_retry_count)
        metadata["retry_after"] = retry_after.isoformat()
        self._repository.schedule_retry(entry.bonus_id, retry_after, metadata)
        result.rescheduled += 1
        result.errors.append(reason)

    def _compute_delay(self, retry_count: int) -> timedelta:
        exponent = max(retry_count - 1, 0)
        minutes = self._base_delay * (self._backoff_factor ** exponent)
        return timedelta(minutes=minutes)
