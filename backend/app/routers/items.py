import datetime
import itertools
import os

import httpx
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from sqlmodel import Session, text
from unidecode import unidecode

from app.dependencies import get_db, get_http_client
from app.blizzard_api import fetch_blizzard_api
from app.models import Item
from app.schemas import (
    CreateItemOptions,
    EditItem,
    Intent,
    PriceGoldSilver,
    ReturnItem,
    TodayItem,
    TodayResponse,
    WeekResponse,
)
from app.utils import (
    download_image,
    get_item_quality,
    get_plotly_heatmap_data,
    gold_and_silver_to_price,
    price_to_gold_and_silver,
)

router = APIRouter(
    prefix="/items",
    tags=["items"],
)


@router.get("/week", response_model=list[WeekResponse])
def get_week_items(request: Request, db_session: Session = Depends(get_db)):
    results = db_session.execute(
        text("""
    WITH AggregatedHistory AS (    
        SELECT 
            item_id,
            strftime('%w', timestamp, '-3 hours') AS weekday_num,
            CAST(strftime('%H', timestamp, '-3 hours') AS INTEGER) AS hour,
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
    ORDER BY rp.weekday_num, rp.hour""")
    )

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


@router.get("/today", response_model=list[TodayResponse])
def get_today_items(request: Request, db_session: Session = Depends(get_db)):
    today_weekday = (
        datetime.datetime.now().weekday() + 1
    ) % 7  # Deixando weekday igual ao do SQL
    results = db_session.execute(
        text("""
    WITH AggregatedHistory AS (
        SELECT
            item_id,
            strftime('%w', timestamp, '-3 hours') AS weekday_num,
            CAST(strftime('%H', timestamp, '-3 hours') AS INTEGER) AS hour,
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
    WHERE rp.rn = 1 AND CAST (rp.weekday_num AS INTEGER) = :today_weekday AND i.intent IN ('sell', 'both')
    ORDER BY rp.hour
    """),
        {"today_weekday": today_weekday},
    )

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


