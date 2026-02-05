"""State management for ASW composable architecture.

Provides persistent state management via file storage and
transient state passing between scripts via stdin/stdout.

Supports both application (app) and infrastructure (io) workflows.
"""

import json
import os
import sys
import logging
from typing import Dict, Any, Optional
from .data_types import ASWAppStateData, ASWIOStateData


class ASWAppState:
    """Container for ASW application workflow state with file persistence.

    Replaces the former ADWState class.
    """

    STATE_FILENAME = "asw_app_state.json"

    def __init__(self, asw_id: str):
        """Initialize ASWAppState with a required ASW ID.

        Args:
            asw_id: The ASW ID for this state (required)
        """
        if not asw_id:
            raise ValueError("asw_id is required for ASWAppState")

        self.asw_id = asw_id
        # Start with minimal state
        self.data: Dict[str, Any] = {"asw_id": self.asw_id}
        self.logger = logging.getLogger(__name__)

    def update(self, **kwargs):
        """Update state with new key-value pairs."""
        # Filter to only our core fields
        core_fields = {
            "asw_id", "issue_number", "branch_name", "plan_file", "issue_class",
            "worktree_path", "backend_port", "frontend_port", "model_set", "all_asw_ids",
            "shipped_at", "merge_commit", "pr_number",  # Ship workflow metadata
        }
        for key, value in kwargs.items():
            if key in core_fields:
                self.data[key] = value

    def get(self, key: str, default=None):
        """Get value from state by key."""
        return self.data.get(key, default)

    def append_asw_id(self, asw_id: str):
        """Append an ASW ID to the all_asw_ids list if not already present."""
        all_asw_ids = self.data.get("all_asw_ids", [])
        if asw_id not in all_asw_ids:
            all_asw_ids.append(asw_id)
            self.data["all_asw_ids"] = all_asw_ids

    def get_working_directory(self) -> str:
        """Get the working directory for this ASW instance.

        Returns worktree_path if set (for isolated workflows),
        otherwise returns the main repo path.
        """
        worktree_path = self.data.get("worktree_path")
        if worktree_path:
            return worktree_path

        # Return main repo path (parent of asw directory)
        return os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

    def get_state_path(self) -> str:
        """Get path to state file."""
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        return os.path.join(project_root, "agents", self.asw_id, self.STATE_FILENAME)

    def save(self, workflow_step: Optional[str] = None) -> None:
        """Save state to file in agents/{asw_id}/asw_app_state.json."""
        state_path = self.get_state_path()
        os.makedirs(os.path.dirname(state_path), exist_ok=True)

        # Create ASWAppStateData for validation
        state_data = ASWAppStateData(
            asw_id=self.data.get("asw_id"),
            issue_number=self.data.get("issue_number"),
            branch_name=self.data.get("branch_name"),
            plan_file=self.data.get("plan_file"),
            issue_class=self.data.get("issue_class"),
            worktree_path=self.data.get("worktree_path"),
            backend_port=self.data.get("backend_port"),
            frontend_port=self.data.get("frontend_port"),
            model_set=self.data.get("model_set", "base"),
            all_asw_ids=self.data.get("all_asw_ids", []),
            # Ship workflow metadata
            shipped_at=self.data.get("shipped_at"),
            merge_commit=self.data.get("merge_commit"),
            pr_number=self.data.get("pr_number"),
        )

        # Save as JSON
        with open(state_path, "w") as f:
            json.dump(state_data.model_dump(), f, indent=2)

        self.logger.info(f"Saved state to {state_path}")
        if workflow_step:
            self.logger.info(f"State updated by: {workflow_step}")

    @classmethod
    def load(
        cls, asw_id: str, logger: Optional[logging.Logger] = None
    ) -> Optional["ASWAppState"]:
        """Load state from file if it exists."""
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        state_path = os.path.join(project_root, "agents", asw_id, cls.STATE_FILENAME)

        if not os.path.exists(state_path):
            return None

        try:
            with open(state_path, "r") as f:
                data = json.load(f)

            # Validate with ASWAppStateData
            state_data = ASWAppStateData(**data)

            # Create ASWAppState instance
            state = cls(state_data.asw_id)
            state.data = state_data.model_dump()

            if logger:
                logger.info(f"Found existing state from {state_path}")
                logger.info(f"State: {json.dumps(state_data.model_dump(), indent=2)}")

            return state
        except Exception as e:
            if logger:
                logger.error(f"Failed to load state from {state_path}: {e}")
            return None

    @classmethod
    def from_stdin(cls) -> Optional["ASWAppState"]:
        """Read state from stdin if available (for piped input).

        Returns None if no piped input is available (stdin is a tty).
        """
        if sys.stdin.isatty():
            return None
        try:
            input_data = sys.stdin.read()
            if not input_data.strip():
                return None
            data = json.loads(input_data)
            asw_id = data.get("asw_id")
            if not asw_id:
                return None  # No valid state without asw_id
            state = cls(asw_id)
            state.data = data
            return state
        except (json.JSONDecodeError, EOFError):
            return None

    def to_stdout(self):
        """Write state to stdout as JSON (for piping to next script)."""
        # Only output core fields
        output_data = {
            "asw_id": self.data.get("asw_id"),
            "issue_number": self.data.get("issue_number"),
            "branch_name": self.data.get("branch_name"),
            "plan_file": self.data.get("plan_file"),
            "issue_class": self.data.get("issue_class"),
            "worktree_path": self.data.get("worktree_path"),
            "backend_port": self.data.get("backend_port"),
            "frontend_port": self.data.get("frontend_port"),
            "all_asw_ids": self.data.get("all_asw_ids", []),
        }
        print(json.dumps(output_data, indent=2))


