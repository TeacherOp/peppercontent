"""Local file-backed store for generated reports.

No database — each report is a JSON file under ``data/reports/`` plus a small
``_index.json`` of metadata for the home-page list. Storing the full report
(including the Claude narrative) means reopening a saved report needs no
recompute and no second API call.
"""

import json
import os
import uuid
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "reports")
INDEX_PATH = os.path.join(DATA_DIR, "_index.json")


def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _path(report_id):
    return os.path.join(DATA_DIR, f"{report_id}.json")


def _write_json(path, obj):
    _ensure_dir()
    tmp = f"{path}.tmp"
    with open(tmp, "w") as fh:
        json.dump(obj, fh, indent=2)
    os.replace(tmp, path)  # atomic


def _load_index():
    if not os.path.exists(INDEX_PATH):
        return []
    with open(INDEX_PATH) as fh:
        return json.load(fh)


def valid_id(report_id):
    """Guard against path traversal — ids are hex only."""
    return bool(report_id) and report_id.isalnum()


def save_report(report):
    """Persist a built report; return its metadata entry."""
    report_id = uuid.uuid4().hex[:12]
    now = datetime.now()
    meta = {
        "id": report_id,
        "name": report["client"]["name"],          # default name, editable later
        "company": report["client"]["name"],
        "period": report["period"]["label"],
        "cadence": report["period"]["cadence"],
        "created_at": now.isoformat(timespec="seconds"),
        "created_display": now.strftime("%d %b %Y, %H:%M"),
        "created_date": now.strftime("%d %b %Y"),
        "created_time": now.strftime("%H:%M"),
    }
    _write_json(_path(report_id), {"meta": meta, "report": report})
    index = _load_index()
    index.insert(0, meta)  # newest first
    _write_json(INDEX_PATH, index)
    return meta


def list_reports():
    return _load_index()


def get_report(report_id):
    if not valid_id(report_id):
        return None
    path = _path(report_id)
    if not os.path.exists(path):
        return None
    with open(path) as fh:
        return json.load(fh)


def rename_report(report_id, name):
    data = get_report(report_id)
    if data is None:
        return None
    name = (name or "").strip() or "Untitled report"
    data["meta"]["name"] = name
    _write_json(_path(report_id), data)
    index = _load_index()
    for item in index:
        if item["id"] == report_id:
            item["name"] = name
    _write_json(INDEX_PATH, index)
    return name


_EDITABLE_ROOTS = {"executive_summary", "section_insights", "highlights", "recommendations"}


def update_narrative(report_id, edits):
    """Apply manager edits to the stored narrative.

    ``edits`` maps dotted paths (e.g. "section_insights.organic",
    "recommendations.0.title") to new text. Only existing keys under known
    narrative roots are updated — unknown paths are ignored.
    """
    data = get_report(report_id)
    if data is None:
        return False
    narrative = data.get("report", {}).get("narrative")
    if not isinstance(narrative, dict):
        return False
    for path, value in edits.items():
        if path == "recommendations" and isinstance(value, list):
            narrative["recommendations"] = _clean_recs(value)
            continue
        parts = path.split(".")
        if parts and parts[0] in _EDITABLE_ROOTS:
            _set_by_path(narrative, parts, str(value))
    _write_json(_path(report_id), data)
    return True


def _clean_recs(items):
    """Normalise an incoming recommendations list (add/remove/reorder safe)."""
    allowed = {"High", "Medium", "Low"}
    cleaned = []
    for item in items:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()
        detail = str(item.get("detail", "")).strip()
        if not title and not detail:
            continue
        priority = str(item.get("priority", "Medium")).strip().title()
        if priority not in allowed:
            priority = "Medium"
        cleaned.append({"title": title, "detail": detail, "priority": priority})
    return cleaned


def _set_by_path(node, parts, value):
    """Set value at a path, only when every step already exists."""
    for part in parts[:-1]:
        if isinstance(node, list):
            if not part.isdigit() or int(part) >= len(node):
                return
            node = node[int(part)]
        elif isinstance(node, dict):
            if part not in node:
                return
            node = node[part]
        else:
            return
    last = parts[-1]
    if isinstance(node, list):
        if last.isdigit() and int(last) < len(node):
            node[int(last)] = value
    elif isinstance(node, dict) and last in node:
        node[last] = value


def delete_report(report_id):
    if not valid_id(report_id):
        return False
    path = _path(report_id)
    if os.path.exists(path):
        os.remove(path)
    _write_json(INDEX_PATH, [i for i in _load_index() if i["id"] != report_id])
    return True
