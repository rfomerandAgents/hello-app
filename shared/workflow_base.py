"""Base classes for workflow implementations.

Provides abstract base classes that can be extended by ADW and IDW implementations.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Optional, List, Dict, Any
import logging


class IsolatedWorkflow(ABC):
    """Abstract base class for isolated workflows.

    This class defines the interface for workflow implementations
    that operate in isolated git worktrees (ADW, IDW, etc.).
    """

    def __init__(self, issue_number: str, workflow_id: str):
        """Initialize workflow instance.

        Args:
            issue_number: GitHub issue number
            workflow_id: Unique workflow identifier
        """
        self.issue_number = issue_number
        self.workflow_id = workflow_id
        self.logger = self._setup_logger()
        self.state = self._load_state()

    @abstractmethod
    def setup_environment(self, worktree_path: str) -> Tuple[bool, Optional[str]]:
        """Setup workflow-specific environment in worktree.

        Args:
            worktree_path: Path to the git worktree

        Returns:
            Tuple of (success, error_message)
        """
        pass

    @abstractmethod
    def run_validation_tests(self, worktree_path: str) -> List[Dict[str, Any]]:
        """Run workflow-specific validation tests.

        Args:
            worktree_path: Path to the git worktree

        Returns:
            List of test results
        """
        pass

    @abstractmethod
    def review_changes(self, worktree_path: str, spec_file: str) -> Dict[str, Any]:
        """Review workflow-specific changes against spec.

        Args:
            worktree_path: Path to the git worktree
            spec_file: Path to the specification file

        Returns:
            Review results
        """
        pass

    @abstractmethod
    def prepare_for_ship(self, worktree_path: str) -> Tuple[bool, Optional[str]]:
        """Prepare changes for shipping (merging/applying).

        Args:
            worktree_path: Path to the git worktree

        Returns:
            Tuple of (success, error_message)
        """
        pass

    def _setup_logger(self) -> logging.Logger:
        """Setup logger for workflow."""
        from shared.utils import setup_logger
        return setup_logger(self.workflow_id, self.__class__.__name__)

    def _load_state(self):
        """Load workflow state."""
        from shared.state import WorkflowState
        return WorkflowState.load(self.workflow_id, self.logger)


class WorkflowPhase(ABC):
    """Abstract base class for workflow phases (plan, build, test, etc.)."""

    def __init__(self, workflow_id: str, issue_number: str):
        """Initialize workflow phase.

        Args:
            workflow_id: Unique workflow identifier
            issue_number: GitHub issue number
        """
        self.workflow_id = workflow_id
        self.issue_number = issue_number
        self.logger = self._setup_logger()

    @abstractmethod
    def execute(self) -> Tuple[bool, Optional[str]]:
        """Execute this workflow phase.

        Returns:
            Tuple of (success, error_message)
        """
        pass

    def _setup_logger(self) -> logging.Logger:
        """Setup logger for this phase."""
        from shared.utils import setup_logger
        phase_name = self.__class__.__name__
        return setup_logger(self.workflow_id, phase_name)
