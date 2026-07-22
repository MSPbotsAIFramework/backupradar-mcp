import json
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..api_client import BackupRadarClient, BackupRadarError
from ._common import NO_TOKEN


def register(mcp: FastMCP, client_factory: Callable[[], BackupRadarClient | None]) -> None:

    @mcp.tool()
    async def backupradar_get_backups(
        page: int | None = None,
        size: int | None = None,
        date: str | None = None,
        search_by_company_name: str | None = None,
        search_by_device_name: str | None = None,
        search_by_job_name: str | None = None,
        statuses: list[str] | None = None,
        companies: list[str] | None = None,
        tags: list[str] | None = None,
        extra_params: dict | None = None,
    ) -> str:
        """Retrieve a paginated list of backups, optionally filtered by date.

        API: GET /backups (Backup Radar API v2)

        Args:
            page: Page number to fetch (default 1).
            size: Page size (default 50, max 1000).
            date: Date to retrieve backups for, e.g. "2018-02-14".
            search_by_company_name: Filter by company name.
            search_by_device_name: Filter by device name.
            search_by_job_name: Filter by job name.
            statuses: Filter by one or more backup statuses.
            companies: Filter by one or more companies.
            tags: Filter by one or more tags.
            extra_params: Additional raw query params (SearchByBackupMethod,
                SearchByTooltip, SearchByTag, DaysWithoutSuccess, HistoryDays,
                FilterScheduled, searchString, excludeTags, backupMethods,
                deviceTypes, excludeDeviceTypes, policyIds,
                excludeBackupMethods, policyTypes).
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        params = {
            "Page": page,
            "Size": size,
            "date": date,
            "SearchByCompanyName": search_by_company_name,
            "SearchByDeviceName": search_by_device_name,
            "SearchByJobName": search_by_job_name,
            "statuses": statuses,
            "companies": companies,
            "tags": tags,
            **(extra_params or {}),
        }
        try:
            result = await client.get("/backups", params=params)
            return json.dumps(result, indent=2)
        except BackupRadarError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def backupradar_get_scheduled_backups(
        history_days: int | None = None,
        size: int | None = None,
        search_by_company_name: str | None = None,
        search_by_device_name: str | None = None,
        search_by_job_name: str | None = None,
        extra_params: dict | None = None,
    ) -> str:
        """Retrieve backups filtered to only scheduled backup jobs, with recent history.

        API: GET /backups?FilterScheduled=true (Backup Radar API v2)

        Args:
            history_days: Number of days of backup history to include
                (default 0 = no history, max 31).
            size: Page size (default 50, max 1000).
            search_by_company_name: Filter by company name.
            search_by_device_name: Filter by device name.
            search_by_job_name: Filter by job name.
            extra_params: Additional raw query params (Page, DaysWithoutSuccess,
                date, statuses, companies, tags, backupMethods, deviceTypes,
                policyIds, policyTypes).
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        params = {
            "FilterScheduled": True,
            "HistoryDays": history_days,
            "Size": size,
            "SearchByCompanyName": search_by_company_name,
            "SearchByDeviceName": search_by_device_name,
            "SearchByJobName": search_by_job_name,
            **(extra_params or {}),
        }
        try:
            result = await client.get("/backups", params=params)
            return json.dumps(result, indent=2)
        except BackupRadarError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def backupradar_get_inactive_backups(
        page: int | None = None,
        size: int | None = None,
        search_by_company_name: str | None = None,
        search_by_device_name: str | None = None,
        search_by_job_name: str | None = None,
        extra_params: dict | None = None,
    ) -> str:
        """Retrieve a paginated list of inactive backups.

        API: GET /backups/inactive (Backup Radar API v2)

        Args:
            page: Page number to fetch (default 1).
            size: Page size (default 50, max 1000).
            search_by_company_name: Filter by company name.
            search_by_device_name: Filter by device name.
            search_by_job_name: Filter by job name.
            extra_params: Additional raw query params (SearchByBackupMethod,
                SearchByEmailFrom, SearchByBackupType).
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        params = {
            "Page": page,
            "Size": size,
            "SearchByCompanyName": search_by_company_name,
            "SearchByDeviceName": search_by_device_name,
            "SearchByJobName": search_by_job_name,
            **(extra_params or {}),
        }
        try:
            result = await client.get("/backups/inactive", params=params)
            return json.dumps(result, indent=2)
        except BackupRadarError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def backupradar_get_backup_results(
        backup_id: int,
        date: str | None = None,
    ) -> str:
        """Retrieve backup results for a specific backup, for a given date.

        API: GET /backups/{backupId}/results (Backup Radar API v2)

        Args:
            backup_id: Required unique identifier of the backup.
            date: Date to retrieve results for, e.g. "2018-02-14". Defaults
                to the vendor API's own default (typically the latest result)
                if omitted.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        params = {"date": date}
        try:
            result = await client.get(f"/backups/{backup_id}/results", params=params)
            return json.dumps(result, indent=2)
        except BackupRadarError as e:
            return f"Error: {e}"
