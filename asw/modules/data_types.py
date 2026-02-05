"""Data types for ASW (Agentic Software Workflow) system.

This module contains unified data types for both application (app) and
infrastructure (io) workflows.
"""

from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from enum import Enum


# =============================================================================
# Common Types (shared between app and io)
# =============================================================================

class RetryCode(str, Enum):
    """Codes indicating different types of errors that may be retryable."""

    CLAUDE_CODE_ERROR = "claude_code_error"  # General Claude Code CLI error
    TIMEOUT_ERROR = "timeout_error"  # Command timed out
    EXECUTION_ERROR = "execution_error"  # Error during execution
    ERROR_DURING_EXECUTION = "error_during_execution"  # Agent encountered an error
    NONE = "none"  # No retry needed


class GitHubRetryCode(str, Enum):
    """Codes indicating different types of GitHub API errors that may be retryable."""

    NETWORK_ERROR = "network_error"        # Connection issues to api.github.com
    TIMEOUT_ERROR = "timeout_error"        # Request timed out
    RATE_LIMIT_ERROR = "rate_limit_error"  # GitHub rate limiting (403)
    SERVER_ERROR = "server_error"          # GitHub 5xx errors
    AUTH_ERROR = "auth_error"              # Authentication failed (not retryable)
    NOT_FOUND_ERROR = "not_found_error"    # Resource not found (not retryable)
    NONE = "none"                          # No retry needed


# Model set types for all workflows
ModelSet = Literal["base", "heavy"]


class GitHubUser(BaseModel):
    """GitHub user model."""

    id: Optional[str] = None  # Not always returned by GitHub API
    login: str
    name: Optional[str] = None
    is_bot: bool = Field(default=False, alias="is_bot")


class GitHubLabel(BaseModel):
    """GitHub label model."""

    id: str
    name: str
    color: str
    description: Optional[str] = None


class GitHubMilestone(BaseModel):
    """GitHub milestone model."""

    id: str
    number: int
    title: str
    description: Optional[str] = None
    state: str


class GitHubComment(BaseModel):
    """GitHub comment model."""

    id: str
    author: GitHubUser
    body: str
    created_at: datetime = Field(alias="createdAt")
    updated_at: Optional[datetime] = Field(
        None, alias="updatedAt"
    )  # Not always returned


class GitHubIssueListItem(BaseModel):
    """GitHub issue model for list responses (simplified)."""

    number: int
    title: str
    body: str
    labels: List[GitHubLabel] = []
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    class Config:
        populate_by_name = True


class GitHubIssue(BaseModel):
    """GitHub issue model."""

    number: int
    title: str
    body: str
    state: str
    author: GitHubUser
    assignees: List[GitHubUser] = []
    labels: List[GitHubLabel] = []
    milestone: Optional[GitHubMilestone] = None
    comments: List[GitHubComment] = []
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    closed_at: Optional[datetime] = Field(None, alias="closedAt")
    url: str

    class Config:
        populate_by_name = True


class AgentPromptResponse(BaseModel):
    """Claude Code agent response (common for both app and io)."""

    output: str
    success: bool
    session_id: Optional[str] = None
    retry_code: RetryCode = RetryCode.NONE
    duration_ms: Optional[int] = None  # Execution duration in milliseconds


class ClaudeCodeResultMessage(BaseModel):
    """Claude Code JSONL result message (last line)."""

    type: str
    subtype: str
    is_error: bool
    duration_ms: int
    duration_api_ms: int
    num_turns: int
    result: str
    session_id: str
    total_cost_usd: float


class TestResult(BaseModel):
    """Individual test result from test suite execution."""

    test_name: str
    passed: bool
    execution_command: str
    test_purpose: str
    error: Optional[str] = None


class E2ETestResult(BaseModel):
    """Individual E2E test result from browser automation."""

    test_name: str
    status: Literal["passed", "failed"]
    test_path: str  # Path to the test file for re-execution
    screenshots: List[str] = []
    error: Optional[str] = None

    @property
    def passed(self) -> bool:
        """Check if test passed."""
        return self.status == "passed"


class ReviewIssue(BaseModel):
    """Individual review issue found during verification."""

    review_issue_number: int
    screenshot_path: str  # Local file path to screenshot
    screenshot_url: Optional[str] = None  # Public URL after upload
    issue_description: str
    issue_resolution: str
    issue_severity: Literal["skippable", "tech_debt", "blocker"]


