from models import PriceGoldSilver


def get_env() -> dict[str, str]:
    with open("./.env", "r", encoding="utf-8") as file:
        env: dict[str, str] = dict()
        for line in file.readlines():
            key, value = line.split("=")
            env[key] = value.strip()
    return env


def price_to_gold_and_silver(price: int | float) -> PriceGoldSilver:
    """Converte o preço em centavos para ouro e prata."""
    gold = int(price) // 10000
    silver = (int(price) % 10000) // 100
    return PriceGoldSilver(gold=gold, silver=silver)


def gold_and_silver_to_price(price_gold_and_silver: PriceGoldSilver) -> int:
    """Converte ouro e prata para preço em centavos."""
    return (
        price_gold_and_silver.gold * 10000 + price_gold_and_silver.silver * 100
    )
