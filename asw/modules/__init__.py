"""
ASW - Agentic Software Workflow unified modules.

This package contains the unified modules for both application (app) and
infrastructure (io) workflows. The module supports:

- asw/app/ workflows (formerly adws/) - Application development workflows
- asw/io/ workflows (formerly ipe/) - Infrastructure platform workflows

State Management:
- ASWAppState: State for application workflows (replaces ADWState)
- ASWIOState: State for infrastructure workflows (replaces IPEState)

ID Generation:
- make_asw_app_id(): Generate ID for application workflows (replaces make_adw_id)
- make_asw_io_id(): Generate ID for infrastructure workflows (replaces make_ipe_id)
"""

# State management
from .state import ASWAppState, ASWIOState

# Data types
from .data_types import (
    # Common types
    RetryCode,
    GitHubRetryCode,
    ModelSet,
    GitHubUser,
    GitHubLabel,
    GitHubMilestone,
    GitHubComment,
    GitHubIssueListItem,
    GitHubIssue,
    AgentPromptResponse,
    ClaudeCodeResultMessage,
    TestResult,
    E2ETestResult,
    ReviewIssue,
    ReviewResult,
    DocumentationResult,
    # App-specific types
    ASWAppStateData,
    ASWAppExtractionResult,
    AppIssueClassSlashCommand,
    ASWAppWorkflow,
    AppSlashCommand,
    AppAgentPromptRequest,
    AppAgentTemplateRequest,
    # IO-specific types
    ASWIOStateData,
    ASWIOExtractionResult,
    IOIssueClassSlashCommand,
    ASWIOWorkflow,
    IOSlashCommand,
    IOAgentPromptRequest,
    IOAgentTemplateRequest,
)

# Core operations - agent
from .agent import execute_template

# GitHub operations
from .github import (
    fetch_issue,
    make_issue_comment,
    get_repo_url,
    extract_repo_path,
    ASW_APP_BOT_IDENTIFIER,
    ASW_IO_BOT_IDENTIFIER,
)

# Git operations
from .git_ops import (
    commit_changes,
    finalize_git_operations,
    get_current_branch,
    create_branch,
)

# Workflow operations
from .workflow_ops import (
    # App workflow functions
    ensure_asw_app_id,
    # IO workflow functions
    ensure_asw_io_id,
    # Common functions
    classify_issue,
    build_plan,
    implement_plan,
    generate_branch_name,
    create_commit,
    format_issue_message,
    # App-specific
    extract_asw_app_info,
    AVAILABLE_ASW_APP_WORKFLOWS,
    # IO-specific
    extract_asw_io_info,
    AVAILABLE_ASW_IO_WORKFLOWS,
    # Agent constants
    AGENT_PLANNER,
    AGENT_BUILDER,
    AGENT_VALIDATOR,
    AGENT_IMPLEMENTOR,
    AGENT_CLASSIFIER,
    AGENT_BRANCH_GENERATOR,
    AGENT_PR_CREATOR,
)

# Worktree operations
from .worktree_ops import (
    create_worktree,
    validate_worktree,
)

# R2 uploader for screenshots
from .r2_uploader import R2Uploader

# Utility functions
from .utils import (
    setup_logger,
    get_logger,
    check_env_vars,
    make_asw_app_id,
    make_asw_io_id,
    parse_json,
    get_safe_subprocess_env,
    parse_cache_flag,
)

__all__ = [
    # State
    'ASWAppState',
    'ASWIOState',
    # Data types - common
    'RetryCode',
    'GitHubRetryCode',
    'ModelSet',
    'GitHubUser',
    'GitHubLabel',
    'GitHubMilestone',
    'GitHubComment',
    'GitHubIssueListItem',
    'GitHubIssue',
    'AgentPromptResponse',
    'ClaudeCodeResultMessage',
    'TestResult',
    'E2ETestResult',
    'ReviewIssue',
    'ReviewResult',
    'DocumentationResult',
    # Data types - app
    'ASWAppStateData',
    'ASWAppExtractionResult',
    'AppIssueClassSlashCommand',
    'ASWAppWorkflow',
    'AppSlashCommand',
    'AppAgentPromptRequest',
    'AppAgentTemplateRequest',
    # Data types - io
    'ASWIOStateData',
    'ASWIOExtractionResult',
    'IOIssueClassSlashCommand',
    'ASWIOWorkflow',
    'IOSlashCommand',
    'IOAgentPromptRequest',
    'IOAgentTemplateRequest',
    # Agent
    'execute_template',
    # GitHub
    'fetch_issue',
    'make_issue_comment',
    'get_repo_url',
    'extract_repo_path',
    'ASW_APP_BOT_IDENTIFIER',
    'ASW_IO_BOT_IDENTIFIER',
    # Git ops
    'commit_changes',
    'finalize_git_operations',
    'get_current_branch',
    'create_branch',
    # Workflow ops
    'ensure_asw_app_id',
    'ensure_asw_io_id',
    'classify_issue',
    'build_plan',
    'implement_plan',
    'generate_branch_name',
    'create_commit',
    'format_issue_message',
    'extract_asw_app_info',
    'extract_asw_io_info',
    'AVAILABLE_ASW_APP_WORKFLOWS',
    'AVAILABLE_ASW_IO_WORKFLOWS',
    'AGENT_PLANNER',
    'AGENT_BUILDER',
    'AGENT_VALIDATOR',
    'AGENT_IMPLEMENTOR',
    'AGENT_CLASSIFIER',
    'AGENT_BRANCH_GENERATOR',
    'AGENT_PR_CREATOR',
    # Worktree ops
    'create_worktree',
    'validate_worktree',
    # R2 uploader
    'R2Uploader',
    # Utils
    'setup_logger',
    'get_logger',
    'check_env_vars',
    'make_asw_app_id',
    'make_asw_io_id',
    'parse_json',
    'get_safe_subprocess_env',
    'parse_cache_flag',
]
