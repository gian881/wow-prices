import datetime
import json
import os
import zoneinfo
from typing import Any, Sequence

import httpx
import pandas as pd
from bs4 import BeautifulSoup, Tag
from sqlalchemy import Row
from sqlmodel import Session, select

from app.blizzard_api import fetch_blizzard_api
from app.logger import get_logger
from app.models import Settings
from app.schemas import PriceGoldSilver, Quality
from exceptions import EnvNotSetError
from supabase import Client, create_client

logger = get_logger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
if not SUPABASE_URL:
    raise EnvNotSetError("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_KEY:
    raise EnvNotSetError("SUPABASE_KEY")

supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
BUCKET_NAME = "images"


def price_to_gold_and_silver(price: int | float) -> PriceGoldSilver:
    """Converte o preço em centavos para ouro e prata."""
    gold = int(price) // 10000
    silver = (int(price) % 10000) // 100
    return PriceGoldSilver(gold=gold, silver=silver)


def gold_and_silver_to_price(
    price_gold_and_silver: PriceGoldSilver | dict[str, int],
) -> int:
    """Converte ouro e prata para preço em centavos."""
    if isinstance(price_gold_and_silver, PriceGoldSilver):
        return price_gold_and_silver.gold * 10000 + price_gold_and_silver.silver * 100
    return price_gold_and_silver["gold"] * 10000 + price_gold_and_silver["silver"] * 100


async def download_image_and_upload_to_supabase(
    httpx_client: httpx.AsyncClient, url: str, file_name: str
):
    try:
        img_response = await httpx_client.get(url)
        img_response.raise_for_status()
        supabase_client.storage.from_(BUCKET_NAME).upload(
            file_name, img_response.content
        )
        public_url = supabase_client.storage.from_(BUCKET_NAME).get_public_url(
            file_name
        )
        return public_url
    except httpx.HTTPStatusError as e:
        logger.error(f"Failed to download image: {e}")
        return None
    except Exception as e:
        if "duplicate" in str(e).lower():
            logger.info("Image already exists in Supabase, getting public URL.")
            return supabase_client.storage.from_(BUCKET_NAME).get_public_url(file_name)
        else:
            logger.error(f"Unexpected error downloading image: {e}", exc_info=True)
            raise e


async def get_item_quality(item_id: int, httpx_client: httpx.AsyncClient) -> Quality:
    response = await httpx_client.get(f"https://www.wowhead.com/item={item_id}/")
    if response.status_code == 301:
        response = await httpx_client.get(
            f"https://www.wowhead.com{response.headers['location']}"
        )
    soup = BeautifulSoup(response.content, "html.parser")
    script = soup.find("script", {"id": "data.page.wow.item.contextNames"})
    if script and script.next_sibling and isinstance(script.next_sibling, Tag):
        script_text = script.next_sibling.string
        if script_text:
            if "tier3.png" in script_text:
                return Quality.tier_1
            if "tier2.png" in script_text:
                return Quality.tier_2
            if "tier1.png" in script_text:
                return Quality.tier_3
    return Quality.normal


def get_plotly_heatmap_data(
    raw_data: Sequence[Row[Any]],
    column_name: str,
):
    if not raw_data:
        return {"x": [], "y": [], "z": []}

    weekday_order = [
        "Domingo",
        "Segunda",
        "Terça",
        "Quarta",
        "Quinta",
        "Sexta",
        "Sábado",
    ]

    heatmap_df = pd.DataFrame(raw_data, columns=["weekday", "hour", column_name])

    heatmap_df["weekday"] = pd.Categorical(
        heatmap_df["weekday"], categories=weekday_order, ordered=True
    )
    heatmap_df = heatmap_df.set_index(["weekday", "hour"])
    heatmap_data = heatmap_df[column_name].unstack(level="weekday").sort_index()

    heatmap_data_json = json.loads(heatmap_data.to_json(orient="split"))
    return {
        "x": heatmap_data_json["columns"],
        "y": [f"{str(hour).zfill(2)}h" for hour in heatmap_data_json["index"]],
        "z": heatmap_data_json["data"],
    }


async def get_item_blizzard_image_url(
    httpx_client: httpx.AsyncClient, item_id: int
) -> str | None:
    try:
        item_response = await fetch_blizzard_api(
            f"https://us.api.blizzard.com/data/wow/item/{item_id}",
            httpx_client,
            {"namespace": "static-us", "locale": "pt_BR"},
            "Item",
        )
        img_response = await fetch_blizzard_api(
            item_response["media"]["key"]["href"],
            httpx_client,
        )
        return img_response["assets"][0]["value"]
    except Exception as e:
        logger.error(
            f"Failed to get Blizzard image URL for item {item_id}: {e}", exc_info=True
        )
        return None


def best_price_window_start_date(db_session: Session) -> datetime.datetime | None:
    best_price_window_days_db = db_session.exec(
        select(Settings.value).where(Settings.key == "best_price_window_days")
    ).one_or_none()

    best_price_window_days = "all"

    if best_price_window_days_db != "all" and best_price_window_days_db is not None:
        best_price_window_days = int(best_price_window_days_db)

    window_start = None
    if best_price_window_days != "all":
        sao_paulo = zoneinfo.ZoneInfo("America/Sao_Paulo")
        now_sp = datetime.datetime.now(sao_paulo)
        target_date = (now_sp - datetime.timedelta(days=best_price_window_days)).date()
        window_start_local = datetime.datetime(
            target_date.year,
            target_date.month,
            target_date.day,
            tzinfo=sao_paulo,
        )
        window_start = window_start_local.astimezone(datetime.timezone.utc)

    return window_start