@router.get("/", response_model=list[TodayItem])
def get_items(
    request: Request,
    db_session: Session = Depends(get_db),
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

    result = db_session.execute(
        text(f"""WITH latest_prices AS (
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
                strftime('%Y-%m-%d %H:%M:%S', lp.timestamp, '-3 hours') -- 10
            FROM
                items AS i
            JOIN
                latest_prices AS lp ON i.id = lp.item_id
            WHERE
                lp.rn = 1
                {intent_clause}
            ORDER BY {order_by_map.get(order_by, "i.id")} {order.upper() if order.lower() in ["asc", "desc"] else "DESC"}
        """),
    )

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


@router.post("/{item_id}", status_code=201)
async def add_item(
    item_id: int,
    item_optionals: CreateItemOptions,
    db_session: Session = Depends(get_db),
    httpx_client: httpx.AsyncClient = Depends(get_http_client),
):
    result = db_session.execute(
        text("SELECT 1 FROM items WHERE id = :item_id"), {"item_id": item_id}
    ).first()
    if result is not None:
        raise HTTPException(status_code=409, detail="Item já adicionado")
    try:
        cached_item = db_session.execute(
            text(
                "SELECT name, blizzard_image_url, quality, rarity FROM item_cache WHERE item_id = :item_id"
            ),
            {"item_id": item_id},
        ).fetchone()

        if cached_item:
            item_name = cached_item[0]
            img_url = cached_item[1]
            item_quality = cached_item[2]
            item_rarity = cached_item[3]

        else:
            item_response = await fetch_blizzard_api(
                f"https://us.api.blizzard.com/data/wow/item/{item_id}",
                httpx_client,
                {"namespace": "static-us", "locale": "pt_BR"},
                "Item",
            )

            item_name = item_response["name"]
            item_rarity = item_response["quality"]["type"]

            img_response = await fetch_blizzard_api(
                item_response["media"]["key"]["href"],
                httpx_client,
            )
            img_url = img_response["assets"][0]["value"]
            item_quality = await get_item_quality(item_id, httpx_client)
            db_session.execute(
                text(
                    "INSERT INTO item_cache(item_id, name, blizzard_image_url, quality, rarity) VALUES (:item_id, :name, :blizzard_image_url, :quality, :rarity)"
                ),
                {
                    "item_id": item_id,
                    "name": item_name,
                    "blizzard_image_url": img_url,
                    "quality": item_quality,
                    "rarity": item_rarity,
                },
            )
            db_session.commit()

        img_path = os.path.join("static", "images", img_url.split("/")[-1])
        await download_image(httpx_client, img_url, img_path)

        item = Item(
            id=item_id,
            name=item_name,
            image_path=img_path.replace("\\", "/"),
            quality=item_quality,
            rarity=item_rarity,
            quantity_threshold=item_optionals.quantity_threshold,
            intent=item_optionals.intent,
            above_alert=gold_and_silver_to_price(item_optionals.above_alert),
            below_alert=gold_and_silver_to_price(item_optionals.below_alert),
            notify_sell=item_optionals.notify_sell,
            notify_buy=item_optionals.notify_buy,
        )

        db_session.execute(
            text(
                """INSERT INTO items(id, name, image_path, quality, rarity, quantity_threshold, intent, above_alert, below_alert, notify_sell, notify_buy)
               VALUES (:id, :name, :image_path, :quality, :rarity, :quantity_threshold, :intent, :above_alert, :below_alert, :notify_sell, :notify_buy)"""
            ),
            {
                "id": item.id,
                "name": item.name,
                "image_path": item.image_path,
                "quality": item.quality,
                "rarity": item.rarity,
                "quantity_threshold": item.quantity_threshold,
                "intent": item.intent,
                "above_alert": item.above_alert,
                "below_alert": item.below_alert,
                "notify_sell": item.notify_sell,
                "notify_buy": item.notify_buy,
            },
        )
        db_session.commit()

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


@router.get("/{item_id}/lookup")
async def get_item_blizzard(
    item_id: int,
    httpx_client: httpx.AsyncClient = Depends(get_http_client),
    db_session: Session = Depends(get_db),
):
    result = db_session.execute(
        text("SELECT 1 FROM items WHERE id = :item_id"), {"item_id": item_id}
    ).fetchone()
    if result is not None:
        raise HTTPException(status_code=409, detail="Item já adicionado")

    cached_item = db_session.execute(
        text("SELECT * FROM item_cache WHERE item_id = :item_id"),
        {"item_id": item_id},
    ).fetchone()

    if cached_item:
        return {
            "id": item_id,
            "name": cached_item[1],
            "image": cached_item[2],
            "quality": cached_item[3],
            "rarity": cached_item[4],
        }

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
        img_url = img_response["assets"][0]["value"]
        item_quality = await get_item_quality(item_id, httpx_client)

        db_session.execute(
            text("""
            INSERT INTO item_cache (item_id, name, blizzard_image_url, quality, rarity)
            VALUES (:item_id, :name, :blizzard_image_url, :quality, :rarity)
            """),
            {
                "item_id": item_id,
                "name": item_response["name"],
                "blizzard_image_url": img_url,
                "quality": item_quality,
                "rarity": item_response["quality"]["type"],
            },
        )
        db_session.commit()

        return {
            "id": item_id,
            "name": item_response["name"],
            "image": img_url,
            "quality": item_quality,
            "rarity": item_response["quality"]["type"],
        }

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Erro ao se comunicar com a API externa: {e}",
        )


