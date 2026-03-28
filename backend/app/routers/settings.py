from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlmodel import Session, select

from app.dependencies import get_db
from app.models import Settings
from app.schemas import UpdateSettings

router = APIRouter(
    prefix="/settings",
    tags=["settings"],
)


@router.get("/")
def get_settings(
    setting_keys: list[str] | None = None, db_session: Session = Depends(get_db)
):
    if setting_keys:
        settings = db_session.exec(
            select(Settings).where(Settings.key in setting_keys)
        ).all()
    else:
        settings = db_session.exec(select(Settings)).all()
    return settings


@router.get("/{setting_key}", response_model=Settings)
def get_setting(setting_key: str, db_session: Session = Depends(get_db)):
    setting = db_session.exec(
        select(Settings).where(Settings.key == setting_key)
    ).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Configuração não encontrada")
    return setting


@router.put("/{setting_key}")
def update_setting(setting_key: str, value: str, db_session: Session = Depends(get_db)):
    setting = db_session.exec(
        select(Settings).where(Settings.key == setting_key)
    ).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Configuração não encontrada")
    setting.value = value
    db_session.add(setting)
    db_session.commit()
    db_session.refresh(setting)
    return setting


@router.put("/")
def update_settings(
    update_settings: list[UpdateSettings], db_session: Session = Depends(get_db)
):
    settings = db_session.exec(
        select(Settings).where(Settings.key in map(lambda s: s.key, update_settings))
    ).all()

    if not settings:
        raise HTTPException(status_code=404, detail="Configurações não encontradas")

    for setting in settings:
        update = next((s for s in update_settings if s.key == setting.key), None)
        if update:
            setting.value = update.value
            db_session.add(setting)
            db_session.commit()
            db_session.refresh(setting)
    return settings
