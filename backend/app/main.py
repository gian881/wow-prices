import asyncio
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import websocket
from app.background_tasks import run_periodic_data_fetch
from app.logger import get_logger
from app.startup_tasks import verify_images_on_startup

load_dotenv()

logger = get_logger(__name__)

from .routers import internal, items, notifications, settings  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Servidor iniciando: Iniciando a tarefa de busca de dados periódica.")
    asyncio.create_task(run_periodic_data_fetch())
    asyncio.create_task(verify_images_on_startup())
    yield
    logger.info("Servidor desligando.")


app = FastAPI(lifespan=lifespan)
app.include_router(items.router)
app.include_router(notifications.router)
app.include_router(settings.router)
app.include_router(internal.router)
app.include_router(websocket.router)

origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
