from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Prices(BaseModel):
    model_config = ConfigDict(extra="forbid")

    currency: str = "MXN"
    regular: Optional[float] = None
    sale: Optional[float] = None


class ProductBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = None
    description: Optional[str] = None
    is_kit: bool = False
    kit_includes: list[str] = Field(default_factory=list)
    prices: Prices = Field(default_factory=Prices)
    discount_text: Optional[str] = None


class PageExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page: int
    blocks: list[ProductBlock] = Field(default_factory=list)
