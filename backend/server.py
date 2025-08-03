import datetime
import itertools
import json
import os
import sqlite3
from io import BytesIO

import httpx
import pandas as pd
from bs4 import BeautifulSoup, Tag
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image
from unidecode import unidecode

# from sqlmodel import Field, SQLModel
from blizzard_api import fetch_blizzard_api
from models import ItemOptionalsCreate
from utils import price_to_gold_and_silver

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


# class Item(SQLModel, table=True):
#     id: int = Field(primary_key=True)
#     name: str
#     image_path: str
#     quality: int
#     rarity: str


# class PriceHistory(SQLModel, table=True):
#     item_id: int = Field(primary_key=True, foreign_key="items.id")
#     price: int
#     quantity: int
#     timestamp: str = Field(primary_key=True)


def get_db():
    conn = sqlite3.connect("./data/test.db", check_same_thread=False)
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


@app.get("/items/week")
def get_week_items(
    request: Request, db_conn: sqlite3.Connection = Depends(get_db)
):
    results = db_conn.execute("""
    WITH AggregatedHistory AS (    
        SELECT 
            item_id,
            strftime('%w', timestamp) AS weekday_num,
            CAST(strftime('%H', timestamp) AS INTEGER) AS hour,
            AVG(price) AS avg_price
        FROM price_history
        GROUP BY item_id, weekday_num, hour
    ),

    RankedHistory AS (
        SELECT *,
            ROW_NUMBER() OVER(PARTITION BY item_id ORDER BY avg_price DESC) AS rn
        FROM AggregatedHistory
    )

    SELECT
        i.id, -- 0
        i.name, -- 1
        i.quality, -- 2
        i.image_path, -- 3
        i.rarity, -- 4
        CASE rp.weekday_num
            WHEN '0' THEN 'Domingo'
            WHEN '1' THEN 'Segunda'
            WHEN '2' THEN 'Terça'
            WHEN '3' THEN 'Quarta'
            WHEN '4' THEN 'Quinta'
            WHEN '5' THEN 'Sexta'
            ELSE 'Sábado'
        END AS weekday, -- 5
        rp.hour, -- 6
        rp.avg_price / 10000 AS gold, -- 7
        (rp.avg_price % 10000) / 100 AS silver -- 8
    FROM RankedHistory rp
    JOIN items i ON i.id = rp.item_id
    WHERE rp.rn = 1
    ORDER BY rp.weekday_num, rp.hour""").fetchall()

    return [
        {
            "weekday": unidecode(weekday.lower()),
            "hours": [
                {
                    "hour": f"{hour}:00",
                    "items": [
                        {
                            "id": item[0],
                            "name": item[1],
                            "price": {
                                "gold": int(item[7]),
                                "silver": int(item[8]),
                            },
                            "quality": item[2],
                            "rarity": item[4],
                            "image": f"{request.base_url}{item[3]}",
                        }
                        for item in items
                    ],
                }
                for hour, items in itertools.groupby(hour_items, lambda x: x[6])
            ],
        }
        for weekday, hour_items in itertools.groupby(results, lambda x: x[5])
    ]


@app.get("/items/today")
def get_today_items(
    request: Request, db_conn: sqlite3.Connection = Depends(get_db)
):
    today_weekday = (
        datetime.datetime.now().weekday() + 1
    ) % 7  # Deixando weekday igual ao do SQL
    results = db_conn.execute(
        """
    WITH AggregatedHistory AS (    
        SELECT 
            item_id,
            strftime('%w', timestamp) AS weekday_num,
            CAST(strftime('%H', timestamp) AS INTEGER) AS hour,
            AVG(price) AS avg_price
        FROM price_history
        GROUP BY item_id, weekday_num, hour
    ),

    RankedHistory AS (
        SELECT *,
            ROW_NUMBER() OVER(PARTITION BY item_id ORDER BY avg_price DESC) AS rn
        FROM AggregatedHistory
    )

    SELECT
        i.id, -- 0
        i.name, -- 1
        i.quality, -- 2
        i.image_path, -- 3
        i.rarity, -- 4
        CASE rp.weekday_num
            WHEN '0' THEN 'Domingo'
            WHEN '1' THEN 'Segunda'
            WHEN '2' THEN 'Terça'
            WHEN '3' THEN 'Quarta'
            WHEN '4' THEN 'Quinta'
            WHEN '5' THEN 'Sexta'
            ELSE 'Sábado'
        END AS weekday, -- 5
        rp.hour, -- 6
        rp.avg_price / 10000 AS gold, -- 7
        (rp.avg_price % 10000) / 100 AS silver -- 8
    FROM RankedHistory rp
    JOIN items i ON i.id = rp.item_id
    WHERE rp.rn = 1 AND CAST (rp.weekday_num AS INTEGER) = ?
    ORDER BY rp.hour
    """,
        (today_weekday,),
    ).fetchall()

    return [
        {
            "hour": f"{str(hour).zfill(2)}:00",
            "items": [
                {
                    "id": item[0],
                    "name": item[1],
                    "price": {"gold": int(item[7]), "silver": int(item[8])},
                    "quality": item[2],
                    "rarity": item[4],
                    "image": f"{request.base_url}{item[3]}",
                }
                for item in items
            ],
        }
        for hour, items in itertools.groupby(results, key=lambda x: x[6])
    ]


