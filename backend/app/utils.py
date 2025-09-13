import json
import os
from io import BytesIO
from typing import Any, Sequence

import httpx
import pandas as pd
from bs4 import BeautifulSoup, Tag
from PIL import Image
from sqlalchemy import Row
from supabase import Client, create_client

from app.schemas import PriceGoldSilver
from exceptions import EnvNotSetError

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
        return (
            price_gold_and_silver.gold * 10000
            + price_gold_and_silver.silver * 100
        )
    return (
        price_gold_and_silver["gold"] * 10000
        + price_gold_and_silver["silver"] * 100
    )


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
        print(f"Failed to download image: {e}")
        return None
    except Exception as e:
        if "duplicate" in str(e).lower():
            print("Image already exists in Supabase, getting public URL.")
            return supabase_client.storage.from_(BUCKET_NAME).get_public_url(
                file_name
            )
        else:
            raise e


async def get_item_quality(
    item_id: int, httpx_client: httpx.AsyncClient
) -> int:
    response = await httpx_client.get(
        f"https://www.wowhead.com/item={item_id}/"
    )
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
                return 3
            if "tier2.png" in script_text:
                return 2
            if "tier1.png" in script_text:
                return 1
    return 0


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

    heatmap_df = pd.DataFrame(
        raw_data, columns=["weekday", "hour", column_name]
    )

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
