from typing import Any

import httpx

US_SITE = "https://api.backupradar.com"
EU_SITE = "https://api-eu.backupradar.com"


class BackupRadarError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"Backup Radar API error {status_code}: {message}")


class BackupRadarClient:
    """Async httpx client wrapping the Backup Radar v2 Backups API.

    Authentication is a static, long-lived API key sent in a header literally
    named "ApiKey" (per the vendor's own OpenAPI securityScheme) — not OAuth2.
    """

    def __init__(self, api_key: str, base_url: str = US_SITE):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        return {
            "ApiKey": self._api_key,
            "Accept": "application/json",
        }

    def _clean_params(self, params: dict | None) -> dict:
        if not params:
            return {}
        return {k: v for k, v in params.items() if v is not None}

    async def get(self, path: str, params: dict | None = None) -> Any:
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.get(
                    f"{self._base_url}{path}",
                    headers=self._headers(),
                    params=self._clean_params(params),
                )
            except httpx.RequestError as e:
                raise BackupRadarError(0, f"{e or type(e).__name__} (url={self._base_url}{path})") from e
            self._raise_for_status(resp)
            return self._parse_body(resp)

    def _parse_body(self, resp: httpx.Response) -> Any:
        if not resp.content:
            return None
        try:
            return resp.json()
        except ValueError:
            return {"raw_response": resp.text}

    def _raise_for_status(self, resp: httpx.Response) -> None:
        if resp.status_code >= 400:
            try:
                detail = resp.json()
                if isinstance(detail, dict):
                    msg = detail.get("title") or detail.get("message") or detail.get("detail") or str(detail)
                else:
                    msg = str(detail)
            except ValueError:
                msg = resp.text
            raise BackupRadarError(resp.status_code, msg)
