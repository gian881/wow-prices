import os
import sqlite3

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Security,
)
from fastapi.security import APIKeyHeader

from app.dependencies import get_db
from app.services.notification_services import notify_after_update
from exceptions import EnvNotSetError

INTERNAL_WEBHOOK_SECRET = os.getenv("INTERNAL_WEBHOOK_SECRET")

if not INTERNAL_WEBHOOK_SECRET:
    raise EnvNotSetError("INTERNAL_WEBHOOK_SECRET")


API_KEY_HEADER = APIKeyHeader(name="X-Internal-Secret")

router = APIRouter(
    prefix="/internal",
    tags=["internal"],
)


@router.post("/new-data")
async def trigger_data_update_function(
    request: Request,
    secret: str = Security(API_KEY_HEADER),
    db_conn: sqlite3.Connection = Depends(get_db),
):
    if secret != INTERNAL_WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Acesso não autorizado")

    await notify_after_update(db_conn, str(request.base_url))
