"""Lead event tracker — SQLite-backed logging with full payload for retry."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.db import get_connection

logger = logging.getLogger(__name__)


@dataclass
class LeadEvent:
    integration_id: str
    lead_id: str
    timestamp: str
    status: str  # "received", "sent", "failed"
    mapped_fields_count: int = 0
    error: str = ""
    fb_raw_data: dict[str, Any] | None = None
    mapped_values: dict[str, str] | None = None
    medidesk_form_id: str = ""


@dataclass
class IntegrationStats:
    integration_id: str
    total: int = 0
    sent: int = 0
    failed: int = 0
    success_rate: float = 0.0
    last_lead_at: str = ""


def _row_to_dict(row) -> dict[str, Any]:
    """Convert a SQLite Row to a dict with parsed JSON fields."""
    d = dict(row)
    for json_field in ("fb_raw_data", "mapped_values"):
        if json_field in d and isinstance(d[json_field], str):
            try:
                d[json_field] = json.loads(d[json_field])
            except Exception:
                d[json_field] = {}
    d["retried"] = bool(d.get("retried", 0))
    return d


# SQL fragment that hides events belonging to deleted integrations (orphans).
# Non-admin callers pass `include_orphans=False` to keep a clean history view
# — admins pass True so they retain the 72h restore window.
_ORPHAN_HIDE_CLAUSE = (
    "(integration_deleted_at IS NULL OR integration_deleted_at = '')"
)


def _orphan_clause(include_orphans: bool, prefix: str = "AND") -> str:
    """Produce `AND <hide>` (or `WHERE <hide>`) when orphans must be hidden."""
    return "" if include_orphans else f" {prefix} {_ORPHAN_HIDE_CLAUSE}"


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
    conn = get_connection()
    conn.execute(
        """INSERT INTO lead_events
           (integration_id, lead_id, timestamp, status,
            mapped_fields_count, error, fb_raw_data,
            mapped_values, medidesk_form_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            event.integration_id, event.lead_id,
            event.timestamp, event.status,
            event.mapped_fields_count, event.error,
            json.dumps(event.fb_raw_data, ensure_ascii=False),
            json.dumps(event.mapped_values, ensure_ascii=False),
            event.medidesk_form_id,
        ),
    )
    conn.commit()
    logger.info("Lead event: %s lead=%s status=%s", integration_id, lead_id, status)
    return event


def get_lead_event(
    lead_id: str,
    status: str | None = None,
    include_orphans: bool = True,
) -> dict[str, Any] | None:
    """Find a specific lead event (latest matching). If status given, filter by it.

    `include_orphans=False` hides events whose integration was soft-deleted.
    The retry path passes True because it needs to resolve event data even
    for deleted integrations (so admins can still retry within the 72h window).
    """
    conn = get_connection()
    orphan_sql = _orphan_clause(include_orphans)
    if status:
        row = conn.execute(
            f"SELECT * FROM lead_events WHERE lead_id = ? AND status = ?{orphan_sql} ORDER BY id DESC LIMIT 1",
            (lead_id, status),
        ).fetchone()
    else:
        row = conn.execute(
            f"SELECT * FROM lead_events WHERE lead_id = ?{orphan_sql} ORDER BY id DESC LIMIT 1",
            (lead_id,),
        ).fetchone()
    return _row_to_dict(row) if row else None


