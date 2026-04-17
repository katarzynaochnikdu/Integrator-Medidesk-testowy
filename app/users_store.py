"""User accounts store (FB-authenticated, no passwords).

Each login touches the users table — upsert_user keeps fb_user_name/email fresh
and bumps last_seen_at. Role/label/facility_id are managed by admin.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.db import get_connection

logger = logging.getLogger(__name__)


ROLES = ("owner", "admin", "viewer")


@dataclass
class User:
    fb_user_id: str
    fb_user_name: str
    email: str
    facility_id: str
    role: str
    label: str
    first_seen_at: str
    last_seen_at: str
    active: bool


def _row_to_user(row) -> User:
    return User(
        fb_user_id=row["fb_user_id"],
        fb_user_name=row["fb_user_name"] or "",
        email=row["email"] or "",
        facility_id=row["facility_id"] or "",
        role=row["role"] or "viewer",
        label=row["label"] or "",
        first_seen_at=row["first_seen_at"] or "",
        last_seen_at=row["last_seen_at"] or "",
        active=bool(row["active"]),
    )


def upsert_user(
    fb_user_id: str,
    fb_user_name: str = "",
    email: str = "",
    facility_id: str | None = None,
    role: str | None = None,
) -> User:
    """Insert or refresh a user record. Touches last_seen_at.

    If the user is new, creates with default role='viewer' (requires admin promotion
    before they get any facility access). If row exists, facility_id/role are NOT
    overwritten unless explicitly provided — admin-managed fields stay stable.
    """
    if not fb_user_id:
        raise ValueError("fb_user_id is required")

    now_iso = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    existing = conn.execute(
        "SELECT * FROM users WHERE fb_user_id = ?", (fb_user_id,)
    ).fetchone()

    if existing is None:
        conn.execute(
            """INSERT INTO users
               (fb_user_id, fb_user_name, email, facility_id, role, label, first_seen_at, last_seen_at, active)
               VALUES (?, ?, ?, ?, ?, '', ?, ?, 1)""",
            (
                fb_user_id,
                fb_user_name or "",
                email or "",
                facility_id or "",
                role or "viewer",
                now_iso,
                now_iso,
            ),
        )
    else:
        # Refresh volatile fields; preserve admin-managed ones unless overridden.
        new_facility = facility_id if facility_id is not None else existing["facility_id"]
        new_role = role if role is not None else existing["role"]
        conn.execute(
            """UPDATE users
               SET fb_user_name = COALESCE(NULLIF(?, ''), fb_user_name),
                   email = COALESCE(NULLIF(?, ''), email),
                   facility_id = ?,
                   role = ?,
                   last_seen_at = ?
               WHERE fb_user_id = ?""",
            (fb_user_name or "", email or "", new_facility, new_role, now_iso, fb_user_id),
        )
    conn.commit()

    row = conn.execute(
        "SELECT * FROM users WHERE fb_user_id = ?", (fb_user_id,)
    ).fetchone()
    return _row_to_user(row)


def get_user(fb_user_id: str) -> User | None:
    if not fb_user_id:
        return None
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE fb_user_id = ?", (fb_user_id,)
    ).fetchone()
    return _row_to_user(row) if row else None


def list_users(facility_id: str | None = None) -> list[User]:
    conn = get_connection()
    if facility_id:
        rows = conn.execute(
            "SELECT * FROM users WHERE facility_id = ? ORDER BY last_seen_at DESC",
            (facility_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM users ORDER BY last_seen_at DESC"
        ).fetchall()
    return [_row_to_user(r) for r in rows]


def set_role(fb_user_id: str, role: str) -> bool:
    if role not in ROLES:
        raise ValueError(f"role must be one of {ROLES}")
    conn = get_connection()
    cur = conn.execute("UPDATE users SET role = ? WHERE fb_user_id = ?", (role, fb_user_id))
    conn.commit()
    return cur.rowcount > 0


def set_label(fb_user_id: str, label: str) -> bool:
    conn = get_connection()
    cur = conn.execute("UPDATE users SET label = ? WHERE fb_user_id = ?", (label or "", fb_user_id))
    conn.commit()
    return cur.rowcount > 0


def set_facility(fb_user_id: str, facility_id: str, role: str = "viewer") -> bool:
    """Assign user to a facility (used by admin approving pending registration)."""
    if role not in ROLES:
        raise ValueError(f"role must be one of {ROLES}")
    conn = get_connection()
    cur = conn.execute(
        "UPDATE users SET facility_id = ?, role = ?, active = 1 WHERE fb_user_id = ?",
        (facility_id, role, fb_user_id),
    )
    conn.commit()
    return cur.rowcount > 0


def deactivate(fb_user_id: str) -> bool:
    """Soft-disable user (blocks login without deleting audit trail)."""
    conn = get_connection()
    cur = conn.execute("UPDATE users SET active = 0 WHERE fb_user_id = ?", (fb_user_id,))
    conn.commit()
    return cur.rowcount > 0


def log_integration_action(
    *,
    action: str,
    integration_id: str = "",
    facility_id: str = "",
    fb_user_id: str = "",
    fb_user_name: str = "",
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    ip: str = "",
    user_agent: str = "",
) -> None:
    """Write an entry to integrations_audit. Safe to call — never raises."""
    import json
    import time
    try:
        conn = get_connection()
        conn.execute(
            """INSERT INTO integrations_audit
               (ts, action, integration_id, facility_id, fb_user_id, fb_user_name, before, after, ip, user_agent)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                time.time(),
                action,
                integration_id or "",
                facility_id or "",
                fb_user_id or "",
                fb_user_name or "",
                json.dumps(before, ensure_ascii=False) if before is not None else "",
                json.dumps(after, ensure_ascii=False) if after is not None else "",
                ip or "",
                (user_agent or "")[:300],
            ),
        )
        conn.commit()
    except Exception:
        logger.warning("log_integration_action failed action=%s", action, exc_info=True)


def list_audit(
    facility_id: str | None = None,
    fb_user_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """Return audit entries joined with user labels (fb_user_name live from users)."""
    conn = get_connection()
    where = []
    params: list[Any] = []
    if facility_id:
        where.append("a.facility_id = ?")
        params.append(facility_id)
    if fb_user_id:
        where.append("a.fb_user_id = ?")
        params.append(fb_user_id)
    where_clause = ("WHERE " + " AND ".join(where)) if where else ""
    params.extend([limit, offset])
    rows = conn.execute(
        f"""SELECT a.*, u.fb_user_name AS live_user_name, u.label AS user_label, u.role AS user_role
            FROM integrations_audit a
            LEFT JOIN users u ON u.fb_user_id = a.fb_user_id
            {where_clause}
            ORDER BY a.ts DESC
            LIMIT ? OFFSET ?""",
        params,
    ).fetchall()
    return [
        {
            "ts": r["ts"],
            "action": r["action"],
            "integration_id": r["integration_id"],
            "facility_id": r["facility_id"],
            "fb_user_id": r["fb_user_id"],
            "fb_user_name": r["live_user_name"] or r["fb_user_name"] or "",
            "user_label": r["user_label"] or "",
            "user_role": r["user_role"] or "",
            "before": r["before"] or "",
            "after": r["after"] or "",
            "ip": r["ip"] or "",
        }
        for r in rows
    ]
