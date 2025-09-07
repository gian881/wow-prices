from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import websocket

load_dotenv()

from .routers import internal, items, notifications  # noqa: E402


app = FastAPI()
app.include_router(items.router)
app.include_router(notifications.router)
app.include_router(internal.router)
app.include_router(websocket.router)

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="./static"), name="static")
