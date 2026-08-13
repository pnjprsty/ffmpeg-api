from pydantic import BaseModel, Field
from typing import List
from enum import Enum


class SceneType(str, Enum):
    """Scene type enum for different scene categories"""
    hook = "hook"
    context = "context"
    problem = "problem"
    deepening = "deepening"
    insight = "insight"
    advice = "advice"
    takeaway = "takeaway"
    cta = "cta"


class Scene(BaseModel):
    """Single scene with image, voice, and subtitle"""
    type: SceneType
    image: str = Field(..., description="Absolute path to image file")
    voice: str = Field(..., description="Absolute path to MP3 audio file")
    subtitleText: str = Field(..., description="Subtitle text to display during scene")


class RenderRequest(BaseModel):
    """Request body for video rendering"""
    ide: str = Field(..., description="Unique identifier for the video project", min_length=1)
    scenes: List[Scene] = Field(..., description="Array of scenes to render", min_items=1)


class RenderResponse(BaseModel):
    """Response after successful rendering"""
    success: bool
    ide: str
    filename: str
    output: str
    duration: float
    scenes: int


class ErrorResponse(BaseModel):
    """Error response"""
    success: bool = False
    error: str
    path: str = None
