import asyncio
import gc
import os
from datetime import datetime, timedelta, timezone

import httpx
import pandas as pd
from fastapi import HTTPException
from sqlmodel import Session, desc, select

from app.blizzard_api import fetch_blizzard_api
from app.dependencies import engine
from app.logger import get_logger
from app.models import Item, PriceHistory

logger = get_logger(__name__)


async def get_data(httpx_client: httpx.AsyncClient):
    logger.info("Getting new data.")

    try:
        logger.info("Fetching data from Blizzard API.")
        data = await fetch_blizzard_api(
            "https://us.api.blizzard.com/data/wow/auctions/commodities",
            httpx_client,
            params={"namespace": "dynamic-us", "locale": "pt_BR"},
        )

        return data
    except HTTPException as e:
        logger.error(f"Erro ao carregar dados da blizzard: {e}", exc_info=True)


async def notify_server(httpx_client: httpx.AsyncClient) -> None:
    logger.info("Notifying the server about new data.")

    webhook_secret = os.getenv("INTERNAL_WEBHOOK_SECRET")
    if not webhook_secret:
        logger.warning("No webhook secret provided, skipping server notification.")
        return
    base_url = os.getenv("SELF_BASE_URL")
    if not base_url:
        logger.warning("No base URL provided, skipping server notification.")
        return

    try:
        response = await httpx_client.post(
            f"{base_url}/internal/new-data",
            headers={"X-Internal-Secret": webhook_secret},
        )
        if response.status_code == 200:
            logger.info("Server notified successfully.")

        response.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to notify server: {e}", exc_info=True)


async def process_data(
    json_result, db_session: Session, current_timestamp: datetime
) -> pd.DataFrame | None:
    logger.info("Processing the new data")
    db_items = db_session.exec(
        select(Item.id, Item.quantity_threshold).where(Item.is_active)
    ).all()

    logger.info(f"Found {len(db_items)} active items in the database for processing.")

    threshold_map = {int(item[0]): int(item[1]) for item in db_items}
    items_ids = set(threshold_map.keys())

    logger.info("Filtering all the data for active items")

    df = (
        pd.json_normalize(json_result["auctions"])
        .query("`item.id` in @items_ids")
        .rename(columns={"item.id": "item_id", "unit_price": "price"})
    )

    df = df[["item_id", "quantity", "price"]]

    logger.info('Grouping data by "item_id" and "price" and summing quantities.')

    df = df.groupby(["item_id", "price"])["quantity"].sum().reset_index()

    logger.info("Filtering by threshold quantity for each item.")

    df = df[
        df.apply(lambda row: row["quantity"] >= threshold_map[row["item_id"]], axis=1)
    ]

    if not df.empty:
        logger.info(
            "Dataframe is not empty, proceeding with final grouping and timestamp addition."
        )
        df = (
            df.groupby("item_id")
            .agg(price=("price", "min"), quantity=("quantity", "sum"))
            .reset_index()
        )

        df["timestamp"] = current_timestamp.strftime("%Y-%m-%d %H:%M:%S")

        logger.info("Returning the processed data")
        return df
    else:
        logger.info("No data was persisted after processing.")
        return None


def save_data(processed_data: pd.DataFrame, db_session: Session) -> None:
    logger.info("Saving the new data to the DB")

    processed_data.to_sql(
        "price_history",
        con=db_session.connection(),
        if_exists="append",
        index=False,
    )

    logger.info("Data saved to the database, committing the transaction.")

    db_session.commit()


async def run_periodic_data_fetch() -> None:
    logger.info("Initializing periodic data fetch.")

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

                last_timestamp_utc = res.replace(tzinfo=timezone.utc) if res else None

                now_utc = datetime.now(timezone.utc)

                if last_timestamp_utc:
                    time_since_last_fetch = now_utc - last_timestamp_utc
                    if time_since_last_fetch < FETCH_INTERVAL:
                        sleep_duration = 1 * 60  # Sleep for 1 minute
                        continue

                # 1 hour or more has passed, or no data found, fetch new data
                logger.info("Fetching new data.")
                async with httpx.AsyncClient(timeout=30) as client:
                    data = await get_data(client)
                    now_utc = datetime.now(timezone.utc)
                    if data:
                        sleep_duration = (
                            FETCH_INTERVAL.total_seconds()
                        )  # Sleep for 1 hour
                        processed_data = await process_data(data, db_session, now_utc)
                        if processed_data is not None:
                            save_data(processed_data, db_session)
                            await notify_server(client)
                        else:
                            logger.info("No processed data to save.")
                    else:
                        sleep_duration = 1 * 60  # Sleep for 1 minute
                        logger.warning("No data fetched from the API.")

                del data
                gc.collect()
        except Exception as e:
            logger.error(
                f"An error occurred in the periodic task loop: {e}", exc_info=True
            )


if __name__ == "__main__":
    try:
        asyncio.run(run_periodic_data_fetch())
    except ValueError as e:
        logger.error(f"Error occurred: {e}", exc_info=True)
