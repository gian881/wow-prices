from enum import Enum

from pydantic import BaseModel


class Intent(Enum):
    SELL = "sell"
    BUY = "buy"
    BOTH = "both"


class Weekday(Enum):
    DOMINGO = "domingo"
    SEGUNDA = "segunda"
    TERCA = "terca"
    QUARTA = "quarta"
    QUINTA = "quinta"
    SEXTA = "sexta"
    SABADO = "sabado"


class NotificationType(Enum):
    PRICE_ABOVE_ALERT = "price_above_alert"
    PRICE_BELOW_ALERT = "price_below_alert"
    PRICE_ABOVE_BEST_AVG_ALERT = "price_above_best_avg_alert"
    PRICE_BELOW_BEST_AVG_ALERT = "price_below_best_avg_alert"


class Rarity(Enum):
    POOR = "POOR"
    COMMON = "COMMON"
    UNCOMMON = "UNCOMMON"
    RARE = "RARE"
    EPIC = "EPIC"
    LEGENDARY = "LEGENDARY"
    ARTIFACT = "ARTIFACT"
    HEIRLOOM = "HEIRLOOM"


class Sign(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"


class PriceGoldSilver(BaseModel):
    gold: int
    silver: int


class PriceDiff(BaseModel):
    sign: Sign
    gold: int
    silver: int


class ErrorResponse(BaseModel):
    status: str
    message: str


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


class SimpleItem(BaseModel):
    id: int
    name: str
    price: PriceGoldSilver
    quality: int
    rarity: str
    image: str


class Hour(BaseModel):
    hour: str
    items: list[SimpleItem]


class WeekResponse(BaseModel):
    weekday: Weekday
    hours: list[Hour]


class TodayItem(SimpleItem):
    intent: Intent
    notify_sell: bool
    notify_buy: bool


class TodayResponse(BaseModel):
    hour: str
    items: list[TodayItem]
