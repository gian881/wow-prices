import json
import os
from io import BytesIO

import httpx
import pandas as pd
from bs4 import BeautifulSoup, Tag
from PIL import Image

from app.schemas import PriceGoldSilver


def get_env() -> dict[str, str]:
    with open("../.env", "r", encoding="utf-8") as file:
        env: dict[str, str] = dict()
        for line in file.readlines():
            key, value = line.split("=")
            env[key] = value.strip()
    return env


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


async def download_image(
    httpx_client: httpx.AsyncClient, url: str, file_path: str
):
    if os.path.exists(file_path):
        return
    img_response = await httpx_client.get(url)

    if img_response.status_code == 200:
        img = Image.open(BytesIO(img_response.content))
        img.save(file_path)


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
    raw_data: list[tuple[str, int, float]], column_name: str
):
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
