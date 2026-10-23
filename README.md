# backupradar-mcp

**Backup Radar** MCP server — exposes the Backup Radar v2 Backups API as MCP tools.

> **Naming note:** app.mspbots.ai calls this integration **"Backup Radar"** (`sys_integration.subject_code = BACKUPRADAR`).

<div align="center">

## MSPbots Connector

**The MCP Gateway built for MSPs: visible, controlled, and your data stays where it belongs.**

[**Get started at connect.mspbots.ai →**](https://connect.mspbots.ai)

</div>

---

MSPbots Connector gives your AI clients one MCP URL to reach your entire MSP stack (RMM, PSA, documentation, security, finance), and gives you control over who can call which tool and a record of everything that was called.

**Hosted service: [connect.mspbots.ai](https://connect.mspbots.ai)** · Free to use.

### Why Connector

![MSPbots Connector](https://stgoss.mspbots.ai/files/mcp/mspbots-mcp.png)

| | |
|---|---|
| **Visible** | Every tool call is logged: who, which vendor, when. Usage dashboard, CSV export, SIEM streaming. |
| **Controlled** | Role-based, per-tool allowlist. Deny by default. |
| **Protected** | Credentials encrypted per record. AI clients never see your vendor passwords or tokens. |
| **MSP-native** | Built for the MSP stack only: RMM, PSA, documentation, security, finance. |

### Quick start

1. **Sign up** at [connect.mspbots.ai](https://connect.mspbots.ai).
2. **Connect your vendors.** Pick from 150+ connectors and authorize each one on the vendor's own page, or bring your own API keys. No extra vendor accounts needed.
3. **Set access.** Create roles and decide which tools each role may call. Nothing is allowed until you allow it.
4. **Add your MCP URL to your AI client.** Copy the URL from your Connector dashboard into Claude, ChatGPT, Cursor, VS Code, Gemini, Codex, or any MCP-capable client.
5. **Ask your AI to do real work**, and watch every call appear in the audit log.

### Features

**Unified gateway**
- One MCP URL for all your AI clients
- 150+ connectors across the MSP stack
- Custom MCP servers supported, free
- Authorization happens on each vendor's own page; the AI never sees passwords or tokens
- Bring your own credentials: use the vendor API keys you already have
- Multiple accounts per app; connect once, reuse across AI clients
- Tool search: finds the right action for the task
- One sign-in; vendor credentials are injected behind the scenes and OAuth tokens refresh automatically

**Visibility**
- Audit log for every tool call (who, which vendor, when)
- Usage dashboard: call volume, top vendors, error rate, per-user activity
- Export audit logs to CSV, or stream to Loki, Graylog, or LogScale (SIEM)
- Optional recording of tool arguments and result summaries (off by default, enabled per organization)

**Control**
- Per-role, per-tool allowlist, deny by default
- owner / admin / member roles
- SCIM provisioning with Entra ID, Okta, JumpCloud, and Google Workspace

**Security**
- Credentials encrypted one record at a time (AES-256-GCM, per-record key)
- AI clients authenticate with OAuth 2.1 + PKCE
- Vendor responses are scanned for prompt-injection patterns and returned as structured data. This is one layer of defense, not a guarantee against every attack.
- Static egress IP for customer firewall and API allowlisting

### Pricing

**Free.**

Links: [connect.mspbots.ai](https://connect.mspbots.ai) · [mspbots.ai](https://mspbots.ai)

---

## Overview

This server implements the [Model Context Protocol](https://modelcontextprotocol.io/) (Streamable HTTP/SSE transport) and follows the MSPbots **Vendor MCP Service SOP**: stateless, no stored credentials, per-request header authentication.

Backup Radar's own API authenticates with a **static, long-lived API key** sent in a header literally named `ApiKey` (not OAuth2 — confirmed against the vendor's own OpenAPI `securitySchemes`). This server never stores the key; it is forwarded per-request from the caller's `X-BackupRadar-Api-Key` header.

## Scope note: MSPbots' Backup Radar integration references 2 endpoints from a retired API version

MSPbots' own Backup Radar integration (`sys_integration_api`) is configured with 6 interfaces. While researching this build, 2 of them were found to target the **Backup Radar API v1**, which the vendor retired on **2026-01-09** ("As of January 9, 2026, the Backup Radar API v1 has been retired and is no longer available... all integrations must use API v2"):

- `Backup Radar Policies` — `GET /policies` (v1 only, no v2 equivalent)
- `Backup Radar BG` — `GET /backups/bg` (v1 only, no v2 equivalent)

The current v2 spec (`https://api.backupradar.com/docs/2.0`) has exactly 7 operations, all under a single `Backups` tag (`/backups`, `/backups/{backupId}`, `/backups/{backupId}/results`, `/backups/filters`, `/backups/inactive`, `/backups/retired`, `/backups/overview`) — there is no `policies` or `bg` concept in v2. Calling these 2 legacy endpoints today would fail, which conflicts with this build's "self-test must succeed" requirement.

**Decision (confirmed with the requester):** this MCP implements only the **4 of 6** MSPbots-configured interfaces that map cleanly onto the current, supported Backup Radar API v2 — `Backup Radar Backups`, `Backup Radar Backup Scheduled`, `Backup Radar Inactive`, and `Backup Radar Backup Results`. The 2 retired-v1-only interfaces are intentionally not implemented.

## Quick Start

### Docker (recommended)

```bash
docker compose up --build
```

The server starts on `http://localhost:8080`.

### Local (uv)

```bash
uv sync
python -m backupradar_mcp
```

## Health Check

```bash
curl http://localhost:8080/health
# {"status": "ok"}
```

No credentials are required for the health endpoint.

## Authentication Parameters (Authentication)

Every request to `/mcp` must include the following HTTP headers:

| Header | Type | Required | Default | Allowed values | Description | Example |
|---|---|---|---|---|---|---|
| `X-BackupRadar-Api-Key` | string | Yes | None | None (free text) | Backup Radar's static long-lived API Key (not OAuth2), consistent with the header authentication method named `ApiKey` in the vendor's own OpenAPI spec; corresponds to the "API Key" field in the existing MSPbots Backup Radar integration configuration. | `X-BackupRadar-Api-Key: <api_key>` |
| `X-BackupRadar-Site` | string | Yes | None | `us`, `eu` (or pass the full domain `api.backupradar.com` / `api-eu.backupradar.com` directly) | Selects whether to call the US or the EU region Backup Radar API; corresponds to the required "Site" dropdown field in the existing MSPbots Backup Radar integration configuration. | `X-BackupRadar-Site: us` |

Missing either header returns `401 Unauthorized`.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MCP_HTTP_PORT` | `8080` | Listening port |
| `MCP_HTTP_HOST` | `0.0.0.0` | Listening host |

## MCP Endpoint

```
POST http://localhost:8080/mcp
```

Connect your MCP client with:
- Transport: `http` (Streamable HTTP / SSE)
- Headers: `X-BackupRadar-Api-Key: <api_key>` (required), `X-BackupRadar-Site: us|eu` (required)

## Tool List

**4 tools** — the subset of MSPbots' 6 configured Backup Radar interfaces that are still supported by the current (v2) Backup Radar API (see scope note above).

| Tool | Description | Parameters |
|---|---|---|
| `backupradar_get_backups` | Query the backup list with pagination, filterable by date/company/device/job name | `page?`, `size?`, `date?`, `search_by_company_name?`, `search_by_device_name?`, `search_by_job_name?`, `statuses?`, `companies?`, `tags?`, `extra_params?` |
| `backupradar_get_scheduled_backups` | Query scheduled backup jobs and recent history | `history_days?`, `size?`, `search_by_company_name?`, `search_by_device_name?`, `search_by_job_name?`, `extra_params?` |
| `backupradar_get_inactive_backups` | Query inactive backups with pagination | `page?`, `size?`, `search_by_company_name?`, `search_by_device_name?`, `search_by_job_name?`, `extra_params?` |
| `backupradar_get_backup_results` | Get the execution result of a backup on the specified date by ID | `backup_id`(required), `date?` |

## Test Example (Test Example)

Fetch recent backups:

```json
{
  "method": "tools/call",
  "params": { "name": "backupradar_get_backups", "arguments": { "size": 20, "date": "2026-07-01" } }
}
```

Equivalent `curl` against the running server (streamable HTTP MCP endpoint):

```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "X-BackupRadar-Api-Key: <api_key>" \
  -H "X-BackupRadar-Site: us" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": { "name": "backupradar_get_backups", "arguments": { "size": 20 } }
  }'
```

A parameterized call:

```json
{
  "method": "tools/call",
  "params": {
    "name": "backupradar_get_backup_results",
    "arguments": { "backup_id": 3716317, "date": "2026-07-01" }
  }
}
```

## API Reference

- API v2 docs (Swagger UI): `https://api.backupradar.com/index.html` (US) / `https://api-eu.backupradar.com/index.html` (EU)
- OpenAPI JSON: `https://api.backupradar.com/docs/2.0`

## Known Gaps / Implementation Notes

- The 2 MSPbots-configured interfaces that reference the retired Backup Radar API v1 (`policies`, `backups/bg`) are intentionally not implemented — see the scope note above.
- Not yet tested against a live Backup Radar account — only protocol-level verification (health check, 401 on missing headers, `tools/list` returning all 4 tools) has been done so far.
- `backupradar_get_backups` and `backupradar_get_scheduled_backups` both call the same underlying `GET /backups` endpoint with different default filters, mirroring how MSPbots itself configured them as two distinct saved API calls.
