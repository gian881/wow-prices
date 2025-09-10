import datetime

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from fastapi.responses import JSONResponse
from sqlmodel import Session, text

from app.dependencies import get_db
from app.schemas import ErrorResponse

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
        # Update where id in list
        placeholders = ",".join(
            [f":id{i}" for i in range(len(notification_ids))]
        )
        params = {
            f"id{i}": notification_ids[i] for i in range(len(notification_ids))
        }

        db_session.execute(
            text(
                f"UPDATE notifications SET read = 1 WHERE id IN ({placeholders})"
            ),
            params,
        )

        db_session.commit()

        # row_count = result.rowcount

        # updated_count = result.

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
    # Does the notification exists?
    existing_notification = db_session.execute(
        text("SELECT id FROM notifications WHERE id = :notification_id"),
        {"notification_id": notification_id},
    ).fetchone()

    if not existing_notification:
        raise HTTPException(
            status_code=404, detail="Notificação não encontrada"
        )

    db_session.execute(
        text("UPDATE notifications SET read = 1 WHERE id = :notification_id"),
        {"notification_id": notification_id},
    )
    db_session.commit()

    return {"message": "Notificação marcada como lida"}


@router.get("/")
async def get_latest_notifications(
    request: Request,
    db_session: Session = Depends(get_db),
):
    results = db_session.execute(
        text("""
        SELECT notif.id, -- 0
            notif.type, -- 1
            notif.price_diff, -- 2
            notif.current_price, -- 3
            notif.price_threshold, -- 4
            notif.item_id, -- 5
            notif.read, -- 6
            strftime("%Y-%m-%d %H:%M:%S", notif.created_at), -- 7
            i.id, -- 8
            i.name, -- 9
            i.image_path, -- 10
            i.quality, -- 11
            i.rarity -- 12
        FROM notifications notif
        JOIN items i ON notif.item_id = i.id
        WHERE notif.read = 0
        ORDER BY notif.created_at DESC
    """)
    ).fetchall()

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
            "created_at": datetime.datetime.strptime(
                row[7], "%Y-%m-%d %H:%M:%S"
            )
            .replace(tzinfo=datetime.timezone.utc)
            .isoformat(),
        }
        for row in results
    ]
