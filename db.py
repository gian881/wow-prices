import sqlite3

# cur.execute(
#     "CREATE TABLE IF NOT EXISTS items(id NUMERIC PRIMARY KEY, name TEXT, image_path TEXT, quality NUMERIC)"
# )
# cur.execute(
#     """
#     CREATE TABLE IF NOT EXISTS price_history(
#     item_id NUMERIC,
#     price NUMERIC,
#     timestamp TEXT DEFAULT current_timestamp,
#     FOREIGN KEY(item_id) REFERENCES items(id),
#     PRIMARY KEY (item_id,timestamp)
#     )
#     """
# )


class DB:
    def __init__(self) -> None:
        self.con = sqlite3.connect("test.db")

    def insert_into_item(
        self, id: int, name: str, image_path: str, quality: int | None = None
    ):
        if not quality:
            quality = 0
        with self.con:
            self.con.execute(
                "INSERT INTO items(id, name, image_path, quality) VALUES (?, ?, ?, ?)",
                (id, name, image_path, quality),
            )
