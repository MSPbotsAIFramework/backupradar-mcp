from collections.abc import Callable
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .._json import dump_json_capped
from ..api_client import BackupRadarClient, BackupRadarError
from ._common import NO_TOKEN

_MAX_SIZE = 200


def register(mcp: FastMCP, client_factory: Callable[[], BackupRadarClient | None]) -> None:

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def backupradar_get_backups(
        page: Annotated[int | None, Field(description="Page number to fetch (default 1).")] = None,
        size: Annotated[
            int | None, Field(description="Page size (default 50, hard-capped at 200).")
        ] = None,
        date: Annotated[
            str | None, Field(description='Date to retrieve backups for, e.g. "2018-02-14".')
        ] = None,
        search_by_company_name: Annotated[
            str | None, Field(description="Filter by company name.")
        ] = None,
        search_by_device_name: Annotated[
            str | None, Field(description="Filter by device name.")
        ] = None,
        search_by_job_name: Annotated[str | None, Field(description="Filter by job name.")] = None,
        statuses: Annotated[
            list[str] | None, Field(description="Filter by one or more backup statuses.")
        ] = None,
        companies: Annotated[
            list[str] | None, Field(description="Filter by one or more companies.")
        ] = None,
        tags: Annotated[list[str] | None, Field(description="Filter by one or more tags.")] = None,
        extra_params: Annotated[
            dict[str, object] | None,
            Field(
                description=(
                    "Additional raw query params: SearchByBackupMethod, "
                    "SearchByTooltip, SearchByTag, DaysWithoutSuccess, HistoryDays, "
                    "FilterScheduled, searchString, excludeTags, backupMethods, "
                    "deviceTypes, excludeDeviceTypes, policyIds, "
                    "excludeBackupMethods, policyTypes."
                )
            ),
        ] = None,
    ) -> str:
        """List backups, optionally filtered by date, company, device, job, status, or tag."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        if size is not None:
            size = min(size, _MAX_SIZE)
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
            return dump_json_capped(result)
        except BackupRadarError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def backupradar_get_scheduled_backups(
        history_days: Annotated[
            int | None,
            Field(description="Days of backup history to include (default 0, max 31)."),
        ] = None,
        size: Annotated[
            int | None, Field(description="Page size (default 50, hard-capped at 200).")
        ] = None,
        search_by_company_name: Annotated[
            str | None, Field(description="Filter by company name.")
        ] = None,
        search_by_device_name: Annotated[
            str | None, Field(description="Filter by device name.")
        ] = None,
        search_by_job_name: Annotated[str | None, Field(description="Filter by job name.")] = None,
        extra_params: Annotated[
            dict[str, object] | None,
            Field(
                description=(
                    "Additional raw query params: Page, DaysWithoutSuccess, date, "
                    "statuses, companies, tags, backupMethods, deviceTypes, "
                    "policyIds, policyTypes."
                )
            ),
        ] = None,
    ) -> str:
        """List scheduled backup jobs, with optional recent history."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        if size is not None:
            size = min(size, _MAX_SIZE)
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
            return dump_json_capped(result)
        except BackupRadarError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def backupradar_get_inactive_backups(
        page: Annotated[int | None, Field(description="Page number to fetch (default 1).")] = None,
        size: Annotated[
            int | None, Field(description="Page size (default 50, hard-capped at 200).")
        ] = None,
        search_by_company_name: Annotated[
            str | None, Field(description="Filter by company name.")
        ] = None,
        search_by_device_name: Annotated[
            str | None, Field(description="Filter by device name.")
        ] = None,
        search_by_job_name: Annotated[str | None, Field(description="Filter by job name.")] = None,
        extra_params: Annotated[
            dict[str, object] | None,
            Field(
                description=(
                    "Additional raw query params: SearchByBackupMethod, "
                    "SearchByEmailFrom, SearchByBackupType."
                )
            ),
        ] = None,
    ) -> str:
        """List backups that have gone inactive (stopped reporting)."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        if size is not None:
            size = min(size, _MAX_SIZE)
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
            return dump_json_capped(result)
        except BackupRadarError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def backupradar_get_backup_results(
        backup_id: Annotated[int, Field(description="Required unique identifier of the backup.")],
        date: Annotated[
            str | None,
            Field(
                description=(
                    'Date to retrieve results for, e.g. "2018-02-14". Defaults to '
                    "the vendor API's own default (typically the latest result) if "
                    "omitted."
                )
            ),
        ] = None,
    ) -> str:
        """Get backup results for one specific backup, for a given date."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        params = {"date": date}
        try:
            result = await client.get(f"/backups/{backup_id}/results", params=params)
            return dump_json_capped(result)
        except BackupRadarError as e:
            return e.to_envelope()
