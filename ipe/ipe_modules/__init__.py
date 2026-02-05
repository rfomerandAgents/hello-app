"""
IPE Modules - Infrastructure Platform Engineer workflow modules

This package contains all the core modules for the IPE system.
"""

# State management
from .ipe_state import IPEState
from .ipe_data_types import IPEStateData

# Core operations
from .ipe_agent import execute_template
from .ipe_github import (
    fetch_issue,
    make_issue_comment,
    get_repo_url,
    extract_repo_path,
)
from .ipe_git_ops import (
    commit_changes,
    finalize_git_operations,
    get_current_branch,
)
from .ipe_workflow_ops import (
    ensure_ipe_id,
    classify_issue,
    build_plan,
    implement_plan,
    generate_branch_name,
    create_commit,
    format_issue_message,
    extract_ipe_info,
    AGENT_PLANNER,
    AGENT_BUILDER,
    AGENT_VALIDATOR,
    AVAILABLE_IPE_WORKFLOWS,
)
from .ipe_worktree_ops import (
    create_worktree,
    validate_worktree,
)
from .ipe_utils import (
    setup_logger,
    check_env_vars,
    make_ipe_id,
)

# Infrastructure-specific modules
from .terraform_ops import (
    run_terraform_init,
    run_terraform_validate,
    run_terraform_plan,
    run_terraform_fmt,
    apply_terraform_changes,
    destroy_terraform,
)

__all__ = [
    # State
    'IPEState',
    'IPEStateData',
    # Agent
    'execute_template',
    # GitHub
    'fetch_issue',
    'make_issue_comment',
    'get_repo_url',
    'extract_repo_path',
    # Git ops
    'commit_changes',
    'finalize_git_operations',
    'get_current_branch',
    # Workflow ops
    'ensure_ipe_id',
    'classify_issue',
    'build_plan',
    'implement_plan',
    'generate_branch_name',
    'create_commit',
    'format_issue_message',
    'extract_ipe_info',
    'AGENT_PLANNER',
    'AGENT_BUILDER',
    'AGENT_VALIDATOR',
    'AVAILABLE_IPE_WORKFLOWS',
    # Worktree ops
    'create_worktree',
    'validate_worktree',
    # Utils
    'setup_logger',
    'check_env_vars',
    'make_ipe_id',
    # Terraform ops
    'run_terraform_init',
    'run_terraform_validate',
    'run_terraform_plan',
    'run_terraform_fmt',
    'apply_terraform_changes',
    'destroy_terraform',
]
