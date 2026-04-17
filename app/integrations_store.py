"""SQLite-backed storage for FB→Medidesk integrations."""
from __future__ import annotations

import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.config import settings
from app.db import get_connection

logger = logging.getLogger(__name__)


# ─── Fernet encryption for tokens ─────────────────────────────────

_fernet = None


def _get_fernet():
    global _fernet
    if _fernet is not None:
        return _fernet
    if not settings.encryption_key:
        return None
    from cryptography.fernet import Fernet
    try:
        _fernet = Fernet(settings.encryption_key.encode())
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Invalid encryption_key format: {e}")
        return None
    return _fernet


def _encrypt_token(plaintext: str) -> str:
    """Encrypt a token for at-rest storage."""
    f = _get_fernet()
    if not f:
        return plaintext  # dev mode: no encryption
    return f.encrypt(plaintext.encode()).decode()


def _decrypt_token(ciphertext: str) -> str:
    """Decrypt a stored token."""
    f = _get_fernet()
    if not f:
        return ciphertext  # dev mode: no encryption
    try:
        return f.decrypt(ciphertext.encode()).decode()
    except Exception:
        logger.warning("Failed to decrypt token — returning as-is (may be unencrypted)")
        return ciphertext


@dataclass
class FieldMapping:
    fb_field: str
    medidesk_field: str
    confidence: float = 0.0


@dataclass
class Integration:
    id: str
    fb_page_id: str
    fb_page_name: str
    fb_page_token: str
    fb_form_id: str
    fb_form_name: str
    fb_form_questions: list[dict[str, Any]]
    medidesk_form_id: str
    medidesk_form_name: str
    medidesk_fields: list[dict[str, Any]]
    field_mappings: list[FieldMapping]
    active: bool = False
    created_at: str = ""
    updated_at: str = ""


def _row_to_integration(row) -> Integration:
    mappings = [FieldMapping(**m) for m in json.loads(row["field_mappings"])]
    return Integration(
        id=row["id"],
        fb_page_id=row["fb_page_id"],
        fb_page_name=row["fb_page_name"],
        fb_page_token=_decrypt_token(row["fb_page_token"]),
        fb_form_id=row["fb_form_id"],
        fb_form_name=row["fb_form_name"],
        fb_form_questions=json.loads(row["fb_form_questions"]),
        medidesk_form_id=row["medidesk_form_id"],
        medidesk_form_name=row["medidesk_form_name"],
        medidesk_fields=json.loads(row["medidesk_fields"]),
        field_mappings=mappings,
        active=bool(row["active"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def create_integration(
    fb_page_id: str,
    fb_page_name: str,
    fb_page_token: str,
    fb_form_id: str,
    fb_form_name: str,
    fb_form_questions: list[dict[str, Any]],
    medidesk_form_id: str,
    medidesk_form_name: str,
    medidesk_fields: list[dict[str, Any]],
    field_mappings: list[FieldMapping],
) -> Integration:
    """Create and save a new integration."""
    now = datetime.now(timezone.utc).isoformat()
    integration_id = str(uuid.uuid4())
    integration = Integration(
        id=integration_id,
        fb_page_id=fb_page_id,
        fb_page_name=fb_page_name,
        fb_page_token=fb_page_token,
        fb_form_id=fb_form_id,
        fb_form_name=fb_form_name,
        fb_form_questions=fb_form_questions,
        medidesk_form_id=medidesk_form_id,
        medidesk_form_name=medidesk_form_name,
        medidesk_fields=medidesk_fields,
        field_mappings=field_mappings,
        active=False,
        created_at=now,
        updated_at=now,
    )
    conn = get_connection()
    conn.execute(
        """INSERT INTO integrations
           (id, fb_page_id, fb_page_name, fb_page_token,
            fb_form_id, fb_form_name, fb_form_questions,
            medidesk_form_id, medidesk_form_name, medidesk_fields,
            field_mappings, active, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            integration_id, fb_page_id, fb_page_name,
            _encrypt_token(fb_page_token),
            fb_form_id, fb_form_name,
            json.dumps(fb_form_questions, ensure_ascii=False),
            medidesk_form_id, medidesk_form_name,
            json.dumps(medidesk_fields, ensure_ascii=False),
            json.dumps([asdict(m) for m in field_mappings], ensure_ascii=False),
            0, now, now,
        ),
    )
    conn.commit()
    logger.info("Created integration %s (FB form %s → MD form %s)", integration_id, fb_form_id, medidesk_form_id)
    return integration


def get_integration(integration_id: str) -> Integration | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM integrations WHERE id = ?", (integration_id,)).fetchone()
    return _row_to_integration(row) if row else None


def get_all_integrations() -> list[Integration]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM integrations ORDER BY created_at DESC").fetchall()
    return [_row_to_integration(r) for r in rows]


def find_by_fb_form(fb_form_id: str) -> Integration | None:
    """Find active integration by Facebook form ID."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM integrations WHERE fb_form_id = ? AND active = 1",
        (fb_form_id,),
    ).fetchone()
    return _row_to_integration(row) if row else None


def find_by_fb_page(fb_page_id: str) -> Integration | None:
    """Find active integration by Facebook page ID (first match)."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM integrations WHERE fb_page_id = ? AND active = 1",
        (fb_page_id,),
    ).fetchone()
    return _row_to_integration(row) if row else None


def find_by_fb_page_and_form(fb_page_id: str, fb_form_id: str | None = None) -> Integration | None:
    """Find active integration by page + form ID. Falls back to page-only if no form match."""
    conn = get_connection()
    if fb_form_id:
        row = conn.execute(
            "SELECT * FROM integrations WHERE fb_page_id = ? AND fb_form_id = ? AND active = 1",
            (fb_page_id, fb_form_id),
        ).fetchone()
        if row:
            return _row_to_integration(row)
    # Fallback: match on page only
    row = conn.execute(
        "SELECT * FROM integrations WHERE fb_page_id = ? AND active = 1",
        (fb_page_id,),
    ).fetchone()
    return _row_to_integration(row) if row else None


def update_integration(integration_id: str, **updates: Any) -> Integration | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM integrations WHERE id = ?", (integration_id,)).fetchone()
    if not row:
        return None

    now = datetime.now(timezone.utc).isoformat()
    set_clauses = ["updated_at = ?"]
    params: list[Any] = [now]

    simple_fields = {"fb_page_id", "fb_page_name", "fb_form_id", "fb_form_name",
                     "medidesk_form_id", "medidesk_form_name"}

    for k, v in updates.items():
        if k == "active":
            set_clauses.append("active = ?")
            params.append(1 if v else 0)
        elif k == "fb_page_token":
            set_clauses.append("fb_page_token = ?")
            params.append(_encrypt_token(v))
        elif k == "field_mappings":
            set_clauses.append("field_mappings = ?")
            if v and hasattr(v[0], "__dataclass_fields__"):
                params.append(json.dumps([asdict(m) for m in v], ensure_ascii=False))
            else:
                params.append(json.dumps(v, ensure_ascii=False))
        elif k in simple_fields:
            set_clauses.append(f"{k} = ?")
            params.append(v)

    params.append(integration_id)
    conn.execute(
        f"UPDATE integrations SET {', '.join(set_clauses)} WHERE id = ?",
        params,
    )
    conn.commit()
    return get_integration(integration_id)


def delete_integration(integration_id: str) -> bool:
    conn = get_connection()
    cursor = conn.execute("DELETE FROM integrations WHERE id = ?", (integration_id,))
    conn.commit()
    return cursor.rowcount > 0
