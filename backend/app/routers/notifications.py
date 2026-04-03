import datetime
import string

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from fastapi.responses import JSONResponse
from sqlmodel import Session, and_, col, desc, func, not_, select, text

from app.dependencies import get_db
from app.models import Item, Notification
from app.schemas import ErrorResponse
from app.utils import price_to_gold_and_silver

router = APIRouter(
    prefix="/notifications",
    tags=["notifications"],
)


@router.post(
    "/mark-all-read",
    status_code=status.HTTP_200_OK,
    responses={500: {"model": ErrorResponse}},
)
async def mark_all_notifications_as_read(db_session: Session = Depends(get_db)):
    """Marca todas as notificações como lidas."""
    try:
        result = db_session.execute(
            text("UPDATE notifications SET read = true WHERE read = false;")
        )

        db_session.commit()

        return {
            "message": f"{result.rowcount} notificações foram marcadas como lidas.",  # type: ignore
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "message": str(e),
            },
        )


@router.post("/{notification_id}/mark-read")
async def mark_notification_as_read(
    notification_id: int, db_session: Session = Depends(get_db)
):
    existing_notification = db_session.exec(
        select(Notification).where(Notification.id == notification_id)
    ).first()

    if not existing_notification:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")
    if existing_notification.read:
        return {"message": "Notificação já está marcada como lida"}

    existing_notification.read = True
    db_session.add(existing_notification)
    db_session.commit()

    return {
        "notification": existing_notification.model_dump_json(),
        "message": "Notificação marcada como lida",
    }


@router.get("/")
async def get_notifications(
    limit: int = 10,
    page: int = 1,
    ignore_read: bool = False,
    db_session: Session = Depends(get_db),
):
    page = max(page, 1)
    limit = max(limit, 10)

    if ignore_read:
        notifications = db_session.exec(
            select(Notification, Item)
            .where(and_(not_(Notification.read), Notification.item_id == Item.id))
            .offset((page - 1) * limit)
            .limit(limit)
            .order_by(desc(Notification.created_at))
        ).fetchall()
        total = db_session.exec(
            select(func.count(col(Notification.id))).where(not_(Notification.read))
        ).one()
    else:
        notifications = db_session.exec(
            select(Notification, Item)
            .where(Notification.item_id == Item.id)
            .offset((page - 1) * limit)
            .limit(limit)
            .order_by(desc(Notification.created_at))
        ).fetchall()
        total = db_session.exec(select(func.count(col(Notification.id)))).one()

    total_unread = db_session.exec(
        select(func.count(col(Notification.id))).where(not_(Notification.read))
    ).one()

    return {
        "meta": {
            "next_page": page + 1 if (page * limit) < total else None,
            "total_unread": total_unread,
            "total": total,
        },
        "data": [
            {
                "id": notification.id,
                "type": notification.type,
                "price_diff": price_to_gold_and_silver(notification.price_diff),
                "current_price": price_to_gold_and_silver(notification.current_price),
                "price_threshold": (
                    None
                    if notification.price_threshold is None
                    else price_to_gold_and_silver(notification.price_threshold)
                ),
                "item": {
                    "id": item.id,
                    "name": item.name,
                    "image": item.image_path,
                    "quality": item.quality,
                    "rarity": item.rarity,
                },
                "read": notification.read,
                "created_at": notification.created_at.replace(
                    tzinfo=datetime.timezone.utc
                ).isoformat(),
            }
            for notification, item in notifications
        ],
    }