def get_failed_leads(
    integration_id: str | None = None,
    include_orphans: bool = True,
) -> list[dict[str, Any]]:
    """Get all failed leads (not yet successfully retried).

    `include_orphans=False` hides leads from soft-deleted integrations.
    """
    conn = get_connection()
    orphan_sql = _orphan_clause(include_orphans)
    if integration_id:
        rows = conn.execute(
            f"""SELECT le.* FROM lead_events le
               INNER JOIN (
                   SELECT lead_id, MAX(id) as max_id
                   FROM lead_events
                   WHERE status = 'failed' AND integration_id = ?{orphan_sql}
                   GROUP BY lead_id
               ) latest ON le.id = latest.max_id
               WHERE le.lead_id NOT IN (
                   SELECT lead_id FROM lead_events WHERE status = 'sent'
               )
               ORDER BY le.id DESC""",
            (integration_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            f"""SELECT le.* FROM lead_events le
               INNER JOIN (
                   SELECT lead_id, MAX(id) as max_id
                   FROM lead_events
                   WHERE status = 'failed'{orphan_sql}
                   GROUP BY lead_id
               ) latest ON le.id = latest.max_id
               WHERE le.lead_id NOT IN (
                   SELECT lead_id FROM lead_events WHERE status = 'sent'
               )
               ORDER BY le.id DESC""",
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def mark_retried(lead_id: str) -> None:
    """Mark the latest failed event for a lead as retried."""
    conn = get_connection()
    conn.execute(
        """UPDATE lead_events SET retried = 1
           WHERE id = (
               SELECT id FROM lead_events
               WHERE lead_id = ? AND status = 'failed'
               ORDER BY id DESC LIMIT 1
           )""",
        (lead_id,),
    )
    conn.commit()


def get_stats(integration_id: str, include_orphans: bool = True) -> IntegrationStats:
    """Get stats for a specific integration.

    Counts *unique* leads, not every attempt. A lead counts as 'sent' if it was
    ever successfully sent (even after retries); 'failed' only if it has at least
    one failed attempt and was never sent. `include_orphans=False` hides events
    from soft-deleted integrations (typically: the integration itself is still
    live, so the flag rarely changes output here — but kept for consistency).
    """
    conn = get_connection()
    orphan_sql = _orphan_clause(include_orphans)
    row = conn.execute(
        f"""SELECT
               COUNT(DISTINCT lead_id) as total,
               COUNT(DISTINCT CASE WHEN status = 'sent' THEN lead_id END) as sent,
               COUNT(DISTINCT CASE
                   WHEN status = 'failed' AND lead_id NOT IN (
                       SELECT lead_id FROM lead_events
                       WHERE status = 'sent' AND integration_id = ?
                   ) THEN lead_id
               END) as failed,
               MAX(timestamp) as last_lead_at
           FROM lead_events
           WHERE integration_id = ?{orphan_sql}""",
        (integration_id, integration_id),
    ).fetchone()
    total = row["total"] or 0
    sent = row["sent"] or 0
    failed = row["failed"] or 0
    return IntegrationStats(
        integration_id=integration_id,
        total=total,
        sent=sent,
        failed=failed,
        success_rate=round(sent / total * 100, 1) if total > 0 else 0.0,
        last_lead_at=row["last_lead_at"] or "",
    )


def get_global_stats(include_orphans: bool = True) -> dict[str, Any]:
    """Aggregate stats across all integrations. Counts unique leads — see get_stats.

    `include_orphans=False` excludes events whose integration was soft-deleted,
    so non-admins see KPI counters that match their filtered "Ostatnie leady".
    """
    conn = get_connection()
    orphan_sql = _orphan_clause(include_orphans, prefix="WHERE")
    row = conn.execute(
        f"""SELECT
               COUNT(DISTINCT lead_id) as total,
               COUNT(DISTINCT CASE WHEN status = 'sent' THEN lead_id END) as sent,
               COUNT(DISTINCT CASE
                   WHEN status = 'failed' AND lead_id NOT IN (
                       SELECT lead_id FROM lead_events WHERE status = 'sent'
                   ) THEN lead_id
               END) as failed,
               MAX(timestamp) as last_lead_at
           FROM lead_events{orphan_sql}""",
    ).fetchone()
    total = row["total"] or 0
    sent = row["sent"] or 0
    failed = row["failed"] or 0
    return {
        "total_leads": total,
        "sent": sent,
        "failed": failed,
        "success_rate": round(sent / total * 100, 1) if total > 0 else 0.0,
        "last_lead_at": row["last_lead_at"] or "",
    }


def get_recent_leads(
    integration_id: str | None = None,
    limit: int = 20,
    include_orphans: bool = True,
) -> list[dict[str, Any]]:
    """Get most recent lead events, optionally filtered by integration.

    `include_orphans=False` hides events whose integration was soft-deleted.
    """
    conn = get_connection()
    if integration_id:
        orphan_sql = _orphan_clause(include_orphans)
        rows = conn.execute(
            f"SELECT * FROM lead_events WHERE integration_id = ?{orphan_sql} ORDER BY id DESC LIMIT ?",
            (integration_id, limit),
        ).fetchall()
    else:
        orphan_sql = _orphan_clause(include_orphans, prefix="WHERE")
        rows = conn.execute(
            f"SELECT * FROM lead_events{orphan_sql} ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [_row_to_dict(r) for r in rows]
