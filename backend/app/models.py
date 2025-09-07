import datetime

from sqlmodel import Field, SQLModel

from app.schemas import Intent, NotificationType


# ===================================================================
# 2. Modelos de Tabela (SQLModel) - Mapeamento do Banco de Dados
# ===================================================================
class Item(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    image_path: str
    quality: int
    rarity: str
    quantity_threshold: int = 100
    intent: Intent = Intent.SELL
    above_alert: int = 0
    below_alert: int = 0
    notify_sell: bool = False
    notify_buy: bool = False


class Notification(SQLModel, table=True):
    id: int = Field(primary_key=True)
    type: NotificationType
    price_diff: int
    item_id: int = Field(foreign_key="items.id")
    read: bool = False
    created_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now, nullable=False
    )


class PriceHistory(SQLModel, table=True):
    item_id: int = Field(primary_key=True, foreign_key="items.id")
    price: int
    quantity: int
    timestamp: str = Field(primary_key=True)


class ItemCache(SQLModel, table=True):
    item_id: int = Field(primary_key=True)
    blizzard_image_url: str
    quality: int
