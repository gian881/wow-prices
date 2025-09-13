import asyncio
from contextlib import asynccontextmanager
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import websocket
from app.background_tasks import run_periodic_data_fetch
from app.startup_tasks import verify_images_on_startup

load_dotenv()

from .routers import internal, items, notifications  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Servidor iniciando: Iniciando a tarefa de busca de dados periódica.")
    asyncio.create_task(run_periodic_data_fetch())
    asyncio.create_task(verify_images_on_startup())
    yield
    print("Servidor desligando.")


app = FastAPI(lifespan=lifespan)
app.include_router(items.router)
app.include_router(notifications.router)
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
app.mount("/static", StaticFiles(directory="./static"), name="static")
