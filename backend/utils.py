def get_env() -> dict[str, str]:
    with open("./.env", "r", encoding="utf-8") as file:
        env: dict[str, str] = dict()
        for line in file.readlines():
            key, value = line.split("=")
            env[key] = value.strip()
    return env
