from typing import Any

from authlib.common.errors import AuthlibHTTPError
from authlib.integrations.httpx_client import OAuth2Client
from authlib.oauth2.rfc6749 import OAuth2Token

API_URL: str = "https://apis.cleargrass.com"
API_DEVICES_ENDPOINT: str = "/v1/apis/devices"
OAUTH2_URL: str = "https://oauth.cleargrass.com"
OAUTH2_AUTHORIZE_ENDPOINT: str = "/oauth2/token"

REQUEST_TIMEOUT: int = 30


class QingpingApi:
    def __init__(self, client_id: str, client_secret: str) -> None:
        self.oauth_client = OAuth2Client(
            client_id,
            client_secret,
            scope="device_full_access",
            update_token=self.update_token,
        )

        try:
            response = self.oauth_client.fetch_token(
                OAUTH2_URL + OAUTH2_AUTHORIZE_ENDPOINT,
                grant_type="client_credentials",
            )
        except AuthlibHTTPError as e:
            raise Exception(e)

        self.access_token = response["access_token"]

    def update_token(self, token, refresh_token=None, access_token=None):
        if refresh_token:
            item = OAuth2Token.find(name=name, refresh_token=refresh_token)  # type: ignore
        elif access_token:
            item = OAuth2Token.find(name=name, access_token=access_token)  # type: ignore
        else:
            return

        # update old token
        item.access_token = token["access_token"]
        item.refresh_token = token.get("refresh_token")
        item.expires_at = token["expires_at"]
        item.save()

    def get_devices(self) -> dict[str, Any]:
        try:
            response = self.oauth_client.get(
                API_URL + API_DEVICES_ENDPOINT, timeout=REQUEST_TIMEOUT
            )
        except AuthlibHTTPError as err:
            raise Exception(err)

        self.data = response.json()
        return {
            "name": self.data["devices"][0]["info"]["product"]["en_name"],
            "co2": self.data["devices"][0]["data"]["co2"]["value"],
            "temperature": self.data["devices"][0]["data"]["temperature"]["value"],
            "humidity": round(self.data["devices"][0]["data"]["humidity"]["value"]),
            "tvoc": self.data["devices"][0]["data"]["tvoc"]["value"],
            "pm25": self.data["devices"][0]["data"]["pm25"]["value"],
            "pm10": self.data["devices"][0]["data"]["pm10"]["value"],
        }
