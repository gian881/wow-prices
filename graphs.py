import pandas as pd
from db import DB
import seaborn as sns
import matplotlib.pyplot as plt


def weekday(index: str) -> str:
    if index == "0":
        return "Domingo"
    if index == "1":
        return "Segunda"
    if index == "2":
        return "Terça"
    if index == "3":
        return "Quarta"
    if index == "4":
        return "Quinta"
    if index == "5":
        return "Sexta"
    if index == "6":
        return "Sábado"
    return "Domingo"


def show_graph(db: DB, item_id: str, item_name: str) -> None:
    result = db.con.execute(
        "SELECT strftime('%w', timestamp), strftime('%H', timestamp), price FROM price_history WHERE item_id = ?",
        (item_id,),
    ).fetchall()

    result = (
        (weekday(item[0]), int(item[1]), item[2] / 10000) for item in result
    )

    df = pd.DataFrame(result)

    df.columns = ["weekday", "hour", "price"]

    weekday_order = [
        "Domingo",
        "Segunda",
        "Terça",
        "Quarta",
        "Quinta",
        "Sexta",
        "Sábado",
    ]
    df["weekday"] = pd.Categorical(
        df["weekday"], categories=weekday_order, ordered=True
    )

    df = df.groupby(["weekday", "hour"], observed=False)["price"].mean()

    # Pivot the DataFrame to create the matrix for the heatmap.
    # - index='hour': sets the hours as the rows (y-axis).
    # - columns='weekday': sets the weekdays as the columns (x-axis).
    # - values='price': fills the cells with the price.
    heatmap_data = df.unstack(level="weekday")

    # 3. Generate the Heatmap
    plt.figure(figsize=(10, 12))  # Set the figure size for better readability
    # plt.figure(figsize=(6, 14))  # Set the figure size for better readability
    sns.heatmap(
        heatmap_data,
        annot=True,  # Show the price values in the cells
        fmt=".2f",  # Format the numbers as integers
        cmap="RdYlGn",  # Red-Yellow-Green reversed colormap
        linewidths=0.5,  # Add lines between cells
    )

    # Add titles and labels for clarity
    plt.title(f"Preço pelo dia da semana e hora {item_name}", fontsize=16)
    plt.xlabel("Dia da semana", fontsize=12)
    plt.ylabel("Hora do dia", fontsize=12)

    # Display the plot
    plt.show()


def get_best_weekday_and_hour(db: DB, item_id: int) -> tuple[str, int, float]:
    return db.con.execute(
        """SELECT CASE strftime('%w', timestamp)
                WHEN '0' THEN 'Domingo'
                WHEN '1' THEN 'Segunda'
                WHEN '2' THEN 'Terça'
                WHEN '3' THEN 'Quarta'
                WHEN '4' THEN 'Quinta'
                WHEN '5' THEN 'Sexta'
                WHEN '6' THEN 'Sábado'
            END AS weekday,
            CAST(strftime('%H', timestamp) AS INTEGER) AS hour,
            AVG(price / 10000.0) AS avg_price
        FROM price_history
        WHERE item_id = ?
        GROUP BY weekday,
                hour
        ORDER BY avg_price DESC
        LIMIT 1;""",
        (item_id,),
    ).fetchall()[0]


def graph_module(db: DB):
    while True:
        print("ITEMS")
        for item in items:
            print(
                f"{item[0]} - {item[1]}{f' ({item[2]})' if item[2] > 0 else ''}"
            )
        print()
        item_id = input("Digite o ID do item selecionado (0 para sair): ")
        if item_id == "0":
            print("Saindo...")
            break
        try:
            item = next(filter(lambda x: str(x[0]) == item_id, items))
        except StopIteration:
            print("Item incorreto!\n")
            continue
        show_graph(
            db, item_id, f"{item[1]}{f' [{item[2]}]' if item[2] > 0 else ''}"
        )


def best_day_hour_module(db: DB, items: list[tuple[int, str, int]]):
    result = (
        (
            f"{item[1]}{f' [{item[2]}]' if item[2] > 0 else ''}",
            *get_best_weekday_and_hour(db, item[0]),
        )
        for item in items
    )
    df = pd.DataFrame(result)
    df.columns = ["name", "weekday", "hour", "price"]

    weekday_order = [
        "Domingo",
        "Segunda",
        "Terça",
        "Quarta",
        "Quinta",
        "Sexta",
        "Sábado",
    ]

    df["weekday"] = pd.Categorical(
        df["weekday"], categories=weekday_order, ordered=True
    )

    df = df.sort_values(by=["weekday", "hour", "name"])

    for weekday, group in df.groupby("weekday", observed=False):
        if group.empty:
            continue
        print(f"{weekday}:")
        for data in group.iterrows():
            item = data[1]
            formatted_hour = str(item["hour"]).zfill(2)
            print(f"{formatted_hour}:00: {item['name']} - {item['price']}")
        print()


if __name__ == "__main__":
    db = DB()
    items = db.con.execute(
        "SELECT id, name, quality FROM items ORDER BY id"
    ).fetchall()
    while True:
        print("Selecione o serviço que você quer:")
        print("0 - Sair")
        print("1 - Gráfico")
        print("2 - Melhores dias e horas")
        print()
        escolha = input("Digite a opção: ")
        if escolha == "0":
            print("Saindo...")
            break
        if escolha == "1":
            graph_module(db)
        elif escolha == "2":
            best_day_hour_module(db, items)
        else:
            print("Opção inválida! Tente novamente")
