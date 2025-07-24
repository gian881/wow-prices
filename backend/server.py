import json
import os
import sqlite3

import httpx
import pandas as pd
from PIL import Image
from io import BytesIO
from bs4 import BeautifulSoup, Tag
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from blizzard_api import fetch_blizzard_api

app = FastAPI()

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")


def get_db():
    conn = sqlite3.connect("./data/test.db")
    try:
        yield conn
    finally:
        conn.close()


async def get_http_client():
    async with httpx.AsyncClient() as client:
        yield client


async def download_image(client: httpx.AsyncClient, url: str, file_path: str):
    if os.path.exists(file_path):
        return
    img_response = await client.get(url)

    if img_response.status_code == 200:
        img = Image.open(BytesIO(img_response.content))
        img.save(file_path)


async def get_item_quality(item_id: int, client: httpx.AsyncClient) -> int:
    response = await client.get(f"https://www.wowhead.com/item={item_id}")
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


def weekday(index: str) -> str:
    if index == "0":
        return "Domingo"
    if index == "1":
        return "Segunda"
    if index == "2":
        return "Terça"
    if index == "3":
        return "Quarta"
    if index == "4":
        return "Quinta"
    if index == "5":
        return "Sexta"
    if index == "6":
        return "Sábado"
    return "Domingo"


@app.get("/items/")
def get_items(request: Request, db: sqlite3.Connection = Depends(get_db)):
    result = db.execute(
        """WITH latest_prices AS (
                SELECT
                    item_id,
                    price,
                    quantity,
                    timestamp,
                    ROW_NUMBER() OVER(PARTITION BY item_id ORDER BY timestamp DESC) as rn
                FROM
                    price_history
            )
            SELECT
                i.id,
                i.name,
                i.image_path,
                i.quality,
                lp.price,
                lp.quantity,
                lp.timestamp,
                i.rarity
            FROM
                items AS i
            JOIN
                latest_prices AS lp ON i.id = lp.item_id
            WHERE
                lp.rn = 1
            ORDER BY lp.price DESC
        """
    ).fetchall()

    return [
        {
            "id": item[0],
            "name": item[1],
            "price": {
                "gold": int(item[4] / 10000),
                "silver": int((item[4] / 10000 - int(item[4] / 10000)) * 100),
            },
            "quality": item[3],
            "image": f"{request.base_url}{item[2]}",
            "rarity": item[7],
        }
        for item in result
    ]


@app.post("/items/{item_id}", status_code=201)
async def add_item(
    item_id: int,
    db: sqlite3.Connection = Depends(get_db),
    client: httpx.AsyncClient = Depends(get_http_client),
):
    result = db.execute(
        "SELECT * FROM items WHERE id = ?", (item_id,)
    ).fetchone()
    if result is not None:
        raise HTTPException(status_code=409, detail="Item já adicionado")
    try:
        item_response = await fetch_blizzard_api(
            f"https://us.api.blizzard.com/data/wow/item/{item_id}",
            client,
            {"namespace": "static-us", "locale": "pt_BR"},
            "Item",
        )

        img_response = await fetch_blizzard_api(
            item_response["media"]["key"]["href"],
            client,
        )

        img_url = img_response["assets"][0]["value"]
        img_path = os.path.join("static", "images", img_url.split("/")[-1])

        await download_image(client, img_url, img_path)

        item = {
            "id": item_id,
            "name": item_response["name"],
            "image_path": img_path.replace("\\", "/"),
            "quality": await get_item_quality(item_id, client),
            "rarity": item_response["quality"]["type"],
        }

        db.execute(
            "INSERT INTO items VALUES (:id, :name, :image_path, :quality, :rarity)",
            item,
        )
        db.commit()

        return item

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Erro ao se comunicar com a API externa: {e}",
        )
    except (KeyError, IndexError) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resposta inesperada da API da Blizzard: {e}",
        )


@app.get("/items/{item_id}")
def get_item(
    item_id: int, request: Request, db: sqlite3.Connection = Depends(get_db)
):
    name, image_path, quality, price, quantity, timestamp, rarity = db.execute(
        """SELECT
                i.name,
                i.image_path,
                i.quality,
                ph.price,
                ph.quantity,
                ph.timestamp,
                i.rarity
            FROM
                items AS i
            JOIN
                price_history AS ph ON i.id = ph.item_id
            WHERE
                i.id = ?
            ORDER BY
                ph.timestamp DESC
            LIMIT 1;
        """,
        (item_id,),
    ).fetchone()

    gold = int(price / 10000)
    silver = int((price / 10000 - gold) * 100)

    result = db.execute(
        "SELECT strftime('%w', timestamp), strftime('%H', timestamp), price FROM price_history WHERE item_id = ?",
        (item_id,),
    ).fetchall()

    result = (
        (weekday(item[0]), int(item[1]), item[2] / 10000) for item in result
    )
    df = pd.DataFrame(result)
    df.columns = ["weekday", "hour", "price"]
    weekday_order = [
        "Domingo",
        "Segunda",
        "Terça",
        "Quarta",
        "Quinta",
        "Sexta",
        "Sábado",
    ]
    df["weekday"] = pd.Categorical(
        df["weekday"], categories=weekday_order, ordered=True
    )
    df = df.groupby(["weekday", "hour"], observed=False)["price"].mean()
    heatmap_data = df.unstack(level="weekday")
    out = heatmap_data.to_json(orient="split")
    json_out = json.loads(out)
    ploty_heatmap_data = {
        "x": json_out["columns"],
        "y": [str(hour).zfill(2) + "h" for hour in json_out["index"]],
        "z": json_out["data"],
    }

    return {
        "name": name,
        "quality": quality,
        "rarity": rarity,
        "image": f"{request.base_url}{image_path}",
        "currentQuantity": quantity,
        "currentPrice": {"gold": gold, "silver": silver},
        "averagePriceData": ploty_heatmap_data,
        "lastTimeStamp": timestamp,
    }
