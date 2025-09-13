from datetime import datetime, timezone

from sqlmodel import Session, text

from app.models import Notification, NotificationType
from app.schemas import ItemForNotification
from app.utils import price_to_gold_and_silver

from ..websocket import connection_manager


async def create_and_broadcast_notification(
    db_session: Session,
    base_url: str,
    item: ItemForNotification,
    notification_type: NotificationType,
    current_price: int,
    price_diff: int,
    price_threshold: int | None = None,
):
    now = datetime.now(timezone.utc)

    notification = Notification(
        type=notification_type,
        price_diff=price_diff,
        current_price=current_price,
        price_threshold=price_threshold,
        item_id=item.id,
        created_at=now,
    )

    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)

    notification_id = notification.id

    if notification_id is None:
        print("Erro ao obter o ID da notificação inserida.")
        return

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
            "price_diff": price_diff_obj.model_dump(),
            "current_price": current_price_obj.model_dump(),
            "price_threshold": (
                price_threshold_obj.model_dump()
                if price_threshold_obj is not None
                else None
            ),
            "item": {
                "id": item.id,
                "name": item.name,
                "image": f"{base_url}{item.image_path}",
                "quality": item.quality,
                "rarity": item.rarity,
            },
            "read": False,
            "created_at": now.isoformat(),
        },
    }

    await connection_manager.broadcast(message)


async def notify_price_below(db_session: Session, base_url: str):
    items_to_notify = db_session.execute(
        text("""
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
    """)
    ).fetchall()

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
            db_session,
            base_url,
            ItemForNotification(
                id=item_id,
                name=name,
                image_path=image_path,
                quality=quality,
                rarity=rarity,
            ),
            NotificationType.price_below_alert,
            current_price,
            abs(current_price - price_threshold),
            price_threshold,
        )


async def notify_price_above(db_session: Session, base_url: str):
    items_to_notify = db_session.execute(
        text("""
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
    """)
    ).fetchall()

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
            db_session,
            base_url,
            ItemForNotification(
                id=item_id,
                name=name,
                image_path=image_path,
                quality=quality,
                rarity=rarity,
            ),
            NotificationType.price_above_alert,
            current_price,
            abs(current_price - price_threshold),
            price_threshold,
        )


async def notify_price_below_best_avg(db_session: Session, base_url: str):
    items_to_notify = db_session.execute(
        text("""
        WITH latest_prices AS (
            SELECT
                item_id,
                price,
                ROW_NUMBER() OVER(PARTITION BY item_id ORDER BY "timestamp" DESC) AS rn
            FROM
                price_history
        ),
        lowest_avg_prices AS (
            SELECT
                item_id,
                MIN(avg_price) as min_avg_price
            FROM
                (
                    SELECT
                        item_id,
                        AVG(price) as avg_price
                    FROM
                        price_history
                    GROUP BY
                        item_id,
                        EXTRACT(DOW FROM "timestamp" AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo'),
                        EXTRACT(HOUR FROM "timestamp" AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo')
                ) AS daily_averages
            GROUP BY
                item_id
        )
        SELECT
            i.id,
            i.name,
            i.image_path,
            i.quality,
            i.rarity,
            lp.price AS current_price,
            lap.min_avg_price
        FROM
            items i
        JOIN latest_prices lp ON i.id = lp.item_id
        JOIN lowest_avg_prices lap ON i.id = lap.item_id
        WHERE
            (i.intent = 'buy' OR i.intent = 'both')
            AND i.notify_buy = TRUE
            AND lp.rn = 1
            AND lp.price < lap.min_avg_price;
    """)
    ).fetchall()

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
            db_session,
            base_url,
            ItemForNotification(
                id=item_id,
                name=name,
                image_path=image_path,
                quality=quality,
                rarity=rarity,
            ),
            NotificationType.price_below_best_avg_alert,
            current_price,
            abs(current_price - min_avg_price),
        )


async def notify_price_above_best_avg(db_session: Session, base_url: str):
    items_to_notify = db_session.execute(
        text("""
        WITH latest_prices AS (
            SELECT
                item_id,
                price,
                ROW_NUMBER() OVER(PARTITION BY item_id ORDER BY "timestamp" DESC) AS rn
            FROM
                price_history
        ),
        highest_avg_prices AS (
            SELECT
                item_id,
                MAX(avg_price) as max_avg_price
            FROM
                (
                    SELECT
                        item_id,
                        AVG(price) as avg_price
                    FROM
                        price_history
                    GROUP BY
                        item_id,
                        EXTRACT(DOW FROM "timestamp" AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo'),
                        EXTRACT(HOUR FROM "timestamp" AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo')
                ) AS daily_averages
            GROUP BY
                item_id
        )
        SELECT
            i.id,
            i.name,
            i.image_path,
            i.quality,
            i.rarity,
            lp.price AS current_price,
            lap.max_avg_price
        FROM
            items i
        JOIN latest_prices lp ON i.id = lp.item_id
        JOIN highest_avg_prices lap ON i.id = lap.item_id
        WHERE
            (i.intent = 'sell' OR i.intent = 'both')
            AND i.notify_sell = TRUE
            AND lp.rn = 1
            AND lp.price > lap.max_avg_price;
    """)
    ).fetchall()

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
            db_session,
            base_url,
            ItemForNotification(
                id=item_id,
                name=name,
                image_path=image_path,
                quality=quality,
                rarity=rarity,
            ),
            NotificationType.price_above_best_avg_alert,
            current_price,
            abs(current_price - max_avg_price),
        )


async def notify_after_update(db_session: Session, base_url: str):
    await connection_manager.broadcast(
        {
            "action": "new_data",
            "data": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }
    )
    await notify_price_below(db_session, base_url)
    await notify_price_above(db_session, base_url)
    await notify_price_below_best_avg(db_session, base_url)
    await notify_price_above_best_avg(db_session, base_url)
