"""State management for IPE composable architecture.

Provides persistent state management via file storage and
transient state passing between scripts via stdin/stdout.
"""

import json
import os
import sys
import logging
from typing import Dict, Any, Optional
from .ipe_data_types import IPEStateData


class IPEState:
    """Container for IPE workflow state with file persistence."""

    STATE_FILENAME = "ipe_state.json"

    def __init__(self, ipe_id: str):
        """Initialize IPEState with a required IPE ID.

        Args:
            ipe_id: The IPE ID for this state (required)
        """
        if not ipe_id:
            raise ValueError("ipe_id is required for IPEState")

        self.ipe_id = ipe_id
        # Start with minimal state
        self.data: Dict[str, Any] = {"ipe_id": self.ipe_id}
        self.logger = logging.getLogger(__name__)

    def update(self, **kwargs):
        """Update state with new key-value pairs."""
        # Filter to only our core fields
        core_fields = {"ipe_id", "issue_number", "branch_name", "spec_file", "issue_class", "worktree_path", "environment", "terraform_dir", "model_set", "all_ipes"}
        for key, value in kwargs.items():
            if key in core_fields:
                self.data[key] = value

    def get(self, key: str, default=None):
        """Get value from state by key."""
        return self.data.get(key, default)

    def append_ipe_id(self, ipe_id: str):
        """Append an IPE ID to the all_ipes list if not already present."""
        all_ipes = self.data.get("all_ipes", [])
        if ipe_id not in all_ipes:
            all_ipes.append(ipe_id)
            self.data["all_ipes"] = all_ipes

    def get_working_directory(self) -> str:
        """Get the working directory for this IPE instance.

        Returns worktree_path if set (for isolated workflows),
        otherwise returns the main repo path.
        """
        worktree_path = self.data.get("worktree_path")
        if worktree_path:
            return worktree_path

        # Return main repo path (parent of ipe directory)
        return os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

    def get_state_path(self) -> str:
        """Get path to state file."""
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        return os.path.join(project_root, "agents", self.ipe_id, self.STATE_FILENAME)

    def save(self, workflow_step: Optional[str] = None) -> None:
        """Save state to file in agents/{ipe_id}/ipe_state.json."""
        state_path = self.get_state_path()
        os.makedirs(os.path.dirname(state_path), exist_ok=True)

        # Create IPEStateData for validation
        state_data = IPEStateData(
            ipe_id=self.data.get("ipe_id"),
            issue_number=self.data.get("issue_number"),
            branch_name=self.data.get("branch_name"),
            spec_file=self.data.get("spec_file"),
            issue_class=self.data.get("issue_class"),
            worktree_path=self.data.get("worktree_path"),
            environment=self.data.get("environment", "sandbox"),
            terraform_dir=self.data.get("terraform_dir"),
            model_set=self.data.get("model_set", "base"),
            all_ipes=self.data.get("all_ipes", []),
        )

        # Save as JSON
        with open(state_path, "w") as f:
            json.dump(state_data.model_dump(), f, indent=2)

        self.logger.info(f"Saved state to {state_path}")
        if workflow_step:
            self.logger.info(f"State updated by: {workflow_step}")

    @classmethod
    def load(
        cls, ipe_id: str, logger: Optional[logging.Logger] = None
    ) -> Optional["IPEState"]:
        """Load state from file if it exists."""
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        state_path = os.path.join(project_root, "agents", ipe_id, cls.STATE_FILENAME)

        if not os.path.exists(state_path):
            return None

        try:
            with open(state_path, "r") as f:
                data = json.load(f)

            # Validate with IPEStateData
            state_data = IPEStateData(**data)

            # Create IPEState instance
            state = cls(state_data.ipe_id)
            state.data = state_data.model_dump()

            if logger:
                logger.info(f"🔍 Found existing state from {state_path}")
                logger.info(f"State: {json.dumps(state_data.model_dump(), indent=2)}")

            return state
        except Exception as e:
            if logger:
                logger.error(f"Failed to load state from {state_path}: {e}")
            return None

    @classmethod
    def from_stdin(cls) -> Optional["IPEState"]:
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
            ipe_id = data.get("ipe_id")
            if not ipe_id:
                return None  # No valid state without ipe_id
            state = cls(ipe_id)
            state.data = data
            return state
        except (json.JSONDecodeError, EOFError):
            return None

    def to_stdout(self):
        """Write state to stdout as JSON (for piping to next script)."""
        # Only output core fields
        output_data = {
            "ipe_id": self.data.get("ipe_id"),
            "issue_number": self.data.get("issue_number"),
            "branch_name": self.data.get("branch_name"),
            "spec_file": self.data.get("spec_file"),
            "issue_class": self.data.get("issue_class"),
            "worktree_path": self.data.get("worktree_path"),
            "environment": self.data.get("environment", "dev"),
            "terraform_dir": self.data.get("terraform_dir"),
            "all_ipes": self.data.get("all_ipes", []),
        }
        print(json.dumps(output_data, indent=2))
