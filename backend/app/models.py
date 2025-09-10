import datetime

from sqlmodel import Field, SQLModel

from app.schemas import Intent, NotificationType, Rarity


class Item(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    image_path: str
    quality: int = Field(default=0)
    rarity: Rarity = Field(default=Rarity.COMMON)
    quantity_threshold: int = Field(default=100)
    intent: Intent = Field(default=Intent.SELL)
    above_alert: int = Field(default=0)
    below_alert: int = Field(default=0)
    notify_sell: bool = Field(default=False)
    notify_buy: bool = Field(default=False)


class Notification(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    type: NotificationType
    price_diff: int = Field(default=0)
    current_price: int
    price_threshold: int
    item_id: int = Field(foreign_key="items.id")
    read: bool = Field(default=False)
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )


class PriceHistory(SQLModel, table=True):
    item_id: int = Field(primary_key=True, foreign_key="items.id")
    price: int
    quantity: int = Field(default=0)
    timestamp: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )


class ItemCache(SQLModel, table=True):
    item_id: int = Field(primary_key=True)
    name: str
    blizzard_image_url: str
    quality: int = Field(default=0)
    rarity: Rarity = Field(default=Rarity.COMMON)
