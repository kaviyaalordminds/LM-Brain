"""
Content Specialist Domain Models.
Provides typed models and schemas for marketing copy, articles, social posts,
press releases, briefs, reviews, and multi-channel content assets.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field, field_validator


class ContentType(str, Enum):
    """Supported content asset types."""
    BLOG_POST = "BLOG_POST"
    SOCIAL_POST = "SOCIAL_POST"
    AD_COPY = "AD_COPY"
    PRESS_RELEASE = "PRESS_RELEASE"
    EMAIL = "EMAIL"


class Tone(str, Enum):
    """Supported voice and tone dimensions."""
    PROFESSIONAL = "PROFESSIONAL"
    FRIENDLY = "FRIENDLY"
    FORMAL = "FORMAL"
    CONVERSATIONAL = "CONVERSATIONAL"
    PERSUASIVE = "PERSUASIVE"
    INFORMATIVE = "INFORMATIVE"


class Channel(str, Enum):
    """Target distribution channels."""
    BLOG = "BLOG"
    LINKEDIN = "LINKEDIN"
    INSTAGRAM = "INSTAGRAM"
    EMAIL = "EMAIL"
    WEBSITE = "WEBSITE"
    PRESS = "PRESS"


class ContentMetadata(BaseModel):
    """
    Metadata associated with a generated or edited piece of content.
    """
    content_id: str = Field(default_factory=lambda: f"cnt_{uuid.uuid4().hex[:8]}")
    content_type: ContentType = ContentType.BLOG_POST
    channel: Channel = Channel.BLOG
    tone: Tone = Tone.PROFESSIONAL
    target_audience: str = "General Audience"
    title: Optional[str] = None
    language: str = "en"
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    custom_attributes: Dict[str, Any] = Field(default_factory=dict)


class ContentBrief(BaseModel):
    """
    Input brief specifying intent, target audience, tone, and key messaging points.
    """
    purpose: str = Field(..., min_length=1, description="Primary goal or message of the content")
    content_type: ContentType = ContentType.BLOG_POST
    channel: Channel = Channel.BLOG
    target_audience: str = "General Audience"
    tone: Tone = Tone.PROFESSIONAL
    key_points: List[str] = Field(default_factory=list)
    call_to_action: Optional[str] = None
    constraints: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("purpose")
    @classmethod
    def validate_purpose(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Content brief purpose cannot be empty.")
        return v.strip()


class ContentPiece(BaseModel):
    """
    Structured domain model representing a concrete content asset.
    """
    metadata: ContentMetadata
    title: Optional[str] = None
    body: str = Field(..., min_length=1, description="Main text body of the content")
    sections: Dict[str, str] = Field(default_factory=dict, description="Named subsections if multi-part")
    call_to_action: Optional[str] = None

    @field_validator("body")
    @classmethod
    def validate_body(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("ContentPiece body cannot be empty.")
        return v.strip()


class ContentReviewResult(BaseModel):
    """
    Result of a content validation / quality review inspection.
    """
    valid: bool = True
    issues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    checks_performed: List[str] = Field(default_factory=list)
