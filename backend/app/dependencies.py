import os
import sqlite3

import httpx

from exceptions import EnvNotSetError


def get_db():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise EnvNotSetError("DATABASE_URL")

    conn = sqlite3.connect(database_url, check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()


async def get_http_client():
    async with httpx.AsyncClient() as client:
        yield client
