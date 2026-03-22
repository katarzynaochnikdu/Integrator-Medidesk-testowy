"""Lead event tracker – JSON-file based logging with full payload for retry."""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LeadEvent:
    integration_id: str
    lead_id: str
    timestamp: str
    status: str  # "received", "sent", "failed"
    mapped_fields_count: int = 0
    error: str = ""
    # Full payload for debugging / retry
    fb_raw_data: dict[str, Any] = field(default_factory=dict)
    mapped_values: dict[str, str] = field(default_factory=dict)
    medidesk_form_id: str = ""


@dataclass
class IntegrationStats:
    integration_id: str
    total: int = 0
    sent: int = 0
    failed: int = 0
    success_rate: float = 0.0
    last_lead_at: str = ""


def _log_path() -> Path:
    return Path(settings.lead_log_file)


def _load_log() -> list[dict[str, Any]]:
    path = _log_path()
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        logger.error("Failed to read lead log", exc_info=True)
        return []


def _save_log(data: list[dict[str, Any]]) -> None:
    path = _log_path()
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def log_lead_event(
    integration_id: str,
    lead_id: str,
    status: str,
    mapped_fields_count: int = 0,
    error: str = "",
    fb_raw_data: dict[str, Any] | None = None,
    mapped_values: dict[str, str] | None = None,
    medidesk_form_id: str = "",
) -> LeadEvent:
    """Log a lead processing event with full payload data."""
    event = LeadEvent(
        integration_id=integration_id,
        lead_id=lead_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        status=status,
        mapped_fields_count=mapped_fields_count,
        error=error,
        fb_raw_data=fb_raw_data or {},
        mapped_values=mapped_values or {},
        medidesk_form_id=medidesk_form_id,
    )
    log = _load_log()
    log.append(asdict(event))
    _save_log(log)
    logger.info("Lead event: %s lead=%s status=%s", integration_id, lead_id, status)
    return event


def get_lead_event(lead_id: str, status: str | None = None) -> dict[str, Any] | None:
    """Find a specific lead event (latest matching). If status given, filter by it."""
    log = _load_log()
    matches = [e for e in log if e["lead_id"] == lead_id]
    if status:
        matches = [e for e in matches if e["status"] == status]
    return matches[-1] if matches else None


def get_failed_leads(integration_id: str | None = None) -> list[dict[str, Any]]:
    """Get all failed leads, optionally filtered by integration."""
    log = _load_log()
    failed = [e for e in log if e["status"] == "failed"]
    if integration_id:
        failed = [e for e in failed if e["integration_id"] == integration_id]
    # Deduplicate: keep only latest event per lead_id
    seen = {}
    for e in failed:
        seen[e["lead_id"]] = e
    # Filter out leads that were later successfully sent
    sent_ids = {e["lead_id"] for e in log if e["status"] == "sent"}
    return [e for e in seen.values() if e["lead_id"] not in sent_ids]


def mark_retried(lead_id: str) -> None:
    """Add a 'retried' flag to the latest failed event for a lead."""
    log = _load_log()
    for i in range(len(log) - 1, -1, -1):
        if log[i]["lead_id"] == lead_id and log[i]["status"] == "failed":
            log[i]["retried"] = True
            break
    _save_log(log)


def get_stats(integration_id: str) -> IntegrationStats:
    """Get stats for a specific integration."""
    events = [e for e in _load_log() if e["integration_id"] == integration_id]
    total = len(events)
    sent = sum(1 for e in events if e["status"] == "sent")
    failed = sum(1 for e in events if e["status"] == "failed")
    last = events[-1]["timestamp"] if events else ""
    return IntegrationStats(
        integration_id=integration_id,
        total=total,
        sent=sent,
        failed=failed,
        success_rate=round(sent / total * 100, 1) if total > 0 else 0.0,
        last_lead_at=last,
    )


def get_global_stats() -> dict[str, Any]:
    """Aggregate stats across all integrations."""
    log = _load_log()
    total = len(log)
    sent = sum(1 for e in log if e["status"] == "sent")
    failed = sum(1 for e in log if e["status"] == "failed")
    return {
        "total_leads": total,
        "sent": sent,
        "failed": failed,
        "success_rate": round(sent / total * 100, 1) if total > 0 else 0.0,
        "last_lead_at": log[-1]["timestamp"] if log else "",
    }


def get_recent_leads(integration_id: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    """Get most recent lead events, optionally filtered by integration."""
    log = _load_log()
    if integration_id:
        log = [e for e in log if e["integration_id"] == integration_id]
    return list(reversed(log[-limit:]))  # most recent first
