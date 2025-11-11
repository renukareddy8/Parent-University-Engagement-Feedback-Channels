import os
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List

from .agents.classifier import analyze_feedback
from .routing import route_feedback, send_notification, DEPARTMENT_MAP
from . import storage
from .schemas import FeedbackIn, FeedbackOut

app = FastAPI(title="Parent-University Feedback Agent (Prototype)")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


@app.get("/")
async def index(request: Request):
    feedbacks = storage.list_feedbacks()
    return templates.TemplateResponse("index.html", {"request": request, "feedbacks": feedbacks})


@app.get("/admin")
async def admin(request: Request, category: str | None = None, sentiment: str | None = None, department: str | None = None):
    """Admin dashboard: filter feedbacks by category, sentiment, and department (all optional).

    Shows latest feedbacks and simple counts.
    """
    feedbacks = storage.list_feedbacks()

    def _matches(fb: dict) -> bool:
        if category and str(fb.get("category", "")).lower() != category.lower():
            return False
        if sentiment and str(fb.get("sentiment", "")).lower() != sentiment.lower():
            return False
        if department and str(fb.get("department", "")).lower() != department.lower():
            return False
        return True

    filtered = [fb for fb in feedbacks if _matches(fb)]

    # counts
    counts = {"total": len(feedbacks), "filtered": len(filtered)}

    # department choices for the filter (use names)
    dept_choices = sorted([v.get("name") for v in DEPARTMENT_MAP.values()])
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "feedbacks": filtered,
            "counts": counts,
            "filters": {"category": category, "sentiment": sentiment, "department": department},
            "departments": dept_choices,
        },
    )


@app.post("/admin/feedback/{feedback_id}/update")
async def admin_update_feedback(feedback_id: int, status: str = Form(...), note: str | None = Form(None)):
    """Admin action: update status for a feedback entry."""
    updated = storage.update_feedback_status(feedback_id, status, note)
    # redirect back to admin list
    return RedirectResponse(url=f"/admin", status_code=303)


@app.get("/admin/export")
async def admin_export():
    csv_data = storage.export_feedbacks_csv()
    return StreamingResponse(iter([csv_data.encode("utf-8")]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=feedbacks.csv"})


@app.get("/dashboard")
async def parent_dashboard(request: Request, parent: str | None = None):
    """Parent-facing dashboard. If `parent` query parameter is provided, filter feedbacks to that parent; otherwise show an overview."""
    feedbacks = storage.list_feedbacks()
    if parent:
        fb_list = [f for f in feedbacks if (f.get("parent_name") or "").lower() == parent.lower()]
    else:
        fb_list = feedbacks

    # summary counts
    total = len(feedbacks)
    by_status = {}
    by_sentiment = {"positive": 0, "neutral": 0, "negative": 0}
    for f in feedbacks:
        st = f.get("status", "pending")
        by_status[st] = by_status.get(st, 0) + 1
        s = f.get("sentiment", "neutral")
        if s in by_sentiment:
            by_sentiment[s] += 1

    # recent activity: sort by submitted desc and take latest 5
    def _submitted_key(x):
        return x.get("submitted") or ""

    recent = sorted(feedbacks, key=_submitted_key, reverse=True)[:5]

    return templates.TemplateResponse(
        "parent_dashboard.html",
        {
            "request": request,
            "total": total,
            "by_status": by_status,
            "by_sentiment": by_sentiment,
            "recent": recent,
            "history": fb_list,
        },
    )


@app.post("/submit")
async def submit_form(
    request: Request,
    parent_name: str = Form(None),
    student_name: str = Form(None),
    student_id: str = Form(None),
    contact: str = Form(None),
    title: str = Form(None),
    text: str = Form(...),
):
    payload = {
        "parent_name": parent_name,
        "student_name": student_name,
        "student_id": student_id,
        "title": title,
        "contact": contact,
        "text": text,
    }
    meta = analyze_feedback(text)
    dept = route_feedback(meta["category"], text)
    entry = {
        **payload,
        "category": meta["category"],
        "sentiment": meta["sentiment"],
        "confidence": meta.get("confidence", 0.5),
        "department": dept.get("name"),
        "department_email": dept.get("email"),
    }
    # try to notify department (will be simulated if SMTP not configured)
    notified = send_notification(entry)
    entry["notified"] = bool(notified)
    saved = storage.add_feedback(entry)
    return RedirectResponse(url="/", status_code=303)


@app.post("/api/feedback")
async def api_feedback(item: FeedbackIn):
    meta = analyze_feedback(item.text)
    dept = route_feedback(meta["category"], item.text)
    entry = {
        **item.dict(),
        "category": meta["category"],
        "sentiment": meta["sentiment"],
        "confidence": meta.get("confidence", 0.5),
        "department": dept.get("name"),
        "department_email": dept.get("email"),
    }
    notified = send_notification(entry)
    entry["notified"] = bool(notified)
    saved = storage.add_feedback(entry)
    return JSONResponse(saved)


@app.get("/api/feedbacks")
async def api_feedbacks():
    return JSONResponse(storage.list_feedbacks())
