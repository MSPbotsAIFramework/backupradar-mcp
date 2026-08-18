# backupradar-mcp

**Backup Radar** MCP server — exposes the Backup Radar v2 Backups API as MCP tools.

> **Naming note:** app.mspbots.ai calls this integration **"Backup Radar"** (`sys_integration.subject_code = BACKUPRADAR`).

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

## 授权参数说明 (Authentication)

Every request to `/mcp` must include the following HTTP headers:

| Header | 类型 | 是否必填 | 默认值 | 枚举值 | 字段描述 | Example |
|---|---|---|---|---|---|---|
| `X-BackupRadar-Api-Key` | string | 必填 | 无 | 无(自由文本) | Backup Radar 的静态长期 API Key(非 OAuth2),与 vendor 自身 OpenAPI 规范里名为 `ApiKey` 的 header 认证方式一致;对应 MSPbots 现有 Backup Radar 集成配置里的 "API Key" 字段。 | `X-BackupRadar-Api-Key: <api_key>` |
| `X-BackupRadar-Site` | string | 必填 | 无 | `us`、`eu`(或直接传完整域名 `api.backupradar.com` / `api-eu.backupradar.com`) | 选择调用美国还是欧洲区域的 Backup Radar API,对应 MSPbots 现有 Backup Radar 集成配置里的必填 "Site" 下拉字段。 | `X-BackupRadar-Site: us` |

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

| Tool | 功能 | 参数 |
|---|---|---|
| `backupradar_get_backups` | 分页查询备份列表,可按日期/公司/设备/任务名过滤 | `page?`, `size?`, `date?`, `search_by_company_name?`, `search_by_device_name?`, `search_by_job_name?`, `statuses?`, `companies?`, `tags?`, `extra_params?` |
| `backupradar_get_scheduled_backups` | 查询已排程的备份任务及近期历史 | `history_days?`, `size?`, `search_by_company_name?`, `search_by_device_name?`, `search_by_job_name?`, `extra_params?` |
| `backupradar_get_inactive_backups` | 分页查询不活跃(inactive)的备份 | `page?`, `size?`, `search_by_company_name?`, `search_by_device_name?`, `search_by_job_name?`, `extra_params?` |
| `backupradar_get_backup_results` | 按 ID 查某个备份在指定日期的执行结果 | `backup_id`(必填), `date?` |

## 测试示例 (Test Example)

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
