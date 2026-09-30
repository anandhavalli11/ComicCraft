from typing import List, Optional

from pydantic import BaseModel, Field


class ComicRequest(BaseModel):

    story: str = Field(
        ...,
        min_length=3,
        max_length=5000
    )

    character: str = Field(
        ...,
        min_length=1,
        max_length=200
    )

    setting: str = Field(
        ...,
        min_length=1,
        max_length=200
    )

    tone: str = Field(
        default="adventure",
        max_length=100
    )

    art_style: str = Field(
        default="cartoon",
        max_length=100
    )

    panel_count: int = Field(
        default=5,
        ge=3,
        le=8
    )


class Panel(BaseModel):

    panel_number: int

    title: str

    scene: str

    narration: str

    dialogue: str

    image_prompt: str

    image_url: Optional[str] = None


class ComicResponse(BaseModel):

    title: str

    story: str

    character: str

    setting: str

    tone: str

    art_style: str

    panels: List[Panel]

    pdf_url: Optional[str] = None