"""Simple JSON-file based storage for FB→Medidesk integrations."""
from __future__ import annotations

import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


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


def _storage_path() -> Path:
    return Path(settings.integrations_file)


def _load_all() -> list[dict[str, Any]]:
    path = _storage_path()
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        logger.error("Failed to read integrations file", exc_info=True)
        return []


def _save_all(data: list[dict[str, Any]]) -> None:
    path = _storage_path()
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _dict_to_integration(d: dict[str, Any]) -> Integration:
    mappings = [FieldMapping(**m) for m in d.get("field_mappings", [])]
    return Integration(
        id=d["id"],
        fb_page_id=d["fb_page_id"],
        fb_page_name=d["fb_page_name"],
        fb_page_token=d["fb_page_token"],
        fb_form_id=d["fb_form_id"],
        fb_form_name=d["fb_form_name"],
        fb_form_questions=d.get("fb_form_questions", []),
        medidesk_form_id=d["medidesk_form_id"],
        medidesk_form_name=d.get("medidesk_form_name", ""),
        medidesk_fields=d.get("medidesk_fields", []),
        field_mappings=mappings,
        active=d.get("active", False),
        created_at=d.get("created_at", ""),
        updated_at=d.get("updated_at", ""),
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
    integration = Integration(
        id=str(uuid.uuid4()),
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
    all_data = _load_all()
    all_data.append(asdict(integration))
    _save_all(all_data)
    logger.info("Created integration %s (FB form %s → MD form %s)", integration.id, fb_form_id, medidesk_form_id)
    return integration


def get_integration(integration_id: str) -> Integration | None:
    for d in _load_all():
        if d["id"] == integration_id:
            return _dict_to_integration(d)
    return None


def get_all_integrations() -> list[Integration]:
    return [_dict_to_integration(d) for d in _load_all()]


def find_by_fb_form(fb_form_id: str) -> Integration | None:
    """Find active integration by Facebook form ID (used by webhook)."""
    for d in _load_all():
        if d.get("fb_form_id") == fb_form_id and d.get("active"):
            return _dict_to_integration(d)
    return None


def find_by_fb_page(fb_page_id: str) -> Integration | None:
    """Find active integration by Facebook page ID (used by webhook)."""
    for d in _load_all():
        if d.get("fb_page_id") == fb_page_id and d.get("active"):
            return _dict_to_integration(d)
    return None


def update_integration(integration_id: str, **updates: Any) -> Integration | None:
    all_data = _load_all()
    for i, d in enumerate(all_data):
        if d["id"] == integration_id:
            d.update(updates)
            d["updated_at"] = datetime.now(timezone.utc).isoformat()
            # Handle field_mappings if passed as list of FieldMapping
            if "field_mappings" in updates and updates["field_mappings"]:
                if hasattr(updates["field_mappings"][0], "__dataclass_fields__"):
                    d["field_mappings"] = [asdict(m) for m in updates["field_mappings"]]
            all_data[i] = d
            _save_all(all_data)
            return _dict_to_integration(d)
    return None


def delete_integration(integration_id: str) -> bool:
    all_data = _load_all()
    new_data = [d for d in all_data if d["id"] != integration_id]
    if len(new_data) == len(all_data):
        return False
    _save_all(new_data)
    return True
