"""Resolve eWoodX entity files for generic file transfer."""

from pathlib import Path
from typing import Any, Dict

from framework.workspace import (
    DomainManager,
    EntityManager,
    EntryManager,
    load_workspace,
)

from projects.ewoodx.config import (
    EWOODX_REPOSITORY_ROOT,
    EWOODX_WORKSPACE_LAYOUT,
    TIMBER_ENTITY_INDEX,
)


class EWoodXEntityFileResolver:
    """
    Resolve semantic entity file requests to authoritative
    eWoodX workspace paths.
    """

    def _load_entity_manager(
        self,
        workspace_name: str,
    ) -> EntityManager:

        workspace_name = str(
            workspace_name or ""
        ).strip()

        if not workspace_name:
            raise ValueError(
                "Missing workspace."
            )

        workspace = load_workspace(
            project_root=EWOODX_REPOSITORY_ROOT,
            workspace_name=workspace_name,
            layout=EWOODX_WORKSPACE_LAYOUT,
        )

        domain_manager = DomainManager(
            workspace=workspace,
        )

        for domain in domain_manager.list_domains():

            entry_manager = EntryManager(
                domain=domain,
            )

            entries = entry_manager.list_entries()

            if entries:
                return EntityManager(
                    workspace=workspace,
                    entry=entries[0],
                    index_schema=TIMBER_ENTITY_INDEX,
                )

        raise FileNotFoundError(
            "No managed entries found in workspace: "
            f"{workspace_name}"
        )

    def resolve_download(
        self,
        request: Dict[str, Any],
    ) -> Path:

        workspace_name = str(
            request.get(
                "workspace",
                "",
            )
        ).strip()

        entity_id = str(
            request.get(
                "entity_id",
                "",
            )
        ).strip()

        file_name = str(
            request.get(
                "file",
                "",
            )
        ).strip()

        if not entity_id:
            raise ValueError(
                "Missing entity_id."
            )

        if not file_name:
            raise ValueError(
                "Missing file."
            )

        entity_manager = (
            self._load_entity_manager(
                workspace_name
            )
        )

        entity = entity_manager.load_entity(
            entity_id
        )

        entity_root = entity.root.resolve()

        requested_path = (
            entity.root
            / file_name
        ).resolve()

        if (
            requested_path != entity_root
            and entity_root
            not in requested_path.parents
        ):
            raise ValueError(
                "Requested file is outside "
                "the entity directory."
            )

        if not requested_path.is_file():
            raise FileNotFoundError(
                "Entity file not found: "
                f"{file_name}"
            )

        return requested_path