class ReviewResult(BaseModel):
    """Result from reviewing implementation against specification."""

    success: bool
    review_summary: str  # 2-4 sentences describing what was built
    review_issues: List[ReviewIssue] = []
    screenshots: List[str] = []  # Local file paths
    screenshot_urls: List[str] = []  # Public URLs after upload


class DocumentationResult(BaseModel):
    """Result from documentation generation workflow."""

    success: bool
    documentation_created: bool
    documentation_path: Optional[str] = None
    error_message: Optional[str] = None


# =============================================================================
# Application (App) Specific Types - formerly ADW
# =============================================================================

# Supported slash commands for app issue classification
AppIssueClassSlashCommand = Literal["/chore", "/bug", "/feature", "/patch"]

# App workflow types (all isolated now)
ASWAppWorkflow = Literal[
    "asw_app_plan_iso",  # Planning only
    "asw_app_patch_iso",  # Direct patch from issue
    "asw_app_build_iso",  # Building only (dependent workflow)
    "asw_app_test_iso",  # Testing only (dependent workflow)
    "asw_app_review_iso",  # Review only (dependent workflow)
    "asw_app_document_iso",  # Documentation only (dependent workflow)
    "asw_app_ship_iso",  # Ship/deployment workflow
    "asw_app_sdlc_ZTE_iso",  # Zero Touch Execution - full SDLC with auto-merge
    "asw_app_plan_build_iso",  # Plan + Build
    "asw_app_plan_build_test_iso",  # Plan + Build + Test
    "asw_app_plan_build_test_review_iso",  # Plan + Build + Test + Review
    "asw_app_plan_build_document_iso",  # Plan + Build + Document
    "asw_app_plan_build_review_iso",  # Plan + Build + Review
    "asw_app_sdlc_iso",  # Complete SDLC: Plan + Build + Test + Review + Document
]

# All slash commands used in the app system
AppSlashCommand = Literal[
    # Issue classification commands
    "/chore",
    "/bug",
    "/feature",
    # App workflow commands
    "/classify_issue",
    "/classify_asw_app",
    "/generate_branch_name",
    "/commit",
    "/pull_request",
    "/implement",
    "/test",
    "/resolve_failed_test",
    "/test_e2e",
    "/resolve_failed_e2e_test",
    "/review",
    "/patch",
    "/document",
    "/track_agentic_kpis",
    # Installation/setup commands
    "/install_worktree",
]


class AppAgentPromptRequest(BaseModel):
    """Claude Code agent prompt configuration for app workflows."""

    prompt: str
    asw_id: str  # Unified ID field
    agent_name: str = "ops"
    model: Literal["sonnet", "opus"] = "sonnet"
    dangerously_skip_permissions: bool = False
    output_file: str
    working_dir: Optional[str] = None
    cache_enabled: bool = True  # Enable response caching
    cache_ttl_seconds: int = 172800  # 48 hours default


class AppAgentTemplateRequest(BaseModel):
    """Claude Code agent template execution request for app workflows."""

    agent_name: str
    slash_command: AppSlashCommand
    args: List[str]
    asw_id: str  # Unified ID field
    model: Literal["sonnet", "opus"] = "sonnet"
    working_dir: Optional[str] = None
    cache_enabled: bool = True  # Enable response caching
    cache_ttl_seconds: int = 172800  # 48 hours default


class ASWAppStateData(BaseModel):
    """Minimal persistent state for app workflow.

    Stored in agents/{asw_id}/asw_app_state.json
    Contains only essential identifiers to connect workflow steps.
    """

    asw_id: str
    issue_number: Optional[str] = None
    branch_name: Optional[str] = None
    plan_file: Optional[str] = None
    issue_class: Optional[AppIssueClassSlashCommand] = None
    worktree_path: Optional[str] = None
    backend_port: Optional[int] = None
    frontend_port: Optional[int] = None
    model_set: Optional[ModelSet] = "base"  # Default to "base" model set
    all_asw_ids: List[str] = Field(default_factory=list)

    # Ship workflow metadata
    shipped_at: Optional[str] = None  # ISO timestamp of successful ship
    merge_commit: Optional[str] = None  # Commit hash of merge
    pr_number: Optional[str] = None  # PR number that was merged


class ASWAppExtractionResult(BaseModel):
    """Result from extracting app workflow information from text."""

    workflow_command: Optional[str] = None  # e.g., "asw_app_plan_iso" (without slash)
    asw_id: Optional[str] = None  # 8-character ASW ID
    model_set: Optional[ModelSet] = "base"  # Model set to use, defaults to "base"

    @property
    def has_workflow(self) -> bool:
        """Check if a workflow command was extracted."""
        return self.workflow_command is not None


