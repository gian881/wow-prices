import os

import httpx
from dotenv import load_dotenv
from sqlmodel import Session, create_engine

from exceptions import EnvNotSetError

load_dotenv()

database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise EnvNotSetError("DATABASE_URL")

engine = create_engine(database_url)


def get_db():
    with Session(engine) as session:
        yield session


async def get_http_client():
    async with httpx.AsyncClient() as client:
        yield client
