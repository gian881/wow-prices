from datetime import datetime
import time
import pandas as pd
import requests

from db import DB
from utils import generate_new_token, get_auth_token


def log(message: str) -> None:
    now = datetime.now()
    print(f"{now.strftime('[%d/%m/%Y] [%H:%M:%S]')} {message}")


def get_data():
    log("Getting new data.")
    res = requests.get(
        "https://us.api.blizzard.com/data/wow/auctions/commodities?namespace=dynamic-us&locale=en_US",
        headers={"Authorization": f"Bearer {get_auth_token()}"},
    )

    if res.status_code == 401:
        log("Token expired, generating new token.")
        generate_new_token()
        return get_data()

    if res.ok:
        result = res.json()
        return result
    raise Exception("Não foi possível fazer o request.")


def process_data(json_result, db: DB):
    log("Processing the new data")
    items_ids = (
        item[0] for item in db.con.execute("SELECT id FROM items").fetchall()
    )
    # items_ids = [
    #     213613,
    #     213612,
    #     213611,
    #     213197,
    #     210810,
    #     210809,
    #     210808,
    #     210807,
    #     210806,
    #     210805,
    #     210804,
    #     210803,
    #     210802,
    #     210801,
    #     210800,
    #     210799,
    #     210798,
    #     210797,
    #     210796,
    #     210939,
    #     210938,
    #     210937,
    #     210936,
    #     210935,
    #     210934,
    #     210933,
    #     210932,
    #     210931,
    #     210930,
    #     224828,
    # ]
    df = (
        pd.json_normalize(json_result["auctions"])
        .query("`item.id` in @items_ids")
        .rename(columns={"item.id": "item_id", "unit_price": "price"})
    )

    df.drop(columns=["id", "time_left"], inplace=True)

    df = df[["item_id", "quantity", "price"]]

    df = df.groupby(["item_id", "price"])["quantity"].sum().reset_index()

    df = df[df["quantity"] >= 100]

    df = df.groupby("item_id")["price"].min().reset_index()

    df["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    log("Saving the new data to the DB")
    df.to_sql("price_history", con=db.con, if_exists="append", index=False)


def main() -> None:
    log("Initializing.")
    db = DB()
    while True:
        res = db.con.execute(
            """SELECT timestamp FROM price_history ORDER BY timestamp DESC LIMIT 1"""
        )

        last_timestamp = datetime.strptime(
            f"{res.fetchone()[0]}000", "%Y-%m-%d %H:%M:%S.%f"
        )

        time_diff = datetime.now() - last_timestamp
        if time_diff.total_seconds() > 3600:
            log("It's been more than one hour, getting new data.")
            data = get_data()
            process_data(data, db)
            time.sleep(60 * 60)  # 60 minutos * 60 segundos
        else:
            time.sleep(1 * 60)  # 1 minuto * 60 segundos


if __name__ == "__main__":
    main()