@app.get("/items")
def get_items(request: Request, db_conn: sqlite3.Connection = Depends(get_db)):
    result = db_conn.execute(
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
    item_optionals: ItemOptionalsCreate,
    db_conn: sqlite3.Connection = Depends(get_db),
    client: httpx.AsyncClient = Depends(get_http_client),
):
    result = db_conn.execute(
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
            "quantity_threshold": item_optionals.quantity_threshold,
        }

        db_conn.execute(
            "INSERT INTO items(id, name, image_path, quality, rarity, quantity_threshold) VALUES (:id, :name, :image_path, :quality, :rarity, :quantity_threshold)",
            item,
        )
        db_conn.commit()

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
    item_id: int,
    request: Request,
    db_conn: sqlite3.Connection = Depends(get_db),
):
    item_details = db_conn.execute(
        """SELECT
                i.name,
                i.image_path,
                i.quality,
                i.rarity,
                ph.price,
                ph.quantity,
                ph.timestamp
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

    if not item_details:
        raise HTTPException(status_code=404, detail="Item não encontrado")

    (
        name,
        image_path,
        quality,
        rarity,
        price,
        quantity,
        timestamp,
    ) = item_details

    price_heatmap_raw_data = db_conn.execute(
        """
        SELECT
            CASE strftime('%w', timestamp)
                WHEN '0' THEN 'Domingo'
                WHEN '1' THEN 'Segunda'
                WHEN '2' THEN 'Terça'
                WHEN '3' THEN 'Quarta'
                WHEN '4' THEN 'Quinta'
                WHEN '5' THEN 'Sexta'
                WHEN '6' THEN 'Sábado'
            END AS weekday,
            CAST (strftime('%H', timestamp) AS INTEGER) AS hour,
            AVG(price) / 10000.0 AS avg_price
        FROM price_history
        WHERE item_id = ?
        GROUP BY weekday, hour
        ORDER BY strftime('%w', timestamp), hour;""",
        (item_id,),
    ).fetchall()

    plotly_price_heatmap_data = get_plotly_heatmap_data(
        price_heatmap_raw_data, "price"
    )

    quantity_heatmap_raw_data = db_conn.execute(
        """
        SELECT
            CASE strftime('%w', timestamp)
                WHEN '0' THEN 'Domingo'
                WHEN '1' THEN 'Segunda'
                WHEN '2' THEN 'Terça'
                WHEN '3' THEN 'Quarta'
                WHEN '4' THEN 'Quinta'
                WHEN '5' THEN 'Sexta'
                WHEN '6' THEN 'Sábado'
            END AS weekday,
            CAST (strftime('%H', timestamp) AS INTEGER) AS hour,
            AVG(quantity) AS avg_quantity
        FROM price_history
        WHERE item_id = ?
        GROUP BY weekday, hour
        ORDER BY strftime('%w', timestamp), hour;""",
        (item_id,),
    ).fetchall()

    plotly_quantity_heatmap_data = get_plotly_heatmap_data(
        quantity_heatmap_raw_data, "quantity"
    )

    selling_data = db_conn.execute(
        """
        SELECT
            -- 1. Formata os dados para ficarem legíveis
            CASE strftime('%w', timestamp)
                WHEN '0' THEN 'Domingo'
                WHEN '1' THEN 'Segunda'
                WHEN '2' THEN 'Terça'
                WHEN '3' THEN 'Quarta'
                WHEN '4' THEN 'Quinta'
                WHEN '5' THEN 'Sexta'
                ELSE 'Sábado'
            END AS weekday,
            CAST(strftime('%H', timestamp) AS INTEGER) AS hour,
            AVG(price) AS best_avg_price
        FROM
            price_history

        WHERE
            -- 2. Filtra para o item específico que você quer
            item_id = ?

        GROUP BY
            -- 3. Agrupa por cada "janela" de dia da semana e hora
            weekday,
            hour

        ORDER BY
            -- 4. Ordena os resultados, colocando o maior preço médio no topo
            best_avg_price DESC

        LIMIT 1; -- 5. Pega APENAS o primeiro resultado (o melhor) """,
        (item_id,),
    ).fetchone()

    weekday, hour, best_avg_price = selling_data

    gold, silver = price_to_gold_and_silver(price)
    best_avg_gold, best_avg_silver = price_to_gold_and_silver(best_avg_price)

    diff = price - best_avg_price
    diff_gold, diff_silver = price_to_gold_and_silver(diff)

    now = datetime.datetime.now()
    last_week_start = (now - datetime.timedelta(days=7)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    last_week_data = db_conn.execute(
        f"""
        SELECT
            strftime('%F %T', timestamp), -- 0
            price / 10000.0, -- 1
            quantity -- 2
        FROM price_history
        WHERE item_id = ? AND timestamp >= '{last_week_start}'
        ORDER BY timestamp DESC
        LIMIT {7 * 24};
        """,
        (item_id,),
    ).fetchall()

    line_chart_price_data = {
        "x": [data[0] for data in last_week_data],
        "y": [data[1] for data in last_week_data],
    }

    line_chart_quantity_data = {
        "x": [data[0] for data in last_week_data],
        "y": [data[2] for data in last_week_data],
    }

    return {
        "name": name,
        "quality": quality,
        "rarity": rarity,
        "image": f"{request.base_url}{image_path}",
        "currentQuantity": quantity,
        "currentPrice": {"gold": int(gold), "silver": silver},
        "averagePriceData": plotly_price_heatmap_data,
        "averageQuantityData": plotly_quantity_heatmap_data,
        "lastWeekData": {
            "price": line_chart_price_data,
            "quantity": line_chart_quantity_data,
        },
        "lastTimeStamp": timestamp,
        "selling": {
            "weekday": weekday,
            "hour": hour,
            "price": {"gold": best_avg_gold, "silver": best_avg_silver},
            "priceDiff": {
                "sign": "positive" if diff >= 0 else "negative",
                "gold": abs(diff_gold),
                "silver": abs(diff_silver),
            },
        },
    }
