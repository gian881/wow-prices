import json
import requests
from requests.auth import HTTPBasicAuth


def get_env() -> dict[str, str]:
    with open("./.env", "r", encoding="utf-8") as file:
        env: dict[str, str] = dict()
        for line in file.readlines():
            key, value = line.split("=")
            env[key] = value.strip()
    return env


def get_auth_token():
    try:
        with open("token.json", "r", encoding="utf-8") as file:
            return json.load(file)["access_token"]
    except FileNotFoundError:
        print("Nenhum arquivo com token salvo, gerando novo token.")
        generate_new_token()
        return get_auth_token()
    except KeyError:
        print("Arquivo de token corrompido, gerando novo token.")
        generate_new_token()
        return get_auth_token()


def generate_new_token():
    try:
        env = get_env()
        client_id = env.get("CLIENT_ID", "")
        client_secret = env.get("CLIENT_SECRET", "")
        if client_id == "" or client_secret == "":
            raise Exception("Credenciais não configuradas.")

        res = requests.post(
            "https://oauth.battle.net/token",
            data={"grant_type": "client_credentials"},
            auth=HTTPBasicAuth(client_id, client_secret),
        )

        res.raise_for_status()

        token_data = res.json()

        with open("token.json", "w", encoding="utf-8") as file:
            json.dump(token_data, file)

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"Response status code: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


get_auth_token()
