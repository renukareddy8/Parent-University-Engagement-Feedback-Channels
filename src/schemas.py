from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class Category(str, Enum):
    ACADEMICS = "Academics"
    ADMIN = "Administration"
    HOUSING = "Housing"
    FINANCE = "Finance"
    FACILITIES = "Facilities"
    OTHER = "Other"


class FeedbackIn(BaseModel):
    parent_name: Optional[str] = Field(None, description="Parent's name")
    student_name: Optional[str] = Field(None, description="Student's name")
    student_id: Optional[str] = Field(None, description="Student ID")
    title: Optional[str] = Field(None, description="Short title for the feedback")
    contact: Optional[str] = Field(None, description="Contact info (email/phone)")
    text: str = Field(..., description="Feedback text from parent")


class FeedbackOut(FeedbackIn):
    id: int
    category: Category
    sentiment: str
    confidence: float
    department: str | None = None
    notified: bool | None = False
    status: str | None = "pending"
    submitted: str | None = None
    history: list | None = None
