import os
import smtplib
from email.message import EmailMessage
from typing import Optional, Dict

# Simple mapping from category to department metadata
DEPARTMENT_MAP: Dict[str, Dict[str, str]] = {
    "Academics": {"name": "Academic Affairs", "email": "academics@university.edu"},
    "Administration": {"name": "Student Administration", "email": "admin@university.edu"},
    "Housing": {"name": "Housing Services", "email": "housing@university.edu"},
    "Finance": {"name": "Finance Office", "email": "finance@university.edu"},
    "Facilities": {"name": "Facilities", "email": "facilities@university.edu"},
    # More fine-grained department for food-related issues
    "Food Services": {"name": "Food Services", "email": "food@university.edu"},
    "Other": {"name": "General Inquiries", "email": "info@university.edu"},
}


def route_feedback(category: str, text: str | None = None) -> Dict[str, str]:
    """Map a category and (optionally) feedback text to a department dict with keys `name` and `email`.

    If `text` contains specific keywords we map to a finer-grained department (e.g., food/cafeteria -> Food Services).
    Otherwise we fall back to the category mapping. If category is unknown we return `Other`.
    """
    # keyword -> department name mapping (lowercase keywords)
    KEYWORD_MAP = {
        "food": "Food Services",
        "cafeteria": "Food Services",
        "dining": "Food Services",
        "canteen": "Food Services",
        "meal": "Food Services",
        # other possible overrides
        "parking": "Facilities",
        "library": "Facilities",
    }

    # Check text-based overrides first if text is provided
    if text:
        text_l = text.lower()
        for kw, dept_name in KEYWORD_MAP.items():
            if kw in text_l:
                return DEPARTMENT_MAP.get(dept_name, DEPARTMENT_MAP["Other"])

    # Fallback to category mapping
    return DEPARTMENT_MAP.get(category, DEPARTMENT_MAP["Other"])


def send_notification(entry: dict) -> bool:
    """Send (or simulate) a notification for a feedback entry.

    Returns True if a notification was actually attempted (SMTP configured and send succeeded),
    False otherwise (no SMTP config or send failed). The function will not raise on failure.
    """
    # Only attempt SMTP if SMTP_HOST is provided in env
    host = os.getenv("SMTP_HOST")
    if not host:
        # Not configured — simulate by printing to console / logs
        print(f"[Notifier] Simulated notify -> {entry.get('department')} <{entry.get('department_email')}>: {entry.get('text')[:120]}")
        return False

    try:
        port = int(os.getenv("SMTP_PORT", "587"))
        user = os.getenv("SMTP_USER")
        password = os.getenv("SMTP_PASS")
        use_tls = os.getenv("SMTP_TLS", "true").lower() in ("1", "true", "yes")
        from_addr = os.getenv("SMTP_FROM", user or f"noreply@{host}")

        msg = EmailMessage()
        msg["Subject"] = f"Parent feedback — {entry.get('category')}"
        msg["From"] = from_addr
        msg["To"] = entry.get("department_email")
        body = (
            f"Parent: {entry.get('parent_name') or 'Anonymous'}\n"
            f"Student: {entry.get('student_name') or 'N/A'}\n"
            f"Contact: {entry.get('contact') or 'N/A'}\n\n"
            f"Message:\n{entry.get('text')}"
        )
        msg.set_content(body)

        server = smtplib.SMTP(host, port, timeout=10)
        try:
            if use_tls:
                server.starttls()
            if user and password:
                server.login(user, password)
            server.send_message(msg)
        finally:
            server.quit()

        print(f"[Notifier] Sent email to {entry.get('department_email')}")
        return True
    except Exception as ex:
        print(f"[Notifier] Failed to send notification: {ex}")
        return False