@router.get("/{item_id}", response_model=ReturnItem)
def get_item(
    item_id: int,
    request: Request,
    db_session: Session = Depends(get_db),
):
    item_details = db_session.execute(
        text("""SELECT
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
                strftime('%Y-%m-%d %H:%M:%S', ph.timestamp, '-3 hours') -- 12
            FROM
                items AS i
            JOIN
                price_history AS ph ON i.id = ph.item_id
            WHERE
                i.id = :item_id
            ORDER BY
                ph.timestamp DESC
            LIMIT 1;
        """),
        {"item_id": item_id},
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

    price_heatmap_raw_data = db_session.execute(
        text("""
        SELECT
            CASE strftime('%w', timestamp, '-3 hours')
                WHEN '0' THEN 'Domingo'
                WHEN '1' THEN 'Segunda'
                WHEN '2' THEN 'Terça'
                WHEN '3' THEN 'Quarta'
                WHEN '4' THEN 'Quinta'
                WHEN '5' THEN 'Sexta'
                WHEN '6' THEN 'Sábado'
            END AS weekday,
            CAST (strftime('%H', timestamp, '-3 hours') AS INTEGER) AS hour,
            AVG(price) / 10000.0 AS avg_price
        FROM price_history
        WHERE item_id = :item_id
        GROUP BY weekday, hour
        ORDER BY strftime('%w', timestamp, '-3 hours'), hour;"""),
        {"item_id": item_id},
    ).all()

    plotly_price_heatmap_data = get_plotly_heatmap_data(
        price_heatmap_raw_data, "price"
    )

    quantity_heatmap_raw_data = db_session.execute(
        text(
            """
        SELECT
            CASE strftime('%w', timestamp, '-3 hours')
                WHEN '0' THEN 'Domingo'
                WHEN '1' THEN 'Segunda'
                WHEN '2' THEN 'Terça'
                WHEN '3' THEN 'Quarta'
                WHEN '4' THEN 'Quinta'
                WHEN '5' THEN 'Sexta'
                WHEN '6' THEN 'Sábado'
            END AS weekday,
            CAST (strftime('%H', timestamp, '-3 hours') AS INTEGER) AS hour,
            AVG(quantity) AS avg_quantity
        FROM price_history
        WHERE item_id = :item_id
        GROUP BY weekday, hour
        ORDER BY strftime('%w', timestamp, '-3 hours'), hour;""",
        ),
        {"item_id": item_id},
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
        selling_data = db_session.execute(
            text(
                """
            SELECT
                CASE strftime('%w', timestamp, '-3 hours')
                    WHEN '0' THEN 'Domingo'
                    WHEN '1' THEN 'Segunda'
                    WHEN '2' THEN 'Terça'
                    WHEN '3' THEN 'Quarta'
                    WHEN '4' THEN 'Quinta'
                    WHEN '5' THEN 'Sexta'
                    ELSE 'Sábado'
                END AS weekday,
                CAST(strftime('%H', timestamp, '-3 hours') AS INTEGER) AS hour,
                AVG(price) AS best_avg_price
            FROM
                price_history

            WHERE
                item_id = :item_id

            GROUP BY
                weekday,
                hour

            ORDER BY
                best_avg_price DESC

            LIMIT 1; -- 5. Pega APENAS o primeiro resultado (o melhor) """,
            ),
            {"item_id": item_id},
        ).fetchone()
        if not selling_data:
            selling_data = ("", 0, 0)

        selling_weekday, selling_hour, selling_best_avg_price = selling_data
        selling_diff = price - selling_best_avg_price
        selling_diff_obj = price_to_gold_and_silver(selling_diff)
        selling_best_avg_obj = price_to_gold_and_silver(selling_best_avg_price)

    if intent == "buy" or intent == "both":
        buying_data = db_session.execute(
            text("""
            SELECT
                CASE strftime('%w', timestamp, '-3 hours')
                    WHEN '0' THEN 'Domingo'
                    WHEN '1' THEN 'Segunda'
                    WHEN '2' THEN 'Terça'
                    WHEN '3' THEN 'Quarta'
                    WHEN '4' THEN 'Quinta'
                    WHEN '5' THEN 'Sexta'
                    ELSE 'Sábado'
                END AS weekday,
                CAST(strftime('%H', timestamp, '-3 hours') AS INTEGER) AS hour,
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
            LIMIT 1;"""),
            {"item_id": item_id},
        ).fetchone()
        if not buying_data:
            buying_data = ("", 0, 0)
        buying_weekday, buying_hour, buying_best_avg_price = buying_data
        buying_diff = price - buying_best_avg_price
        buying_diff_obj = price_to_gold_and_silver(buying_diff)
        buying_best_avg_obj = price_to_gold_and_silver(buying_best_avg_price)

    price_obj = price_to_gold_and_silver(price)
    above_obj = price_to_gold_and_silver(above_alert)
    below_obj = price_to_gold_and_silver(below_alert)

    now = datetime.datetime.now(datetime.timezone.utc)
    last_week_start = (now - datetime.timedelta(days=7)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    last_week_data = db_session.execute(
        text(f"""
        SELECT
            strftime('%F %T', timestamp, '-3 hours'), -- 0
            price / 10000.0, -- 1
            quantity -- 2
        FROM price_history
        WHERE item_id = :item_id AND timestamp >= '{last_week_start}'
        ORDER BY timestamp DESC
        LIMIT {7 * 24};
        """),
        {"item_id": item_id},
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


@router.put("/{item_id}")
def update_item(
    item_id: int,
    item_updates: EditItem,
    db_session: Session = Depends(get_db),
):
    result = db_session.execute(
        text("SELECT 1 FROM items WHERE id = :item_id"), {"item_id": item_id}
    ).first()
    if result is None:
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

    sql = text(
        f"UPDATE items SET {', '.join(f'{key} = :{key}' for key in transformed_data.keys())} WHERE id = :item_id"
    )

    params = list(transformed_data.values())
    params.append(item_id)

    db_session.execute(sql, {"item_id": item_id, **transformed_data})
    db_session.commit()

    return {"message": "Item atualizado com sucesso"}
