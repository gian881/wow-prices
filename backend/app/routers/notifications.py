import sqlite3

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from fastapi.responses import JSONResponse

from app.dependencies import get_db
from app.models import ErrorResponse

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
    notification_ids: list[int], db_conn: sqlite3.Connection = Depends(get_db)
):
    if not notification_ids:
        return {
            "status": "ok",
            "message": "Nenhum ID de notificação fornecido, nenhuma ação foi tomada",
            "unknown_notifications": [],
        }
    try:
        placeholders = ",".join("?" * len(notification_ids))

        result = db_conn.execute(
            f"UPDATE notifications SET read = 1 WHERE id IN ({placeholders})",
            notification_ids,
        )
        db_conn.commit()

        updated_count = result.rowcount

        existing_notifications = db_conn.execute(
            f"SELECT id FROM notifications WHERE id IN ({placeholders})",
            notification_ids,
        ).fetchall()

        existing_ids = {row[0] for row in existing_notifications}

        unknown_ids = [id for id in notification_ids if id not in existing_ids]

        return {
            "status": "ok",
            "message": f"{updated_count} notificações foram marcadas como lidas.",
            "unknown_notifications": unknown_ids,
        }

    except sqlite3.Error as e:
        db_conn.rollback()

        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Erro no banco de dados: {e}",
            },
        )


@router.post("/{notification_id}/mark-read")
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


@router.get("/")
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
