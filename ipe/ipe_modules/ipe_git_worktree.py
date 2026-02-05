"""Git worktree utilities for IPE deployments."""

import subprocess
import logging
import os
from pathlib import Path
from typing import Optional, Tuple


def get_git_root() -> Path:
    """Get git repository root directory.

    Returns:
        Path to git root directory
    """
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True
    )
    return Path(result.stdout.strip())


def ensure_worktree_gitignore():
    """Ensure trees/ directory is in .gitignore."""
    git_root = get_git_root()
    gitignore_path = git_root / ".gitignore"

    gitignore_entry = "trees/"

    if gitignore_path.exists():
        with open(gitignore_path, "r") as f:
            if gitignore_entry in f.read():
                return  # Already present

    with open(gitignore_path, "a") as f:
        f.write(f"\n{gitignore_entry}\n")


def create_worktree(
    operation_name: str,
    branch: str,
    logger: logging.Logger
) -> str:
    """Create a git worktree for isolated deployment.

    Args:
        operation_name: Name of the operation (for worktree directory)
        branch: Git branch to checkout
        logger: Logger instance

    Returns:
        Path to created worktree directory
    """
    git_root = get_git_root()
    worktree_dir = git_root / "trees" / operation_name

    # Create trees directory if needed
    (git_root / "trees").mkdir(exist_ok=True)

    # Create worktree
    logger.info(f"Creating worktree for branch '{branch}'...")
    subprocess.run(
        ["git", "worktree", "add", str(worktree_dir), branch],
        check=True,
        capture_output=True
    )

    return str(worktree_dir)


def cleanup_worktree(operation_name: str, logger: logging.Logger):
    """Clean up a git worktree.

    Args:
        operation_name: Name of the operation (worktree directory name)
        logger: Logger instance
    """
    git_root = get_git_root()
    worktree_dir = git_root / "trees" / operation_name

    if not worktree_dir.exists():
        return

    logger.info(f"Cleaning up worktree: {worktree_dir}")

    # Remove worktree
    subprocess.run(
        ["git", "worktree", "remove", str(worktree_dir), "--force"],
        capture_output=True
    )

    # Prune worktree references
    subprocess.run(
        ["git", "worktree", "prune"],
        capture_output=True
    )


def is_in_worktree() -> Tuple[bool, Optional[Path]]:
    """Detect if currently running inside a git worktree.

    Returns:
        Tuple of (is_in_worktree, worktree_path)
        - is_in_worktree: True if current directory is in a worktree
        - worktree_path: Path to the worktree root, or None if not in worktree
    """
    try:
        # Get current working directory
        cwd = Path(os.getcwd()).resolve()

        # Execute git worktree list to get all worktrees
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            capture_output=True,
            text=True,
            check=True
        )

        # Parse porcelain output
        worktrees = []
        current_worktree = {}

        for line in result.stdout.strip().split('\n'):
            if line.startswith('worktree '):
                if current_worktree:
                    worktrees.append(current_worktree)
                current_worktree = {'path': Path(line.split(' ', 1)[1]).resolve()}
            elif line.startswith('branch '):
                current_worktree['branch'] = line.split(' ', 1)[1]

        # Add last worktree
        if current_worktree:
            worktrees.append(current_worktree)

        # Check if current directory is in any worktree
        for wt in worktrees:
            wt_path = wt['path']
            try:
                # Check if cwd is the worktree or a subdirectory of it
                cwd.relative_to(wt_path)
                return True, wt_path
            except ValueError:
                # Not relative to this worktree
                continue

        return False, None

    except subprocess.CalledProcessError:
        # Not in a git repository or git command failed
        return False, None
    except Exception:
        # Any other error
        return False, None


def get_current_worktree_path() -> Optional[Path]:
    """Get the path to the current worktree if running inside one.

    Returns:
        Path to current worktree root, or None if not in a worktree
    """
    is_worktree, worktree_path = is_in_worktree()
    return worktree_path if is_worktree else None


def is_ipe_workflow_worktree(path: Path) -> bool:
    """Check if a path is an IPE workflow worktree.

    IPE workflow worktrees are located in `.worktrees/` directory
    (as opposed to `trees/` for standalone ipe_deploy.py worktrees).

    Args:
        path: Path to check

    Returns:
        True if path is an IPE workflow worktree, False otherwise
    """
    try:
        path_str = str(path.resolve())

        # Check if path contains .worktrees/ (IPE pattern)
        if '/.worktrees/' in path_str or '\\.worktrees\\' in path_str:
            # Verify terraform directory exists
            terraform_dir = path / "io" / "terraform"
            return terraform_dir.exists()

        return False

    except Exception:
        return False