# =============================================================================
# Infrastructure (IO) Specific Types - formerly IPE
# =============================================================================

# Supported slash commands for io issue classification
IOIssueClassSlashCommand = Literal["/asw_io_chore", "/asw_io_bug", "/asw_io_feature"]

# IO workflow types (all isolated)
ASWIOWorkflow = Literal[
    "asw_io_plan_iso",  # Planning only
    "asw_io_build_iso",  # Building infrastructure
    "asw_io_test_iso",  # Testing infrastructure
    "asw_io_review_iso",  # Review infrastructure changes
    "asw_io_document_iso",  # Documentation
    "asw_io_ship_iso",  # Ship/deployment workflow
    "asw_io_build_ami_iso",  # Build AMI workflow
    "asw_io_patch_iso",  # Patch workflow
    "asw_io_sdlc_zte_iso",  # Zero Touch Execution workflow
    "asw_io_plan_build_iso",
    "asw_io_plan_build_test_iso",
    "asw_io_plan_build_test_review_iso",
    "asw_io_plan_build_document_iso",
    "asw_io_plan_build_review_iso",
    "asw_io_sdlc_iso",
]

# All slash commands used in the IO system
IOSlashCommand = Literal[
    # Issue classification commands
    "/asw_io_chore",
    "/asw_io_bug",
    "/asw_io_feature",
    # IO workflow commands
    "/asw_io_plan",
    "/asw_io_build",
    "/asw_io_test",
    "/resolve_failed_test",
    "/asw_io_review",
    "/asw_io_document",
    "/asw_io_patch",
    "/classify_issue",
    "/classify_asw_io",
    "/generate_branch_name",
    "/asw_io_commit",
    "/asw_io_pull_request",
    "/asw_io_track_agentic_kpis",
    # Installation/setup commands
    "/install_worktree",
]


class IOAgentPromptRequest(BaseModel):
    """Claude Code agent prompt configuration for IO workflows."""

    prompt: str
    asw_id: str  # Unified ID field
    agent_name: str = "ops"
    model: Literal["sonnet", "opus"] = "sonnet"
    dangerously_skip_permissions: bool = False
    output_file: str
    working_dir: Optional[str] = None


class IOAgentTemplateRequest(BaseModel):
    """Claude Code agent template execution request for IO workflows."""

    agent_name: str
    slash_command: IOSlashCommand
    args: List[str]
    asw_id: str  # Unified ID field
    model: Literal["sonnet", "opus"] = "sonnet"
    working_dir: Optional[str] = None


class ASWIOStateData(BaseModel):
    """Minimal persistent state for IO workflow.

    Stored in agents/{asw_id}/asw_io_state.json
    Contains only essential identifiers to connect infrastructure workflow steps.
    """

    asw_id: str
    issue_number: Optional[str] = None
    branch_name: Optional[str] = None
    spec_file: Optional[str] = None  # Infrastructure spec file
    issue_class: Optional[IOIssueClassSlashCommand] = None
    worktree_path: Optional[str] = None
    environment: Optional[str] = "sandbox"  # Infrastructure environment (dev/staging/prod/sandbox)
    terraform_dir: Optional[str] = None  # Terraform directory path (default: io/terraform)
    model_set: Optional[ModelSet] = "base"  # Default to "base" model set
    all_asw_ids: List[str] = Field(default_factory=list)


class ASWIOExtractionResult(BaseModel):
    """Result from extracting IO workflow information from text."""

    workflow_command: Optional[str] = None  # e.g., "asw_io_plan_iso" (without slash)
    asw_id: Optional[str] = None  # 8-character ASW ID
    model_set: Optional[ModelSet] = "base"  # Model set to use, defaults to "base"

    @property
    def has_workflow(self) -> bool:
        """Check if a workflow command was extracted."""
        return self.workflow_command is not None


# =============================================================================
# Legacy Aliases (for backward compatibility during migration)
# =============================================================================

# App aliases (formerly ADW)
ADWStateData = ASWAppStateData
ADWExtractionResult = ASWAppExtractionResult
IssueClassSlashCommand = AppIssueClassSlashCommand
ADWWorkflow = ASWAppWorkflow
SlashCommand = AppSlashCommand
AgentPromptRequest = AppAgentPromptRequest
AgentTemplateRequest = AppAgentTemplateRequest

# IO aliases (formerly IPE)
IPEStateData = ASWIOStateData
IPEExtractionResult = ASWIOExtractionResult
IPEWorkflow = ASWIOWorkflow
