from __future__ import annotations

import structlog

logger = structlog.get_logger()


def check_negative_list(
    entity_name: str,
    list_type: str = "individual",
    negative_entries: list[dict] | None = None,
) -> dict:
    """Check whether an entity appears in a negative / blacklist.

    Parameters
    ----------
    entity_name:
        Name of the person or company to look up.
    list_type:
        ``"individual"`` or ``"company"`` -- controls which entries are
        relevant when filtering.
    negative_entries:
        A list of dicts, each containing at least ``"name"`` and
        optionally ``"type"`` (``"individual"`` / ``"company"``),
        ``"reason"``, and ``"date_added"``.
        If *None* an empty list is assumed (no blacklist data).

    Returns
    -------
    dict
        ``{"is_negative": bool, "matched_entry": dict | None}``
    """
    if negative_entries is None:
        negative_entries = []

    entity_lower = entity_name.strip().lower()

    for entry in negative_entries:
        entry_name = entry.get("name", "").strip().lower()
        entry_type = entry.get("type", list_type)

        # Skip entries that belong to a different list type
        if entry_type != list_type:
            continue

        # Exact match or substring containment both count
        if entry_name == entity_lower or entry_name in entity_lower or entity_lower in entry_name:
            logger.warning(
                "negative_list_hit",
                entity_name=entity_name,
                matched_name=entry.get("name"),
                list_type=list_type,
            )
            return {"is_negative": True, "matched_entry": entry}

    logger.info("negative_list_clear", entity_name=entity_name, list_type=list_type)
    return {"is_negative": False, "matched_entry": None}
