import datetime
from enum import Enum

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class Intent(Enum):
    SELL = "sell"
    BUY = "buy"
    BOTH = "both"


class NotificationType(Enum):
    PRICE_ABOVE_ALERT = "price_above_alert"
    PRICE_BELOW_ALERT = "price_below_alert"
    PRICE_ABOVE_BEST_AVG_ALERT = "price_above_best_avg_alert"
    PRICE_BELOW_BEST_AVG_ALERT = "price_below_best_avg_alert"


class PriceGoldSilver(BaseModel):
    gold: int
    silver: int


class CreateItemOptions(BaseModel):
    quantity_threshold: int = 100
    intent: Intent = Intent.SELL
    above_alert: PriceGoldSilver = PriceGoldSilver(gold=0, silver=0)
    below_alert: PriceGoldSilver = PriceGoldSilver(gold=0, silver=0)
    notify_sell: bool = False
    notify_buy: bool = False


class EditItem(BaseModel):
    quantity_threshold: int | None = None
    intent: Intent | None = None
    above_alert: PriceGoldSilver | None = None
    below_alert: PriceGoldSilver | None = None
    notify_sell: bool | None = None
    notify_buy: bool | None = None


class ItemForNotification(BaseModel):
    id: int
    name: str
    image_path: str
    quality: int
    rarity: str


class Sign(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"


class PriceDiff(BaseModel):
    sign: Sign
    gold: int
    silver: int


class BuyingSellingData(BaseModel):
    weekday: str
    hour: int
    price: PriceGoldSilver
    price_diff: PriceDiff


class ReturnItem(BaseModel):
    id: int
    name: str
    quality: int
    rarity: str
    image: str
    intent: Intent
    quantity_threshold: int
    notify_sell: bool
    notify_buy: bool
    above_alert: PriceGoldSilver
    below_alert: PriceGoldSilver
    current_quantity: int
    current_price: PriceGoldSilver
    average_price_data: dict
    average_quantity_data: dict
    last_week_data: dict
    last_timestamp: str
    selling: BuyingSellingData | None
    buying: BuyingSellingData | None


class Notification(SQLModel, table=True):
    id: int = Field(primary_key=True)
    type: NotificationType
    price_diff: int
    item_id: int = Field(foreign_key="items.id")
    read: bool = False
    created_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now, nullable=False
    )


class Item(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    image_path: str
    quality: int
    rarity: str


class PriceHistory(SQLModel, table=True):
    item_id: int = Field(primary_key=True, foreign_key="items.id")
    price: int
    quantity: int
    timestamp: str = Field(primary_key=True)


class ItemCache(SQLModel, table=True):
    item_id: int = Field(primary_key=True)
    blizzard_image_url: str
    quality: int
