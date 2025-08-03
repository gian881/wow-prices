def get_env() -> dict[str, str]:
    with open("./.env", "r", encoding="utf-8") as file:
        env: dict[str, str] = dict()
        for line in file.readlines():
            key, value = line.split("=")
            env[key] = value.strip()
    return env


def price_to_gold_and_silver(price: int | float) -> tuple[int, int]:
    """Converte o preço em centavos para ouro e prata."""
    gold = int(price) // 10000
    silver = (int(price) % 10000) // 100
    return gold, silver