class ASWIOState:
    """Container for ASW infrastructure workflow state with file persistence.

    Replaces the former IPEState class.
    """

    STATE_FILENAME = "asw_io_state.json"

    def __init__(self, asw_id: str):
        """Initialize ASWIOState with a required ASW ID.

        Args:
            asw_id: The ASW ID for this state (required)
        """
        if not asw_id:
            raise ValueError("asw_id is required for ASWIOState")

        self.asw_id = asw_id
        # Start with minimal state
        self.data: Dict[str, Any] = {"asw_id": self.asw_id}
        self.logger = logging.getLogger(__name__)

    def update(self, **kwargs):
        """Update state with new key-value pairs."""
        # Filter to only our core fields
        core_fields = {
            "asw_id", "issue_number", "branch_name", "spec_file", "issue_class",
            "worktree_path", "environment", "terraform_dir", "model_set", "all_asw_ids"
        }
        for key, value in kwargs.items():
            if key in core_fields:
                self.data[key] = value

    def get(self, key: str, default=None):
        """Get value from state by key."""
        return self.data.get(key, default)

    def append_asw_id(self, asw_id: str):
        """Append an ASW ID to the all_asw_ids list if not already present."""
        all_asw_ids = self.data.get("all_asw_ids", [])
        if asw_id not in all_asw_ids:
            all_asw_ids.append(asw_id)
            self.data["all_asw_ids"] = all_asw_ids

    def get_working_directory(self) -> str:
        """Get the working directory for this ASW instance.

        Returns worktree_path if set (for isolated workflows),
        otherwise returns the main repo path.
        """
        worktree_path = self.data.get("worktree_path")
        if worktree_path:
            return worktree_path

        # Return main repo path (parent of asw directory)
        return os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

    def get_state_path(self) -> str:
        """Get path to state file."""
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        return os.path.join(project_root, "agents", self.asw_id, self.STATE_FILENAME)

    def save(self, workflow_step: Optional[str] = None) -> None:
        """Save state to file in agents/{asw_id}/asw_io_state.json."""
        state_path = self.get_state_path()
        os.makedirs(os.path.dirname(state_path), exist_ok=True)

        # Create ASWIOStateData for validation
        state_data = ASWIOStateData(
            asw_id=self.data.get("asw_id"),
            issue_number=self.data.get("issue_number"),
            branch_name=self.data.get("branch_name"),
            spec_file=self.data.get("spec_file"),
            issue_class=self.data.get("issue_class"),
            worktree_path=self.data.get("worktree_path"),
            environment=self.data.get("environment", "sandbox"),
            terraform_dir=self.data.get("terraform_dir"),
            model_set=self.data.get("model_set", "base"),
            all_asw_ids=self.data.get("all_asw_ids", []),
        )

        # Save as JSON
        with open(state_path, "w") as f:
            json.dump(state_data.model_dump(), f, indent=2)

        self.logger.info(f"Saved state to {state_path}")
        if workflow_step:
            self.logger.info(f"State updated by: {workflow_step}")

    @classmethod
    def load(
        cls, asw_id: str, logger: Optional[logging.Logger] = None
    ) -> Optional["ASWIOState"]:
        """Load state from file if it exists."""
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        state_path = os.path.join(project_root, "agents", asw_id, cls.STATE_FILENAME)

        if not os.path.exists(state_path):
            return None

        try:
            with open(state_path, "r") as f:
                data = json.load(f)

            # Validate with ASWIOStateData
            state_data = ASWIOStateData(**data)

            # Create ASWIOState instance
            state = cls(state_data.asw_id)
            state.data = state_data.model_dump()

            if logger:
                logger.info(f"Found existing state from {state_path}")
                logger.info(f"State: {json.dumps(state_data.model_dump(), indent=2)}")

            return state
        except Exception as e:
            if logger:
                logger.error(f"Failed to load state from {state_path}: {e}")
            return None

    @classmethod
    def from_stdin(cls) -> Optional["ASWIOState"]:
        """Read state from stdin if available (for piped input).

        Returns None if no piped input is available (stdin is a tty).
        """
        if sys.stdin.isatty():
            return None
        try:
            input_data = sys.stdin.read()
            if not input_data.strip():
                return None
            data = json.loads(input_data)
            asw_id = data.get("asw_id")
            if not asw_id:
                return None  # No valid state without asw_id
            state = cls(asw_id)
            state.data = data
            return state
        except (json.JSONDecodeError, EOFError):
            return None

    def to_stdout(self):
        """Write state to stdout as JSON (for piping to next script)."""
        # Only output core fields
        output_data = {
            "asw_id": self.data.get("asw_id"),
            "issue_number": self.data.get("issue_number"),
            "branch_name": self.data.get("branch_name"),
            "spec_file": self.data.get("spec_file"),
            "issue_class": self.data.get("issue_class"),
            "worktree_path": self.data.get("worktree_path"),
            "environment": self.data.get("environment", "dev"),
            "terraform_dir": self.data.get("terraform_dir"),
            "all_asw_ids": self.data.get("all_asw_ids", []),
        }
        print(json.dumps(output_data, indent=2))


# =============================================================================
# Legacy Aliases (for backward compatibility during migration)
# =============================================================================

# Create aliases for backward compatibility
ADWState = ASWAppState
IPEState = ASWIOState
