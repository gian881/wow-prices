import sqlite3

import httpx


def get_db():
    conn = sqlite3.connect("../data/test.db", check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()


async def get_http_client():
    async with httpx.AsyncClient() as client:
        yield client
