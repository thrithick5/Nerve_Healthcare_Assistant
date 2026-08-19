from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class Message(BaseModel):
    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class Conversation(BaseModel):
    id: str
    messages: list[Message] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class RegisterRequest(BaseModel):
    email: str
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6)
    full_name: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    created_at: datetime


class GoogleAuthRequest(BaseModel):
    credential: str


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None
    file_sources: Optional[list[str]] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class Source(BaseModel):
    title: str = "Medical Source"
    content: str = ""
    relevance_score: float = 1.0
    url: Optional[str] = None
    source: Optional[str] = None

    model_config = {"extra": "ignore"}


class ChatResponse(BaseModel):
    reply: str
    conversation_id: int
    disclaimer: str
    sources: Optional[list[Source]] = None
    title: Optional[str] = None
    facility_data: Optional[dict] = None

    model_config = {"extra": "ignore"}


class ConversationSummary(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int


class ConversationDetail(BaseModel):
    id: int
    title: str
    created_at: datetime
    messages: list[dict]


class ResetResponse(BaseModel):
    message: str
    conversation_id: int


class HealthResponse(BaseModel):
    status: str
    version: str


class IngestResponse(BaseModel):
    success: bool
    message: str
    chunks_ingested: int
    total_chunks: Optional[int] = None


class UserSettingsUpdate(BaseModel):
    theme: Optional[str] = None
    language: Optional[str] = None


class ConversationRename(BaseModel):
    title: str


class SearchRequest(BaseModel):
    query: str


class FacilityRequest(BaseModel):
    health_issue: str
    location: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class FacilityItem(BaseModel):
    name: str
    rating: Optional[float] = None
    review_count: Optional[int] = None
    address: Optional[str] = ""
    maps_url: str
    source: str = "google_search"
    specialty: Optional[str] = None
    facility_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distance_km: Optional[float] = None
    phone: Optional[str] = None
    opening_hours: Optional[str] = None
    emergency: Optional[bool] = None


class FacilityResponse(BaseModel):
    specialty: str
    facility_types: list[str]
    search_url: str
    facilities: list[FacilityItem]
    formatted_markdown: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    resolved_location: bool = False
