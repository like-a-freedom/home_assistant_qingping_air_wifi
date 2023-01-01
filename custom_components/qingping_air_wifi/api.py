import logging
from typing import Any
from datetime import datetime as dt, timedelta as td

from authlib.integrations.httpx_client import OAuth2Client

API_URL: str = "https://apis.cleargrass.com"
API_DEVICES_ENDPOINT: str = "/v1/apis/devices"
OAUTH2_URL: str = "https://oauth.cleargrass.com"
OAUTH2_AUTHORIZE_ENDPOINT: str = "/oauth2/token"

SCAN_INTERVAL = td(seconds=5)
REQUEST_TIMEOUT: int = 30
_LOGGER = logging.getLogger(__name__)


class QingpingApi:
    def __init__(self, client_id: str, client_secret: str) -> None:
        self.oauth_client: OAuth2Client = OAuth2Client(
            client_id,
            client_secret,
            scope="device_full_access",
        )

        token = self._get_token()
        self.access_token: str | None = token["access_token"]
        self.token_expire_time: int | None = token["expires_at"]

    def _is_token_expired(self, expire_time: int) -> bool:
        if dt.now() >= dt.fromtimestamp(int(expire_time)):
            return True
        else:
            return False

    def _get_token(self) -> dict[str, Any] | None:
        try:
            self.response = self.oauth_client.fetch_token(
                OAUTH2_URL + OAUTH2_AUTHORIZE_ENDPOINT,
                grant_type="client_credentials",
            )

            self.access_token = self.response["access_token"]
            self.token_expire_time = int(self.response["expires_at"])

            _LOGGER.info(f"Qingping API token successfully fetched")

            return {
                "access_token": self.access_token,
                "expires_at": self.token_expire_time,
            }
        except Exception as err:
            _LOGGER.error(f"Error: {self.response}, got exception: {err}")

    def get_devices(self) -> dict[str, Any] | None:
        try:
            if self._is_token_expired(self.token_expire_time):
                self._get_token()
                _LOGGER.warning("Token has been expired, renewing...")

            response = self.oauth_client.get(
                API_URL + API_DEVICES_ENDPOINT, timeout=REQUEST_TIMEOUT
            )

            if response.status_code == 200:
                self.data = response.json()

                return {
                    "name": self.data["devices"][0]["info"]["product"]["en_name"],
                    "co2": self.data["devices"][0]["data"]["co2"]["value"],
                    "temperature": round(
                        self.data["devices"][0]["data"]["temperature"]["value"], 1
                    ),
                    "humidity": round(
                        self.data["devices"][0]["data"]["humidity"]["value"], 1
                    ),
                    "tvoc": self.data["devices"][0]["data"]["tvoc"]["value"],
                    "pm25": self.data["devices"][0]["data"]["pm25"]["value"],
                    "pm10": self.data["devices"][0]["data"]["pm10"]["value"],
                }
            else:
                _LOGGER.error(
                    f"Status code: {response.status_code}, body: {response.text}"
                )
        except Exception as err:
            _LOGGER.error(f"Can't fetch `/devices` endpoint: {err}")
