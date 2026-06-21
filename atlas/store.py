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


def delete_report(report_id):
    if not valid_id(report_id):
        return False
    path = _path(report_id)
    if os.path.exists(path):
        os.remove(path)
    _write_json(INDEX_PATH, [i for i in _load_index() if i["id"] != report_id])
    return True
