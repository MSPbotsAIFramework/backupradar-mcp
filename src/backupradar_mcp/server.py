import contextvars
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from .api_client import BackupRadarClient
from .config import Settings

# Per-request credential isolation via contextvars.
# GatewayTokenMiddleware sets this before the MCP handler runs.
# Python asyncio copies context per task, so concurrent SSE connections are isolated.
# Value is (api_key, site) — both required, mirroring the "API Key" / "Site"
# fields that are both required on the existing Backup Radar integration on
# app.mspbots.ai (Site: US = api.backupradar.com, EU = api-eu.backupradar.com).
_gateway_creds_var: contextvars.ContextVar[tuple[str, str] | None] = contextvars.ContextVar(
    "backupradar_gateway_creds", default=None
)

_SITE_MAP = {
    "us": "https://api.backupradar.com",
    "eu": "https://api-eu.backupradar.com",
    "api.backupradar.com": "https://api.backupradar.com",
    "api-eu.backupradar.com": "https://api-eu.backupradar.com",
}


def get_client_from_context(settings: Settings) -> BackupRadarClient | None:
    """Resolve the active BackupRadarClient for the current request context."""
    creds = _gateway_creds_var.get()
    if not creds:
        return None
    api_key, site = creds
    base_url = _SITE_MAP.get(site.strip().lower(), site)
    return BackupRadarClient(api_key, base_url)


class GatewayTokenMiddleware:
    """ASGI middleware.

    Reads X-BackupRadar-Api-Key (required) and X-BackupRadar-Site (required)
    from request headers and stores them in the contextvar. Header names
    mirror the "API Key" / "Site" fields used by the existing Backup Radar
    integration on app.mspbots.ai. Returns 401 if either header is missing on
    /mcp requests.
    """

    def __init__(self, app: ASGIApp, settings: Settings):
        self.app = app
        self.settings = settings

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if not path.startswith("/mcp"):
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        api_key = request.headers.get("x-backupradar-api-key")
        site = request.headers.get("x-backupradar-site")
        if not api_key or not site:
            response = JSONResponse(
                {
                    "error": "Missing credentials",
                    "message": (
                        "This server requires the X-BackupRadar-Api-Key header "
                        "(Backup Radar API key) and the X-BackupRadar-Site header "
                        '("us" / "eu" or the full site hostname)'
                    ),
                    "required_headers": ["X-BackupRadar-Api-Key", "X-BackupRadar-Site"],
                    "optional_headers": [],
                },
                status_code=401,
            )
            await response(scope, receive, send)
            return

        ctx_token = _gateway_creds_var.set((api_key, site))
        try:
            await self.app(scope, receive, send)
        finally:
            _gateway_creds_var.reset(ctx_token)


def create_mcp_server(settings: Settings) -> FastMCP:
    """Build the FastMCP server instance and register all Backup Radar tools."""
    # DNS-rebinding protection is a browser-oriented safeguard that rejects
    # non-localhost Host headers with 421. Disable it so the server works
    # correctly behind a reverse proxy or docker network.
    mcp = FastMCP(
        name="backupradar-mcp",
        instructions=(
            "Backup Radar is a backup monitoring and reporting platform MSPs use to "
            "track the health of clients' backup jobs across many backup products "
            "(Veeam, Datto, Acronis, etc.) in one place. It ingests daily backup job "
            "results and classifies each job per device as success, warning, failure, "
            "or missing, and flags jobs that have gone inactive (stopped reporting "
            "entirely). Use this server to answer: which backups failed or need "
            "attention today (backupradar_get_backups, filter by date/status/company/"
            "device), what is scheduled to run and its recent history "
            "(backupradar_get_scheduled_backups), which jobs have gone silent "
            "(backupradar_get_inactive_backups), and the detailed pass/fail history "
            "for one specific backup job (backupradar_get_backup_results, requires "
            "backup_id). All 4 tools are read-only queries against the Backup Radar "
            "v2 API; there are no write or delete tools. Typical flow: call "
            "backupradar_get_backups or backupradar_get_inactive_backups to find "
            "backups of concern, then backupradar_get_backup_results(backup_id=...) "
            "to drill into one job's history."
        ),
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
        stateless_http=True,
        json_response=True,
    )

    client_factory: Callable[[], BackupRadarClient | None] = lambda: get_client_from_context(settings)

    from .tools import backups

    backups.register(mcp, client_factory)

    return mcp
