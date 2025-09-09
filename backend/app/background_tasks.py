import asyncio
import os
import sqlite3
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import httpx
import pandas as pd
from dotenv import load_dotenv
from exceptions import EnvNotSetError
from fastapi import HTTPException

from app.blizzard_api import fetch_blizzard_api

load_dotenv()


def log(message: str) -> None:
    now = datetime.now(ZoneInfo("America/Sao_Paulo"))
    print(f"{now.strftime('[%d/%m/%Y] [%H:%M:%S]')} {message}")


async def get_data(httpx_client: httpx.AsyncClient):
    log("Getting new data.")

    try:
        data = await fetch_blizzard_api(
            "https://us.api.blizzard.com/data/wow/auctions/commodities",
            httpx_client,
            params={"namespace": "dynamic-us", "locale": "pt_BR"},
        )

        return data
    except HTTPException as e:
        print("Erro ao carregar dados da blizzard")
        print(e)


async def notify_server(httpx_client: httpx.AsyncClient) -> None:
    log("Notifying the server about new data.")

    webhook_secret = os.getenv("INTERNAL_WEBHOOK_SECRET")
    if not webhook_secret:
        log("No webhook secret provided, skipping server notification.")
        return

    try:
        response = await httpx_client.post(
            "http://localhost:8000/internal/new-data",
            headers={"X-Internal-Secret": webhook_secret},
        )
        if response.status_code == 200:
            log("Server notified successfully.")

        response.raise_for_status()
    except Exception as e:
        log(f"Failed to notify server: {e}")


async def process_data(
    json_result, db_conn: sqlite3.Connection, httpx_client: httpx.AsyncClient
) -> None:
    log("Processing the new data")
    db_result = db_conn.execute(
        "SELECT id, quantity_threshold FROM items"
    ).fetchall()

    threshold_map = {item_id: threshold for item_id, threshold in db_result}
    items_ids = set(threshold_map.keys())

    df = (
        pd.json_normalize(json_result["auctions"])
        .query("`item.id` in @items_ids")
        .rename(columns={"item.id": "item_id", "unit_price": "price"})
    )

    df = df[["item_id", "quantity", "price"]]

    df = df.groupby(["item_id", "price"])["quantity"].sum().reset_index()

    df = df[
        df.apply(
            lambda row: row["quantity"] >= threshold_map[row["item_id"]], axis=1
        )
    ]

    if not df.empty:
        df = (
            df.groupby("item_id")
            .agg(price=("price", "min"), quantity=("quantity", "sum"))
            .reset_index()
        )

        df["timestamp"] = datetime.now(timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )[:-3]

        log("Saving the new data to the DB")
        df.to_sql("price_history", con=db_conn, if_exists="append", index=False)
        try:
            await notify_server(httpx_client)
        except Exception as e:
            log(f"Failed to notify server: {e}")
    else:
        log("No data to save after filtering.")


async def run_periodic_data_fetch() -> None:
    log("Initializing.")

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise EnvNotSetError("DATABASE_URL")
    db_conn = sqlite3.connect(database_url)
    client = httpx.AsyncClient(timeout=30)

    while True:
        try:
            res = db_conn.execute(
                "SELECT timestamp FROM price_history ORDER BY timestamp DESC LIMIT 1"
            )
            last_timestamp_str = res.fetchone()[0]
            if last_timestamp_str:
                naive_last_timestamp = datetime.strptime(
                    f"{last_timestamp_str}", "%Y-%m-%d %H:%M:%S"
                )

                last_timestamp = naive_last_timestamp.replace(
                    tzinfo=timezone.utc
                )

                time_diff = datetime.now(timezone.utc) - last_timestamp

                if (
                    time_diff.total_seconds() >= 60 * 60 - 1
                ):  # 60 minutos * 60 segundos - 1 segundo
                    log("It's been more than one hour, getting new data.")
                    data = await get_data(client)
                    if data:
                        await process_data(data, db_conn, client)
                    await asyncio.sleep(60 * 60)  # Espera 1 hora
                else:
                    await asyncio.sleep(1 * 60)  # Espera 1 minuto
            else:
                log("No data in price_history, fetching initial data.")
                data = await get_data(client)
                if data:
                    await process_data(data, db_conn, client)
                await asyncio.sleep(
                    60 * 60
                )  # Espera 1 hora após a busca inicial
        except Exception as e:
            log(f"An error occurred in the periodic task loop: {e}")
            await asyncio.sleep(
                2 * 60
            )  # Espera 2 minutos antes de tentar novamente


if __name__ == "__main__":
    try:
        asyncio.run(run_periodic_data_fetch())
    except ValueError as e:
        log(f"Error occurred: {e}")
