from typing import List, Optional
from pydantic import BaseModel
from enum import Enum

# Updated Pydantic model for Congress API
class Bill(BaseModel):
    congress: Optional[int] = None
    latest_action_date: Optional[str] = None
    latest_action_text: Optional[str] = None
    number: Optional[str] = None
    origin_chamber: Optional[str] = None
    origin_chamber_code: Optional[str] = None
    title: Optional[str] = None
    type: Optional[str] = None
    update_date: Optional[str] = None
    update_date_including_text: Optional[str] = None
    url: Optional[str] = None

class BillSummary(BaseModel):
    action_date: str
    action_desc: str
    text: str
    markdown_text: str
    update_date: str
    version_code: str
    congress: Optional[int] = None
    number: Optional[str] = None
    origin_chamber: Optional[str] = None
    origin_chamber_code: Optional[str] = None
    title: Optional[str] = None
    type: Optional[str] = None
    update_date_including_text: Optional[str] = None
    url: Optional[str] = None

class TextFormat(BaseModel):
    type: str
    url: str

class TextVersion(BaseModel):
    date: Optional[str]
    formats: List[TextFormat]
    type: str 

# Add these new models
class President(str, Enum):
    CLINTON = "william-j-clinton"
    BUSH = "george-w-bush"
    OBAMA = "barack-obama"
    TRUMP = "donald-trump"
    BIDEN = "joe-biden"

class DocumentType(str, Enum):
    DETERMINATION = "determination"
    EXECUTIVE_ORDER = "executive_order"
    MEMORANDUM = "memorandum"
    NOTICE = "notice"
    PROCLAMATION = "proclamation"
    PRESIDENTIAL_ORDER = "presidential_order"
    OTHER = "other"

class PresidentialDocument(BaseModel):
    title: str
    type: str
    document_number: str
    html_url: str
    pdf_url: str
    public_inspection_pdf_url: Optional[str]
    publication_date: str
    abstract: Optional[str] = None
    excerpts: Optional[str] = None