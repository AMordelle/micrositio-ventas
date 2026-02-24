from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Prices(BaseModel):
    model_config = ConfigDict(extra="forbid")

    currency: Literal["MXN"] = "MXN"
    regular: Optional[float] = None
    sale: Optional[float] = None


class DiscountBadge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    percent: Optional[int] = None
    kind: Literal["exact", "more_than", "up_to"]


class PageItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sku: str
    title: Optional[str] = None
    variant: Optional[str] = None
    size: Optional[str] = None
    prices: Prices = Field(default_factory=Prices)
    discount_badge: Optional[DiscountBadge] = None
    points: Optional[int] = None

    @model_validator(mode="after")
    def validate_required_sku(self) -> "PageItem":
        if not self.sku or not self.sku.strip():
            raise ValueError("sku is required and cannot be empty")
        self.sku = self.sku.strip()
        return self


class PageExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page: int
    items: list[PageItem] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_sku_per_page(self) -> "PageExtraction":
        seen: dict[str, PageItem] = {}
        for item in self.items:
            if item.sku in seen and item.model_dump() != seen[item.sku].model_dump():
                raise ValueError(f"duplicate SKU with inconsistent values: {item.sku}")
            seen[item.sku] = item
        return self
