import json
import os

import httpx
import requests
from fastapi import HTTPException, status
from requests.auth import HTTPBasicAuth

from app.logger import get_logger
from exceptions import EnvNotSetError

logger = get_logger(__name__)


def get_auth_token():
    try:
        with open("token.json", "r", encoding="utf-8") as file:
            return json.load(file)["access_token"]
    except FileNotFoundError:
        logger.info("Nenhum arquivo com token salvo, gerando novo token.")
        generate_new_token()
        return get_auth_token()
    except KeyError:
        logger.warning("Arquivo de token corrompido, gerando novo token.")
        generate_new_token()
        return get_auth_token()


def generate_new_token():
    try:
        client_id = os.getenv("BLIZZARD_CLIENT_ID")
        client_secret = os.getenv("BLIZZARD_CLIENT_SECRET")
        if client_id is None or client_secret is None:
            variables = []
            if not client_id:
                variables.append("BLIZZARD_CLIENT_ID")
            if not client_secret:
                variables.append("BLIZZARD_CLIENT_SECRET")
            raise EnvNotSetError(variables)

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
        logger.error(f"An error occurred while generating token: {e}", exc_info=True)
        if hasattr(e, "response") and e.response is not None:
            logger.error(f"Response status code: {e.response.status_code}")
            logger.error(f"Response body: {e.response.text}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)


async def fetch_blizzard_api(
    url: str,
    client: httpx.AsyncClient,
    params: dict | None = None,
    resource_name: str = "Recurso",
):
    headers = {"Authorization": f"Bearer {get_auth_token()}"}
    response = await client.get(url, headers=headers, params=params)

    if response.status_code == 401:
        logger.info("Token expirado, gerando novo token.")
        generate_new_token()
        headers["Authorization"] = f"Bearer {get_auth_token()}"
        response = await client.get(url, headers=headers, params=params)

    if response.status_code == 404:
        logger.error(f"{resource_name} não encontrado na API da Blizzard.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_name} não encontrado na API da Blizzard.",
        )

    response.raise_for_status()

    return response.json()
