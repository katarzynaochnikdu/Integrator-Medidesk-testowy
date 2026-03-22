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


def get_lead_event(lead_id: str, status: str | None = None) -> dict[str, Any] | None:
    """Find a specific lead event (latest matching). If status given, filter by it."""
    conn = get_connection()
    if status:
        row = conn.execute(
            "SELECT * FROM lead_events WHERE lead_id = ? AND status = ? ORDER BY id DESC LIMIT 1",
            (lead_id, status),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT * FROM lead_events WHERE lead_id = ? ORDER BY id DESC LIMIT 1",
            (lead_id,),
        ).fetchone()
    return _row_to_dict(row) if row else None


def get_failed_leads(integration_id: str | None = None) -> list[dict[str, Any]]:
    """Get all failed leads (not yet successfully retried)."""
    conn = get_connection()
    if integration_id:
        rows = conn.execute(
            """SELECT le.* FROM lead_events le
               INNER JOIN (
                   SELECT lead_id, MAX(id) as max_id
                   FROM lead_events
                   WHERE status = 'failed' AND integration_id = ?
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
            """SELECT le.* FROM lead_events le
               INNER JOIN (
                   SELECT lead_id, MAX(id) as max_id
                   FROM lead_events
                   WHERE status = 'failed'
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


def get_stats(integration_id: str) -> IntegrationStats:
    """Get stats for a specific integration."""
    conn = get_connection()
    row = conn.execute(
        """SELECT
               COUNT(*) as total,
               SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent,
               SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
               MAX(timestamp) as last_lead_at
           FROM lead_events
           WHERE integration_id = ?""",
        (integration_id,),
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


def get_global_stats() -> dict[str, Any]:
    """Aggregate stats across all integrations."""
    conn = get_connection()
    row = conn.execute(
        """SELECT
               COUNT(*) as total,
               SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent,
               SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
               MAX(timestamp) as last_lead_at
           FROM lead_events""",
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


def get_recent_leads(integration_id: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    """Get most recent lead events, optionally filtered by integration."""
    conn = get_connection()
    if integration_id:
        rows = conn.execute(
            "SELECT * FROM lead_events WHERE integration_id = ? ORDER BY id DESC LIMIT ?",
            (integration_id, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM lead_events ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [_row_to_dict(r) for r in rows]
