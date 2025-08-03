from enum import Enum
from pydantic import BaseModel


class Intent(Enum):
    SELL = "sell"
    BUY = "buy"
    BOTH = "both"


class ItemOptionalsCreate(BaseModel):
    quantity_threshold: int = 100
    intent: Intent = Intent.SELL
    above_alert: int | None = None
    below_alert: int | None = None
