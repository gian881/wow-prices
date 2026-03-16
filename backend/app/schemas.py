from enum import Enum

from pydantic import BaseModel


class Quality(Enum):
    normal = "normal"
    tier_1 = "tier_1"
    tier_2 = "tier_2"
    tier_3 = "tier_3"
    tier_4 = "tier_4"
    tier_5 = "tier_5"
    tier_1_midnight = "tier_1_midnight"
    tier_2_midnight = "tier_2_midnight"


class Intent(Enum):
    sell = "sell"
    buy = "buy"
    both = "both"


class Weekday(Enum):
    DOMINGO = "domingo"
    SEGUNDA = "segunda"
    TERCA = "terca"
    QUARTA = "quarta"
    QUINTA = "quinta"
    SEXTA = "sexta"
    SABADO = "sabado"


class NotificationType(Enum):
    price_above_alert = "price_above_alert"
    price_below_alert = "price_below_alert"
    price_above_best_avg_alert = "price_above_best_avg_alert"
    price_below_best_avg_alert = "price_below_best_avg_alert"


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
    intent: Intent = Intent.sell
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
    quality: Quality | None = None
    is_active: bool | None = None


class ItemForNotification(BaseModel):
    id: int
    name: str
    image_path: str
    quality: Quality
    rarity: Rarity


class BuyingSellingData(BaseModel):
    weekday: str
    hour: int
    price: PriceGoldSilver
    price_diff: PriceDiff


class ReturnItem(BaseModel):
    id: int
    name: str
    quality: Quality
    rarity: Rarity
    image: str
    intent: Intent
    quantity_threshold: int
    notify_sell: bool
    notify_buy: bool
    above_alert: PriceGoldSilver
    below_alert: PriceGoldSilver
    current_quantity: int
    current_price: PriceGoldSilver
    last_timestamp: str
    selling: BuyingSellingData | None
    buying: BuyingSellingData | None
    is_active: bool


class SimpleItem(BaseModel):
    id: int
    name: str
    price: PriceGoldSilver
    quality: Quality
    rarity: Rarity
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
