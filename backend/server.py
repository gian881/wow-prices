import datetime
import itertools
import json
import os
import sqlite3
from io import BytesIO

import httpx
import pandas as pd
from bs4 import BeautifulSoup, Tag
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Security,
    WebSocket,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from PIL import Image
from unidecode import unidecode

from blizzard_api import fetch_blizzard_api
from models import (
    CreateItemOptions,
    EditItem,
    Intent,
    ItemForNotification,
    NotificationType,
    PriceGoldSilver,
    ReturnItem,
)
from utils import get_env, gold_and_silver_to_price, price_to_gold_and_silver

app = FastAPI()

API_KEY_HEADER = APIKeyHeader(name="X-Internal-Secret")
INTERNAL_WEBHOOK_SECRET = get_env().get("INTERNAL_WEBHOOK_SECRET", "")

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
    conn = sqlite3.connect("./data/test.db", check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)


connection_manager = ConnectionManager()


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
    response = await client.get(f"https://www.wowhead.com/item={item_id}/")
    if response.status_code == 301:
        response = await client.get(
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


async def create_and_broadcast_notification(
    db_conn: sqlite3.Connection,
    base_url: str,
    item: ItemForNotification,
    notification_type: NotificationType,
    current_price: int,
    price_diff: int,
    price_threshold: int | None = None,
):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")[:-3]

    db_conn.execute(
        """
        INSERT INTO notifications(type, price_diff, current_price, price_threshold, item_id, created_at) 
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            notification_type.value,
            price_diff,
            current_price,
            price_threshold,
            item.id,
            now,
        ),
    )
    db_conn.commit()

    notification_id = db_conn.execute("SELECT last_insert_rowid()").fetchone()[
        0
    ]
    price_diff_obj = price_to_gold_and_silver(price_diff)
    current_price_obj = price_to_gold_and_silver(current_price)

    if price_threshold is not None:
        price_threshold_obj = price_to_gold_and_silver(price_threshold)
    else:
        price_threshold_obj = None

    message = {
        "action": "new_notification",
        "data": {
            "id": notification_id,
            "type": notification_type.value,
            "price_diff": price_diff_obj,
            "current_price": current_price_obj,
            "price_threshold": (
                None if price_threshold is None else price_threshold_obj
            ),
            "item": {
                "id": item.id,
                "name": item.name,
                "image": f"{base_url}{item.image_path}",
                "quality": item.quality,
                "rarity": item.rarity,
            },
            "read": False,
            "created_at": now,
        },
    }

    await connection_manager.broadcast(message)


async def notify_price_below(db_conn: sqlite3.Connection, base_url: str):
    items_to_notify = db_conn.execute("""
        WITH latest_prices AS
        (SELECT item_id,
                price,
                quantity,
                timestamp,
                ROW_NUMBER() OVER(PARTITION BY item_id ORDER BY timestamp DESC) AS rn
        FROM price_history)
        SELECT i.id,
            i.name,
            i.image_path,
            i.quality,
            i.rarity,
            i.below_alert,
            lp.price
        FROM items AS i
        JOIN latest_prices AS lp ON i.id = lp.item_id
        WHERE lp.rn = 1
        AND lp.price < i.below_alert
        AND i.below_alert > 0
        ORDER BY lp.price DESC
    """).fetchall()

    for item in items_to_notify:
        (
            item_id,
            name,
            image_path,
            quality,
            rarity,
            price_threshold,
            current_price,
        ) = item

        await create_and_broadcast_notification(
            db_conn,
            base_url,
            ItemForNotification(
                id=item_id,
                name=name,
                image_path=image_path,
                quality=quality,
                rarity=rarity,
            ),
            NotificationType.PRICE_BELOW_ALERT,
            current_price,
            abs(current_price - price_threshold),
            price_threshold,
        )


async def notify_price_above(db_conn: sqlite3.Connection, base_url: str):
    items_to_notify = db_conn.execute("""
       WITH latest_prices AS
        (SELECT item_id,
                price,
                quantity,
                timestamp,
                ROW_NUMBER() OVER(PARTITION BY item_id ORDER BY timestamp DESC) AS rn
        FROM price_history)
        SELECT i.id,
            i.name,
            i.image_path,
            i.quality,
            i.rarity,
            i.above_alert,
            lp.price
        FROM items AS i
        JOIN latest_prices AS lp ON i.id = lp.item_id
        WHERE lp.rn = 1
        AND lp.price > i.above_alert
        AND i.above_alert > 0
        ORDER BY lp.price DESC
    """).fetchall()

    for item in items_to_notify:
        (
            item_id,
            name,
            image_path,
            quality,
            rarity,
            price_threshold,
            current_price,
        ) = item

        await create_and_broadcast_notification(
            db_conn,
            base_url,
            ItemForNotification(
                id=item_id,
                name=name,
                image_path=image_path,
                quality=quality,
                rarity=rarity,
            ),
            NotificationType.PRICE_ABOVE_ALERT,
            current_price,
            abs(current_price - price_threshold),
            price_threshold,
        )


async def notify_price_below_best_avg(
    db_conn: sqlite3.Connection, base_url: str
):
    items_to_notify = db_conn.execute("""
        WITH latest_prices AS (
            -- Pega o preço mais recente de cada item
            SELECT item_id, price, ROW_NUMBER() OVER(PARTITION BY item_id ORDER BY timestamp DESC) AS rn
            FROM price_history
        ),
        lowest_avg_prices AS (
            -- Calcula a menor média de preço histórica para cada item
            SELECT item_id, MIN(avg_price) as min_avg_price
            FROM (
                -- Primeiro, calcula a média para cada dia/hora
                SELECT item_id, AVG(price) as avg_price
                FROM price_history
                GROUP BY item_id, strftime('%w', timestamp), strftime('%H', timestamp)
            )
            GROUP BY item_id
        )
        -- Junta tudo e filtra os itens que atendem à condição
        SELECT
            i.id,
            i.name,
            i.image_path,
            i.quality,
            i.rarity,
            lp.price AS current_price,
            lap.min_avg_price
        FROM items i
        JOIN latest_prices lp ON i.id = lp.item_id
        JOIN lowest_avg_prices lap ON i.id = lap.item_id
        WHERE
            (i.intent = 'buy' OR i.intent = 'both') -- Considera apenas itens que são para compra
            AND i.notify_buy = 1 -- Considera apenas itens que têm notificação de compra ativada
            AND lp.rn = 1 -- Garante que estamos usando o preço mais recente
            AND lp.price < lap.min_avg_price -- A condição principal da notificação!
    """).fetchall()

    for item in items_to_notify:
        (
            item_id,
            name,
            image_path,
            quality,
            rarity,
            current_price,
            min_avg_price,
        ) = item

        await create_and_broadcast_notification(
            db_conn,
            base_url,
            ItemForNotification(
                id=item_id,
                name=name,
                image_path=image_path,
                quality=quality,
                rarity=rarity,
            ),
            NotificationType.PRICE_BELOW_BEST_AVG_ALERT,
            current_price,
            abs(current_price - min_avg_price),
        )


async def notify_price_above_best_avg(
    db_conn: sqlite3.Connection, base_url: str
):
    items_to_notify = db_conn.execute("""
        WITH latest_prices AS (
            SELECT item_id, price, ROW_NUMBER() OVER(PARTITION BY item_id ORDER BY timestamp DESC) AS rn
            FROM price_history
        ),
        highest_avg_prices AS (
            -- Calcula a MAIOR média de preço histórica para cada item
            SELECT item_id, MAX(avg_price) as max_avg_price
            FROM (
                -- Primeiro, calcula a média para cada dia/hora
                SELECT item_id, AVG(price) as avg_price
                FROM price_history
                GROUP BY item_id, strftime('%w', timestamp), strftime('%H', timestamp)
            )
            GROUP BY item_id
        )
        -- Junta tudo e filtra os itens que atendem à condição
        SELECT
            i.id,
            i.name,
            i.image_path,
            i.quality,
            i.rarity,
            lp.price AS current_price,
            lap.max_avg_price
        FROM items i
        JOIN latest_prices lp ON i.id = lp.item_id
        JOIN highest_avg_prices lap ON i.id = lap.item_id
        WHERE
            (i.intent = 'sell' OR i.intent = 'both') -- Considera apenas itens que são para venda
            AND i.notify_sell = 1 -- Considera apenas itens que têm notificação de venda ativada
            AND lp.rn = 1 -- Garante que estamos usando o preço mais recente
            AND lp.price > lap.max_avg_price -- A condição principal da notificação!
    """).fetchall()

    for item in items_to_notify:
        (
            item_id,
            name,
            image_path,
            quality,
            rarity,
            current_price,
            max_avg_price,
        ) = item

        await create_and_broadcast_notification(
            db_conn,
            base_url,
            ItemForNotification(
                id=item_id,
                name=name,
                image_path=image_path,
                quality=quality,
                rarity=rarity,
            ),
            NotificationType.PRICE_ABOVE_BEST_AVG_ALERT,
            current_price,
            abs(current_price - max_avg_price),
        )


async def notify_after_update(db_conn: sqlite3.Connection, base_url: str):
    await notify_price_below(db_conn, base_url)
    await notify_price_above(db_conn, base_url)
    await notify_price_below_best_avg(db_conn, base_url)
    await notify_price_above_best_avg(db_conn, base_url)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await connection_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await websocket.send_text(f"Message received: {data}")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        connection_manager.disconnect(websocket)


@app.post("/notification/{notification_id}/mark-read")
async def mark_notification_as_read(
    notification_id: int, db_conn: sqlite3.Connection = Depends(get_db)
):
    result = db_conn.execute(
        "UPDATE notifications SET read = 1 WHERE id = ?", (notification_id,)
    )
    db_conn.commit()

    if result.rowcount == 0:
        raise HTTPException(
            status_code=404, detail="Notificação não encontrada"
        )

    return {"message": "Notificação marcada como lida"}


@app.get("/notifications")
async def get_latest_notifications(
    request: Request,
    db_conn: sqlite3.Connection = Depends(get_db),
):
    results = db_conn.execute("""
        SELECT notif.id, -- 0 
            notif.type, -- 1
            notif.price_diff, -- 2
            notif.current_price, -- 3
            notif.price_threshold, -- 4
            notif.item_id, -- 5
            notif.read, -- 6
            notif.created_at, -- 7
            i.id, -- 8
            i.name, -- 9
            i.image_path, -- 10
            i.quality, -- 11
            i.rarity -- 12
        FROM notifications notif
        JOIN items i ON notif.item_id = i.id
        WHERE notif.read = 0
        ORDER BY notif.created_at DESC
    """).fetchall()

    return [
        {
            "id": row[0],
            "type": row[1],
            "price_diff": {
                "gold": int(row[2]) // 10000,
                "silver": (int(row[2]) % 10000) // 100,
            },
            "current_price": {
                "gold": int(row[3]) // 10000,
                "silver": (int(row[3]) % 10000) // 100,
            },
            "price_threshold": (
                None
                if row[4] is None
                else {
                    "gold": int(row[4]) // 10000,
                    "silver": (int(row[4]) % 10000) // 100,
                }
            ),
            "item": {
                "id": row[8],
                "name": row[9],
                "image": f"{request.base_url}{row[10]}",
                "quality": row[11],
                "rarity": row[12],
            },
            "read": bool(row[6]),
            "created_at": row[7],
        }
        for row in results
    ]


@app.post("/internal/new-data")
async def trigger_data_update_function(
    request: Request,
    secret: str = Security(API_KEY_HEADER),
    db_conn: sqlite3.Connection = Depends(get_db),
):
    if secret != INTERNAL_WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Acesso não autorizado")

    await notify_after_update(db_conn, str(request.base_url))


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
    WHERE rp.rn = 1 AND i.intent IN ('sell', 'both')
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
        i.intent, -- 5
        i.notify_buy, -- 6
        i.notify_sell, -- 7
        CASE rp.weekday_num
            WHEN '0' THEN 'Domingo'
            WHEN '1' THEN 'Segunda'
            WHEN '2' THEN 'Terça'
            WHEN '3' THEN 'Quarta'
            WHEN '4' THEN 'Quinta'
            WHEN '5' THEN 'Sexta'
            ELSE 'Sábado'
        END AS weekday, -- 8
        rp.hour, -- 9
        rp.avg_price / 10000 AS gold, -- 10
        (rp.avg_price % 10000) / 100 AS silver -- 11
    FROM RankedHistory rp
    JOIN items i ON i.id = rp.item_id
    WHERE rp.rn = 1 AND CAST (rp.weekday_num AS INTEGER) = ? AND i.intent IN ('sell', 'both')
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
                    "price": {"gold": int(item[10]), "silver": int(item[11])},
                    "quality": item[2],
                    "rarity": item[4],
                    "image": f"{request.base_url}{item[3]}",
                    "intent": item[5],
                    "notify_sell": bool(item[7]),
                    "notify_buy": bool(item[6]),
                }
                for item in items
            ],
        }
        for hour, items in itertools.groupby(results, key=lambda x: x[9])
    ]


@app.get("/items")
def get_items(
    request: Request,
    db_conn: sqlite3.Connection = Depends(get_db),
    order_by: str = "id",
    order: str = "desc",
    intent: Intent | None = None,
):
    order_by_map = {
        "id": "i.id",
        "name": "i.name",
        "price": "lp.price",
        "quality": "i.quality",
        "rarity": "i.rarity",
    }

    intent_clause = ""
    if intent == Intent.SELL:
        intent_clause = "AND (i.intent = 'sell')"
    elif intent == Intent.BUY:
        intent_clause = "AND (i.intent = 'buy')"
    elif intent == Intent.BOTH:
        intent_clause = "AND (i.intent IN ('sell', 'buy'))"

    result = db_conn.execute(
        f"""WITH latest_prices AS (
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
                i.id, -- 0
                i.name, -- 1
                i.image_path, -- 2
                i.quality, -- 3
                i.intent, -- 4
                i.notify_sell, -- 5
                i.notify_buy, -- 6
                i.rarity, -- 7
                lp.price, -- 8
                lp.quantity, -- 9
                lp.timestamp -- 10
            FROM
                items AS i
            JOIN
                latest_prices AS lp ON i.id = lp.item_id
            WHERE
                lp.rn = 1
                {intent_clause}
            ORDER BY {order_by_map.get(order_by, "i.id")} {order.upper() if order.lower() in ["asc", "desc"] else "DESC"}
        """,
    ).fetchall()

    return [
        {
            "id": item[0],
            "name": item[1],
            "price": {
                "gold": int(item[8] / 10000),
                "silver": int((item[8] / 10000 - int(item[8] / 10000)) * 100),
            },
            "quality": item[3],
            "image": f"{request.base_url}{item[2]}",
            "rarity": item[7],
            "intent": item[4],
            "notify_sell": bool(item[5]),
            "notify_buy": bool(item[6]),
        }
        for item in result
    ]


@app.post("/items/{item_id}", status_code=201)
async def add_item(
    item_id: int,
    item_optionals: CreateItemOptions,
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

        cached_item = db_conn.execute(
            "SELECT blizzard_image_url, quality FROM item_cache WHERE item_id = ?",
            (item_id,),
        ).fetchone()

        if cached_item:
            img_url = cached_item[0]
            item_quality = cached_item[1]
        else:
            img_response = await fetch_blizzard_api(
                item_response["media"]["key"]["href"],
                client,
            )
            img_url = img_response["assets"][0]["value"]
            item_quality = await get_item_quality(item_id, client)
            db_conn.execute(
                "INSERT INTO item_cache(item_id, blizzard_image_url, quality) VALUES (?, ?, ?)",
                (item_id, img_url, item_quality),
            )
            db_conn.commit()

        img_path = os.path.join("static", "images", img_url.split("/")[-1])
        await download_image(client, img_url, img_path)

        item = {
            "id": item_id,
            "name": item_response["name"],
            "image_path": img_path.replace("\\", "/"),
            "quality": item_quality,
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


@app.get("/items/{item_id}", response_model=ReturnItem)
def get_item(
    item_id: int,
    request: Request,
    db_conn: sqlite3.Connection = Depends(get_db),
):
    item_details = db_conn.execute(
        """SELECT
                i.name, -- 0
                i.image_path, -- 1
                i.quality, -- 2
                i.rarity, -- 3
                i.intent, -- 4
                i.quantity_threshold, -- 5
                i.above_alert, -- 6
                i.below_alert, -- 7
                i.notify_sell, -- 8
                i.notify_buy, -- 9
                ph.price, -- 10
                ph.quantity, -- 11
                ph.timestamp -- 12
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
        intent,
        quantity_threshold,
        above_alert,
        below_alert,
        notify_sell,
        notify_buy,
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

    selling_weekday = buying_weekday = ""
    selling_hour = buying_hour = selling_diff = buying_diff = 0
    selling_best_avg_obj = PriceGoldSilver(gold=0, silver=0)
    buying_best_avg_obj = PriceGoldSilver(gold=0, silver=0)
    selling_diff_obj = PriceGoldSilver(gold=0, silver=0)
    buying_diff_obj = PriceGoldSilver(gold=0, silver=0)

    if intent == "sell" or intent == "both":
        selling_data = db_conn.execute(
            """
            SELECT
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
                item_id = ?

            GROUP BY
                weekday,
                hour

            ORDER BY
                best_avg_price DESC

            LIMIT 1; -- 5. Pega APENAS o primeiro resultado (o melhor) """,
            (item_id,),
        ).fetchone()

        selling_weekday, selling_hour, selling_best_avg_price = selling_data
        selling_diff = price - selling_best_avg_price
        selling_diff_obj = price_to_gold_and_silver(selling_diff)
        selling_best_avg_obj = price_to_gold_and_silver(selling_best_avg_price)

    if intent == "buy" or intent == "both":
        buying_data = db_conn.execute(
            """
            SELECT
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
                item_id = ?

            GROUP BY
                weekday,
                hour

            ORDER BY
                best_avg_price ASC
            LIMIT 1;""",
            (item_id,),
        ).fetchone()
        buying_weekday, buying_hour, buying_best_avg_price = buying_data
        buying_diff = price - buying_best_avg_price
        buying_diff_obj = price_to_gold_and_silver(buying_diff)
        buying_best_avg_obj = price_to_gold_and_silver(buying_best_avg_price)

    price_obj = price_to_gold_and_silver(price)
    above_obj = price_to_gold_and_silver(above_alert)
    below_obj = price_to_gold_and_silver(below_alert)

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
        "id": item_id,
        "name": name,
        "quality": quality,
        "rarity": rarity,
        "image": f"{request.base_url}{image_path}",
        "intent": intent,
        "quantity_threshold": quantity_threshold,
        "notify_sell": bool(notify_sell),
        "notify_buy": bool(notify_buy),
        "above_alert": above_obj,
        "below_alert": below_obj,
        "current_quantity": quantity,
        "current_price": price_obj,
        "average_price_data": plotly_price_heatmap_data,
        "average_quantity_data": plotly_quantity_heatmap_data,
        "last_week_data": {
            "price": line_chart_price_data,
            "quantity": line_chart_quantity_data,
        },
        "last_timestamp": timestamp,
        "selling": {
            "weekday": selling_weekday,
            "hour": selling_hour,
            "price": selling_best_avg_obj,
            "price_diff": {
                "sign": "positive" if selling_diff >= 0 else "negative",
                "gold": abs(selling_diff_obj.gold),
                "silver": abs(selling_diff_obj.silver),
            },
        }
        if intent == "sell" or intent == "both"
        else None,
        "buying": {
            "weekday": buying_weekday,
            "hour": buying_hour,
            "price": buying_best_avg_obj,
            "price_diff": {
                "sign": "positive" if buying_diff >= 0 else "negative",
                "gold": abs(buying_diff_obj.gold),
                "silver": abs(buying_diff_obj.silver),
            },
        }
        if intent == "buy" or intent == "both"
        else None,
    }


@app.put("/items/{item_id}")
def update_item(
    item_id: int,
    item_updates: EditItem,
    db_conn: sqlite3.Connection = Depends(get_db),
):
    cursor = db_conn.execute("SELECT 1 FROM items WHERE id = ?", (item_id,))
    if cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    update_data = item_updates.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400, detail="Nenhum dado para atualizar"
        )

    transformed_data = {}

    for key, value in update_data.items():
        if key in ["above_alert", "below_alert"]:
            transformed_data[key] = gold_and_silver_to_price(value)
        elif key == "intent":
            transformed_data[key] = value.value
        elif key in ["notify_sell", "notify_buy"]:
            transformed_data[key] = int(value)
        else:
            transformed_data[key] = value

    set_clause = ", ".join((f"{key} = ?" for key in transformed_data.keys()))
    sql_query = f"UPDATE items SET {set_clause} WHERE id = ?"

    params = list(transformed_data.values())
    params.append(item_id)

    db_conn.execute(sql_query, tuple(params))
    db_conn.commit()

    return {"message": "Item atualizado com sucesso"}
