import datetime

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from fastapi.responses import JSONResponse
from sqlmodel import Session, and_, desc, select, text

from app.dependencies import get_db
from app.models import Item, Notification
from app.schemas import ErrorResponse
from app.utils import price_to_gold_and_silver

router = APIRouter(
    prefix="/notifications",
    tags=["notifications"],
)


@router.post(
    "/mark-read",
    status_code=status.HTTP_200_OK,
    responses={500: {"model": ErrorResponse}},
)
async def mark_notifications_as_read(
    notification_ids: list[int], db_session: Session = Depends(get_db)
):
    if not notification_ids:
        return {
            "status": "ok",
            "message": "Nenhum ID de notificação fornecido, nenhuma ação foi tomada",
            "unknown_notifications": [],
        }
    try:
        placeholders = ",".join(
            [f":id{i}" for i in range(len(notification_ids))]
        )
        params = {
            f"id{i}": notification_ids[i] for i in range(len(notification_ids))
        }

        db_session.execute(
            text(
                f"UPDATE notifications SET read = TRUE WHERE id IN ({placeholders})"
            ),
            params,
        )

        db_session.commit()

        existing_notifications = db_session.execute(
            text(
                f"SELECT id FROM notifications WHERE id IN ({placeholders})",
            ),
            params,
        ).fetchall()

        existing_ids = {row[0] for row in existing_notifications}

        unknown_ids = [id for id in notification_ids if id not in existing_ids]

        return {
            "status": "ok",
            # "message": f"{updated_count} notificações foram marcadas como lidas.",
            "unknown_notifications": unknown_ids,
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Erro: {e}",
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
        raise HTTPException(
            status_code=404, detail="Notificação não encontrada"
        )
    if existing_notification.read:
        return {"message": "Notificação já está marcada como lida"}

    existing_notification.read = True
    db_session.add(existing_notification)
    db_session.commit()

    return {"message": "Notificação marcada como lida"}


@router.get("/")
async def get_latest_notifications(
    db_session: Session = Depends(get_db),
):
    results = db_session.exec(
        select(Notification, Item)
        .where(
            and_(Notification.read == False, Notification.item_id == Item.id)  # noqa: E712
        )
        .order_by(desc(Notification.created_at))
    ).fetchall()

    return [
        {
            "id": notification.id,
            "type": notification.type,
            "price_diff": price_to_gold_and_silver(notification.price_diff),
            "current_price": price_to_gold_and_silver(
                notification.current_price
            ),
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
        for notification, item in results
    ]
