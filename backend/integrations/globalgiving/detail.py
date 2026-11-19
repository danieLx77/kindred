"""Project detail lookup behind the Kindred provider contract."""

import re

from projects.errors import ProviderError, ProviderFailure
from projects.models import ProjectDetail

from .discovery import GlobalGivingDiscoveryAdapter
from .mapping import detail


class GlobalGivingProjectProvider(GlobalGivingDiscoveryAdapter):
    """Support discovery and detail with the same backend HTTP client."""

    async def get_project(self, project_id: str) -> ProjectDetail | None:
        if not isinstance(project_id, str) or not re.fullmatch(
            r"[0-9]{1,20}", project_id
        ):
            raise ValueError("GlobalGiving project ID must be a positive integer")
        project_id = project_id.lstrip("0")
        if not project_id:
            raise ValueError("GlobalGiving project ID must be a positive integer")

        try:
            payload = await self._http.get(f"projectservice/projects/{project_id}", {})
        except ProviderError as error:
            if error.reason == ProviderFailure.NOT_FOUND:
                return None
            raise
        return detail(payload, project_id)
