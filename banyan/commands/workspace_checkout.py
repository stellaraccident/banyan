import logging
from pathlib import Path

from banyan.repo import BanyanWorkspace, WorkspaceMount
from banyan.support.errors import CommandError


logger = logging.getLogger(__name__)


def checkout(ws: BanyanWorkspace, *local_paths: Path | str):
    logger.debug("EXEC workspace checkout(%s): %r", ws.local_path, local_paths)
    parent_gr = ws.depot.git_repo
    current_worktrees = parent_gr.worktree_list()
    mounts: list[WorkspaceMount]
    if not local_paths:
        mounts = list(ws.mounts.values())
    else:
        mounts = []
        for local_path in local_paths:
            mount = ws.mounts.get(local_path)
            if mount is None:
                raise CommandError(
                    f"Unknown checkout path `{local_path}`: Available\n  "
                    f"{'\n  '.join(ws.mount_local_path_names)}"
                )
            mounts.append(mount)

    logger.debug("Checking out %d mounts: %r", len(mounts), mounts)
    for mount in mounts:
        if mount.is_populated(current_worktrees):
            logger.debug(
                "Skipping checkout of %s (already populated)", mount.local_path
            )
        branch_name = mount.branch_name
        logger.debug(
            "Checking out mount %s using branch %s", mount.local_path, branch_name
        )
