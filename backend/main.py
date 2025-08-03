import asyncio
import sqlite3
import time
from datetime import datetime

from fastapi import HTTPException
import httpx
import pandas as pd

from blizzard_api import fetch_blizzard_api


def log(message: str) -> None:
    now = datetime.now()
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


def process_data(json_result, db_conn: sqlite3.Connection):
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

        df["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        log("Saving the new data to the DB")
        df.to_sql("price_history", con=db_conn, if_exists="append", index=False)
    else:
        log("No data to save after filtering.")


async def main() -> None:
    log("Initializing.")
    db_conn = sqlite3.connect("./data/test.db")
    client = httpx.AsyncClient()

    while True:
        res = db_conn.execute(
            "SELECT timestamp FROM price_history ORDER BY timestamp DESC LIMIT 1"
        )

        last_timestamp = datetime.strptime(
            f"{res.fetchone()[0]}000", "%Y-%m-%d %H:%M:%S.%f"
        )

        time_diff = datetime.now() - last_timestamp
        if time_diff.total_seconds() > 3600:
            log("It's been more than one hour, getting new data.")
            data = await get_data(client)
            process_data(data, db_conn)
            time.sleep(60 * 60)  # 60 minutos * 60 segundos
        else:
            time.sleep(1 * 60)  # 1 minuto * 60 segundos


if __name__ == "__main__":
    asyncio.run(main())
