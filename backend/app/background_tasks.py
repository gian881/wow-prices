import asyncio
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import httpx
import pandas as pd
from fastapi import HTTPException
from sqlmodel import Session, desc, select

from app.blizzard_api import fetch_blizzard_api
from app.dependencies import engine
from app.models import Item, PriceHistory


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
    json_result, db_session: Session, current_timestamp: datetime
) -> pd.DataFrame | None:
    log("Processing the new data")
    db_items = db_session.exec(select(Item.id, Item.quantity_threshold)).all()

    threshold_map = {int(item[0]): int(item[1]) for item in db_items}
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

        df["timestamp"] = current_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return df
    else:
        log("No data was persisted after processing.")
        return None


def save_data(processed_data: pd.DataFrame, db_session: Session) -> None:
    log("Saving the new data to the DB")

    processed_data.to_sql(
        "price_history",
        con=db_session.connection(),
        if_exists="append",
        index=False,
    )

    db_session.commit()


async def run_periodic_data_fetch() -> None:
    log("Initializing.")

    client = httpx.AsyncClient(timeout=30)

    FETCH_INTERVAL = timedelta(hours=1)

    sleep_duration = 0

    while True:
        if sleep_duration > 0:
            await asyncio.sleep(sleep_duration)
            sleep_duration = 0
        try:
            with Session(engine) as db_session:
                res = db_session.exec(
                    select(PriceHistory.timestamp)
                    .order_by(desc(PriceHistory.timestamp))
                    .limit(1)
                ).one_or_none()

                last_timestamp_utc = None
                if res:
                    last_timestamp_utc = res.replace(tzinfo=timezone.utc)

                now_utc = datetime.now(timezone.utc)

                if last_timestamp_utc:
                    time_since_last_fetch = now_utc - last_timestamp_utc
                    if time_since_last_fetch < FETCH_INTERVAL:
                        sleep_duration = 1 * 60  # Sleep for 1 minute
                        continue

                # 1 hour or more has passed, or no data found, fetch new data
                log("Fetching new data.")
                data = await get_data(client)
                now_utc = datetime.now(timezone.utc)
                if data:
                    sleep_duration = (
                        FETCH_INTERVAL.total_seconds()
                    )  # Sleep for 1 hour
                    processed_data = await process_data(
                        data, db_session, now_utc
                    )
                    if processed_data is not None:
                        save_data(processed_data, db_session)
                        await notify_server(client)
                    else:
                        log("No processed data to save.")
                else:
                    sleep_duration = 1 * 60  # Sleep for 1 minute
                    log("No data fetched from the API.")
        except Exception as e:
            log(f"An error occurred in the periodic task loop: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(run_periodic_data_fetch())
    except ValueError as e:
        log(f"Error occurred: {e}")
