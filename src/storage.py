import json
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "feedbacks.json"

# In-memory store
_feedbacks: List[Dict[str, Any]] = []
_next_id = 1


def _ensure_file():
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text("[]")


def load_feedbacks() -> List[Dict[str, Any]]:
    global _feedbacks, _next_id
    try:
        _ensure_file()
        _feedbacks = json.loads(DATA_FILE.read_text())
        if _feedbacks:
            _next_id = max(item.get("id", 0) for item in _feedbacks) + 1
    except Exception:
        _feedbacks = []
        _next_id = 1
    return _feedbacks


def save_feedbacks():
    try:
        _ensure_file()
        DATA_FILE.write_text(json.dumps(_feedbacks, indent=2, ensure_ascii=False))
    except Exception:
        pass


def add_feedback(entry: Dict[str, Any]) -> Dict[str, Any]:
    global _next_id
    entry = dict(entry)
    entry.setdefault("id", _next_id)
    _next_id += 1
    # ensure status and submitted timestamp exist
    entry.setdefault("status", "pending")
    if not entry.get("submitted"):
        entry["submitted"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    # initialize history
    entry.setdefault("history", [])
    _feedbacks.append(entry)
    save_feedbacks()
    return entry


def update_feedback_status(feedback_id: int, new_status: str, note: str | None = None, actor: str | None = None) -> Dict[str, Any] | None:
    """Update the status of a feedback entry and append an audit history record.

    Returns the updated entry or None if not found.
    """
    for fb in _feedbacks:
        if fb.get("id") == int(feedback_id):
            prev = fb.get("status", "pending")
            fb["status"] = new_status
            when = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            rec = {"when": when, "actor": actor or "admin", "from": prev, "to": new_status}
            if note:
                rec["note"] = note
            fb.setdefault("history", []).append(rec)
            save_feedbacks()
            return fb
    return None


def export_feedbacks_csv() -> str:
    """Return a CSV string of all feedbacks for export.

    Columns: id,parent_name,student_name,student_id,title,category,department,sentiment,status,submitted,text
    """
    import csv
    from io import StringIO

    out = StringIO()
    writer = csv.writer(out)
    writer.writerow(["id", "parent_name", "student_name", "student_id", "title", "category", "department", "sentiment", "status", "submitted", "text"])
    for fb in _feedbacks:
        writer.writerow([
            fb.get("id"),
            fb.get("parent_name"),
            fb.get("student_name"),
            fb.get("student_id"),
            fb.get("title"),
            fb.get("category"),
            fb.get("department"),
            fb.get("sentiment"),
            fb.get("status"),
            fb.get("submitted"),
            (fb.get("text") or "").replace("\n", " "),
        ])
    return out.getvalue()


def list_feedbacks() -> List[Dict[str, Any]]:
    return _feedbacks


# Load at import to populate store if file exists
load_feedbacks()
