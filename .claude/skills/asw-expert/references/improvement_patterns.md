# ASW Improvement Patterns

A catalog of improvement patterns, optimization opportunities, and enhancement ideas for the Agentic Software Workflow system. This covers both ASW App (application development) and ASW IO (infrastructure operations) workflows.

---

## Performance Improvements

### 1. Parallel Phase Execution

**Current State:** Phases execute sequentially, even when independent.

**Improvement:** Run independent operations in parallel.

**Example - Parallel Classification and Branch Generation:**
```python
import asyncio

async def plan_phase_parallel(issue_number, asw_id, logger):
    # These can run in parallel since they're independent
    classify_task = asyncio.create_task(
        async_classify_issue(issue, asw_id, logger)
    )
    branch_task = asyncio.create_task(
        async_generate_branch_name(issue, "/feature", asw_id, logger)  # Assume feature
    )

    issue_class, error1 = await classify_task
    branch_name, error2 = await branch_task

    # Re-generate branch if classification was different
    if issue_class != "/feature":
        branch_name, _ = await async_generate_branch_name(issue, issue_class, asw_id, logger)

    return issue_class, branch_name
```

**Parallelizable Operations (App):**
- Issue fetch + Worktree creation
- Unit tests + E2E tests (with isolation)
- Screenshot upload + Comment posting
- Documentation generation + PR update

**Parallelizable Operations (IO):**
- Issue fetch + Worktree creation
- terraform validate + terraform fmt check
- Multiple module plan operations
- Documentation generation + Cost estimation

**Savings Estimate:** 20-30% reduction in total workflow time.

---

### 2. Issue Classification Caching

**Current State:** Every workflow run reclassifies the issue from scratch.

**Improvement:** Cache classification results by issue hash.

```python
import hashlib

def get_classification_cache_key(issue: GitHubIssue) -> str:
    """Generate cache key from issue content."""
    content = f"{issue.title}|{issue.body}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]

def classify_issue_cached(issue: GitHubIssue, asw_id: str, logger: logging.Logger):
    cache_key = get_classification_cache_key(issue)
    cache_file = f"agents/{asw_id}/cache/classification_{cache_key}.json"

    if os.path.exists(cache_file):
        with open(cache_file) as f:
            cached = json.load(f)
        logger.info(f"Using cached classification: {cached['issue_class']}")
        return cached['issue_class'], None

    # Run classification
    issue_class, error = classify_issue(issue, asw_id, logger)

    if not error:
        os.makedirs(f"agents/{asw_id}/cache", exist_ok=True)
        with open(cache_file, 'w') as f:
            json.dump({'issue_class': issue_class, 'timestamp': datetime.now().isoformat()}, f)

    return issue_class, error
```

**Savings Estimate:** ~30 seconds per re-run of same issue.

---

### 3. Model Selection Optimization

**Current State:** Model selected per-command from static mapping.

**Improvement:** Dynamic model selection based on:
- Issue complexity (token count)
- Historical success rates
- Available budget
- Time constraints

```python
def get_optimal_model(request: AgentTemplateRequest, state: ASWAppState) -> str:
    """Select model based on multiple factors."""

    # Factor 1: Issue complexity
    issue_tokens = estimate_tokens(state.get("issue_body", ""))
    complexity_model = "opus" if issue_tokens > 2000 else "sonnet"

    # Factor 2: Historical success
    command_history = load_command_history(request.slash_command)
    if command_history.get("sonnet_failure_rate", 0) > 0.3:
        complexity_model = "opus"

    # Factor 3: Time constraints (ZTE mode = faster model)
    if state.get("zte_mode"):
        return "sonnet"  # Always use faster model for ZTE

    # Factor 4: Budget override from model_set
    model_set = state.get("model_set", "base")
    if model_set == "heavy":
        return "opus"

    return complexity_model
```

---

### 4. Incremental Worktree Sync

**Current State:** Fresh worktree created from origin/main each time.

**Improvement:** Reuse existing worktree if branch is clean and up-to-date.

```python
def get_or_create_worktree(asw_id: str, branch_name: str, logger: logging.Logger):
    worktree_path = get_worktree_path(asw_id)

    if os.path.exists(worktree_path):
        # Check if worktree is clean and on correct branch
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=worktree_path
        )
        is_clean = not result.stdout.strip()

        current_branch = get_current_branch(cwd=worktree_path)

        if is_clean and current_branch == branch_name:
            # Just fetch and rebase
            subprocess.run(["git", "fetch", "origin"], cwd=worktree_path)
            subprocess.run(["git", "rebase", "origin/main"], cwd=worktree_path)
            logger.info(f"Reusing existing worktree: {worktree_path}")
            return worktree_path, None

    # Fall back to fresh worktree
    return create_worktree(asw_id, branch_name, logger)
```

**Savings Estimate:** ~60 seconds when reusing worktree.

---

## Reliability Improvements

### 5. Enhanced Retry Logic

**Current State:** Fixed retry delays [1, 3, 5] seconds.

**Improvement:** Exponential backoff with jitter and category-specific strategies.

```python
from enum import Enum
import random

class RetryStrategy(Enum):
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    EXPONENTIAL_JITTER = "exponential_jitter"

def get_retry_delays(
    retry_code: RetryCode,
    max_retries: int = 3,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_JITTER
) -> List[float]:
    """Get retry delays based on error type and strategy."""

    base_delay = {
        RetryCode.TIMEOUT_ERROR: 10,       # Timeouts need longer waits
        RetryCode.CLAUDE_CODE_ERROR: 3,    # Quick retries for transient errors
        RetryCode.EXECUTION_ERROR: 5,      # Medium delay
        RetryCode.ERROR_DURING_EXECUTION: 8,  # Agent crash, needs recovery time
    }.get(retry_code, 3)

    if strategy == RetryStrategy.FIXED:
        return [base_delay] * max_retries

    elif strategy == RetryStrategy.EXPONENTIAL:
        return [base_delay * (2 ** i) for i in range(max_retries)]

    elif strategy == RetryStrategy.EXPONENTIAL_JITTER:
        delays = []
        for i in range(max_retries):
            delay = base_delay * (2 ** i)
            jitter = delay * random.uniform(-0.1, 0.3)  # -10% to +30%
            delays.append(delay + jitter)
        return delays

    return [base_delay] * max_retries
```

---

### 6. State Validation Before Phase Transitions

**Current State:** Phases assume previous phase completed correctly.

**Improvement:** Explicit validation gates between phases.

```python
from dataclasses import dataclass
from typing import Set

@dataclass
class PhaseRequirements:
    required_fields: Set[str]
    optional_fields: Set[str] = None
    validation_func: callable = None

# App workflow phase requirements
APP_PHASE_REQUIREMENTS = {
    "build": PhaseRequirements(
        required_fields={"asw_id", "issue_number", "branch_name", "plan_file", "worktree_path"},
        optional_fields={"issue_class"},
    ),
    "test": PhaseRequirements(
        required_fields={"asw_id", "issue_number", "branch_name", "worktree_path"},
        validation_func=lambda state: os.path.exists(state.get("worktree_path")),
    ),
    "review": PhaseRequirements(
        required_fields={"asw_id", "issue_number", "branch_name", "worktree_path", "plan_file"},
    ),
    "ship": PhaseRequirements(
        required_fields={"asw_id", "issue_number", "branch_name", "pr_number"},
        validation_func=lambda state: state.get("shipped_at") is None,
    ),
}

# IO workflow phase requirements
IO_PHASE_REQUIREMENTS = {
    "build": PhaseRequirements(
        required_fields={"asw_id", "issue_number", "branch_name", "plan_file", "worktree_path", "terraform_workspace"},
        optional_fields={"issue_class", "infrastructure_type"},
    ),
    "test": PhaseRequirements(
        required_fields={"asw_id", "issue_number", "branch_name", "worktree_path"},
        validation_func=lambda state: os.path.exists(state.get("worktree_path")),
    ),
    "deploy": PhaseRequirements(
        required_fields={"asw_id", "issue_number", "branch_name", "worktree_path", "terraform_workspace"},
        validation_func=lambda state: state.get("plan_output_file") is not None,
    ),
}

def validate_phase_requirements(phase: str, state, workflow_type: str = "app") -> Tuple[bool, str]:
    """Validate state meets phase requirements."""
    requirements = APP_PHASE_REQUIREMENTS if workflow_type == "app" else IO_PHASE_REQUIREMENTS
    reqs = requirements.get(phase)
    if not reqs:
        return True, None

    # Check required fields
    missing = []
    for field in reqs.required_fields:
        if not state.get(field):
            missing.append(field)

    if missing:
        return False, f"Missing required fields for {phase}: {', '.join(missing)}"

    # Run custom validation
    if reqs.validation_func and not reqs.validation_func(state):
        return False, f"Custom validation failed for {phase}"

    return True, None
```

---

### 7. Graceful Degradation Patterns

**Current State:** Failures halt workflow entirely.

**Improvement:** Allow phases to succeed partially or skip gracefully.

```python
@dataclass
class PhaseResult:
    success: bool
    skipped: bool = False
    degraded: bool = False
    error: Optional[str] = None
    details: Dict[str, Any] = None

def run_test_phase_graceful(state: ASWAppState, logger: logging.Logger) -> PhaseResult:
    """Run test phase with graceful degradation."""
    results = {"unit_tests": None, "e2e_tests": None}

    # Try unit tests
    try:
        unit_result = run_unit_tests(state, logger)
        results["unit_tests"] = unit_result
    except Exception as e:
        logger.warning(f"Unit tests failed to run: {e}")
        results["unit_tests"] = {"skipped": True, "reason": str(e)}

    # Try E2E tests (can skip if MCP not available)
    try:
        e2e_result = run_e2e_tests(state, logger)
        results["e2e_tests"] = e2e_result
    except PlaywrightMCPNotAvailable:
        logger.warning("E2E tests skipped: Playwright MCP not available")
        results["e2e_tests"] = {"skipped": True, "reason": "MCP not available"}

    # Determine overall result
    if results["unit_tests"].get("skipped") and results["e2e_tests"].get("skipped"):
        return PhaseResult(success=False, error="All tests skipped")

    if results["unit_tests"].get("skipped") or results["e2e_tests"].get("skipped"):
        return PhaseResult(success=True, degraded=True, details=results)

    all_passed = (
        results["unit_tests"].get("passed", False) and
        results["e2e_tests"].get("passed", False)
    )
    return PhaseResult(success=all_passed, details=results)
```

---

## Feature Enhancements

### 8. New Workflow Compositions

**Proposal: Security Scan Phase (App and IO)**

```python
# asw_security_iso.py

def run_security_scan(state, logger: logging.Logger, workflow_type: str = "app"):
    """Run security scanning as a workflow phase."""
    worktree_path = state.get_working_directory()

    findings = []

    # Run Semgrep for code analysis
    semgrep_result = subprocess.run(
        ["semgrep", "--config", "auto", "--json", "."],
        capture_output=True, text=True, cwd=worktree_path
    )
    if semgrep_result.stdout:
        findings.extend(json.loads(semgrep_result.stdout).get("results", []))

    # IO-specific: Check for secrets in Terraform
    if workflow_type == "io":
        tfsec_result = subprocess.run(
            ["tfsec", "--format=json", "io/terraform"],
            capture_output=True, text=True, cwd=worktree_path
        )
        if tfsec_result.stdout:
            findings.extend(json.loads(tfsec_result.stdout).get("results", []))

    # Categorize findings
    critical = [f for f in findings if f.get("severity") in ["ERROR", "CRITICAL", "HIGH"]]
    warnings = [f for f in findings if f.get("severity") in ["WARNING", "MEDIUM"]]

    return SecurityResult(
        critical_count=len(critical),
        warning_count=len(warnings),
        block_ship=len(critical) > 0,
        findings=findings,
    )
```

**Proposal: Terraform Cost Estimation Phase (IO)**

```python
# asw_io_cost_estimate_iso.py

def run_cost_estimation(state: ASWIOState, logger: logging.Logger):
    """Estimate infrastructure costs before deployment."""
    worktree_path = state.get_working_directory()
    terraform_dir = os.path.join(worktree_path, "io/terraform")

    # Run Infracost
    result = subprocess.run([
        "infracost", "breakdown",
        "--path", terraform_dir,
        "--format", "json"
    ], capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"Infracost failed: {result.stderr}")
        return None

    cost_data = json.loads(result.stdout)

    return CostEstimation(
        monthly_cost=cost_data.get("totalMonthlyCost"),
        hourly_cost=cost_data.get("totalHourlyCost"),
        resources=cost_data.get("projects", []),
        currency="USD",
    )
```

**Proposal: Terraform Drift Detection (IO)**

```python
# asw_io_drift_detection_iso.py

def detect_infrastructure_drift(state: ASWIOState, logger: logging.Logger):
    """Detect drift between Terraform state and actual infrastructure."""
    worktree_path = state.get_working_directory()
    terraform_dir = os.path.join(worktree_path, "io/terraform")

    # Run terraform plan to detect drift
    result = subprocess.run([
        "terraform", "plan",
        "-refresh-only",
        "-json"
    ], capture_output=True, text=True, cwd=terraform_dir)

    plan_output = [json.loads(line) for line in result.stdout.strip().split("\n") if line]

    drift_detected = []
    for entry in plan_output:
        if entry.get("type") == "resource_drift":
            drift_detected.append(entry)

    return DriftResult(
        has_drift=len(drift_detected) > 0,
        drifted_resources=drift_detected,
        requires_remediation=len(drift_detected) > 0,
    )
```

---

### 9. Custom Phase Hooks

**Improvement:** Allow users to inject custom logic at phase boundaries.

```python
# .claude/hooks/asw_phase_hooks.py

def pre_build(state, context: Dict, workflow_type: str = "app") -> HookResult:
    """Run before build phase starts."""
    # Custom validation
    if "experimental" in state.get("branch_name", ""):
        return HookResult(
            proceed=True,
            message="Experimental branch detected, extra logging enabled"
        )
    return HookResult(proceed=True)

def post_test(state, test_results: Dict, workflow_type: str = "app") -> HookResult:
    """Run after test phase completes."""
    # Send Slack notification on test failure
    if not test_results.get("passed"):
        send_slack_notification(
            channel="#dev",
            message=f"Tests failed for ASW {workflow_type.upper()} {state.get('asw_id')}"
        )
    return HookResult(proceed=True)

def pre_ship(state, context: Dict, workflow_type: str = "app") -> HookResult:
    """Gate shipping based on custom criteria."""
    # Require approval for production-tagged issues
    if "production" in state.get("labels", []):
        approval = check_approval_status(state.get("pr_number"))
        if not approval:
            return HookResult(
                proceed=False,
                message="Production changes require approval"
            )
    return HookResult(proceed=True)

def pre_deploy(state: ASWIOState, context: Dict) -> HookResult:
    """IO-specific: Gate deployment based on environment."""
    workspace = state.get("terraform_workspace")
    if workspace == "prod":
        # Require explicit confirmation for prod
        if not context.get("prod_confirmed"):
            return HookResult(
                proceed=False,
                message="Production deployment requires explicit confirmation"
            )
    return HookResult(proceed=True)
```

**Hook Registration:**
```python
# In workflow scripts
from asw.hooks import load_phase_hooks

hooks = load_phase_hooks()

# Before build
if hooks.pre_build:
    result = hooks.pre_build(state, context, workflow_type="app")
    if not result.proceed:
        logger.warning(f"Pre-build hook blocked: {result.message}")
        return

# Run build...

# After build
if hooks.post_build:
    hooks.post_build(state, build_result, workflow_type="app")
```

---

### 10. External Service Integration

**Proposal: Jira Integration**

```python
# asw/modules/jira.py

class JiraIntegration:
    def __init__(self, base_url: str, api_token: str):
        self.client = JiraClient(base_url, api_token)

    def sync_issue(self, github_issue: GitHubIssue, asw_id: str, workflow_type: str = "app"):
        """Create or update Jira issue from GitHub issue."""
        jira_key = self.find_linked_issue(github_issue.number)

        if jira_key:
            self.client.update_issue(jira_key, {
                "status": self.map_status(github_issue.state),
                "custom_asw_id": asw_id,
                "custom_workflow_type": workflow_type,
            })
        else:
            jira_key = self.client.create_issue({
                "project": "PROJ",
                "summary": github_issue.title,
                "description": github_issue.body,
                "custom_github_issue": github_issue.number,
                "custom_asw_id": asw_id,
                "custom_workflow_type": workflow_type,
            })

        return jira_key
```

**Proposal: Metrics/Observability**

```python
# asw/modules/metrics.py

from datadog import statsd

class ASWMetrics:
    @staticmethod
    def phase_started(phase: str, asw_id: str, workflow_type: str = "app"):
        statsd.increment(f"asw.phase.started", tags=[
            f"phase:{phase}",
            f"asw:{asw_id}",
            f"workflow:{workflow_type}",
        ])

    @staticmethod
    def phase_completed(phase: str, asw_id: str, duration_ms: int, success: bool, workflow_type: str = "app"):
        statsd.timing(f"asw.phase.duration", duration_ms, tags=[
            f"phase:{phase}",
            f"asw:{asw_id}",
            f"success:{success}",
            f"workflow:{workflow_type}",
        ])
        statsd.increment(f"asw.phase.completed", tags=[
            f"phase:{phase}",
            f"success:{success}",
            f"workflow:{workflow_type}",
        ])

    @staticmethod
    def claude_execution(command: str, model: str, tokens: int, cost_usd: float):
        statsd.histogram("asw.claude.tokens", tokens, tags=[
            f"command:{command}",
            f"model:{model}",
        ])
        statsd.histogram("asw.claude.cost", cost_usd, tags=[
            f"command:{command}",
            f"model:{model}",
        ])

    @staticmethod
    def terraform_operation(operation: str, asw_id: str, duration_ms: int, success: bool):
        statsd.timing("asw.terraform.duration", duration_ms, tags=[
            f"operation:{operation}",
            f"asw:{asw_id}",
            f"success:{success}",
        ])
```

---

## IO-Specific Improvements

### 11. Terraform Caching Strategies

**Current State:** Terraform init runs from scratch each time.

**Improvement:** Cache provider plugins and modules.

```python
def setup_terraform_cache(worktree_path: str, asw_id: str):
    """Configure Terraform plugin and module caching."""
    cache_dir = os.path.join(os.path.expanduser("~"), ".terraform.d/plugin-cache")
    os.makedirs(cache_dir, exist_ok=True)

    # Create terraformrc with caching
    terraformrc_content = f"""
plugin_cache_dir = "{cache_dir}"
disable_checkpoint = true
"""
    with open(os.path.join(worktree_path, ".terraformrc"), "w") as f:
        f.write(terraformrc_content)

    # Set environment for terraform commands
    return {
        "TF_CLI_CONFIG_FILE": os.path.join(worktree_path, ".terraformrc"),
        "TF_PLUGIN_CACHE_DIR": cache_dir,
    }
```

**Savings Estimate:** 30-60 seconds per terraform init.

---

### 12. Parallel Infrastructure Provisioning

**Improvement:** Run independent Terraform resources in parallel.

```python
def analyze_terraform_dependencies(terraform_dir: str) -> Dict[str, List[str]]:
    """Analyze Terraform resource dependencies for parallel execution."""
    result = subprocess.run([
        "terraform", "graph", "-type=plan"
    ], capture_output=True, text=True, cwd=terraform_dir)

    # Parse the DOT graph output
    dependencies = {}
    for line in result.stdout.split("\n"):
        if "->" in line:
            match = re.match(r'"([^"]+)"\s*->\s*"([^"]+)"', line)
            if match:
                resource, depends_on = match.groups()
                if resource not in dependencies:
                    dependencies[resource] = []
                dependencies[resource].append(depends_on)

    return dependencies

def plan_parallel_apply(dependencies: Dict[str, List[str]]) -> List[List[str]]:
    """Create execution waves for parallel apply."""
    waves = []
    remaining = set(dependencies.keys())

    while remaining:
        # Find resources with no remaining dependencies
        wave = []
        for resource in remaining:
            deps = set(dependencies.get(resource, []))
            if not deps.intersection(remaining):
                wave.append(resource)

        if not wave:
            # Circular dependency, fall back to sequential
            wave = list(remaining)

        waves.append(wave)
        remaining -= set(wave)

    return waves
```

---

## Code Quality Improvements

### 13. Module Consolidation Opportunities

**Current State:** Some logic is duplicated across modules.

**Consolidation Targets:**

| Duplicated Logic | Files | Consolidation |
|------------------|-------|---------------|
| Project root path | agent.py, state.py, workflow_ops.py | Create `paths.py` module |
| Git subprocess calls | git_ops.py, workflow_ops.py, worktree_ops.py | Standardize in `git_ops.py` |
| JSON parsing from markdown | agent.py, workflow_ops.py | Use `utils.parse_json()` everywhere |
| Logging setup | Multiple scripts | Create `logger_factory.py` |

**Example - Paths Module:**
```python
# asw/modules/paths.py

import os

_PROJECT_ROOT = None

def get_project_root() -> str:
    """Get project root directory (cached)."""
    global _PROJECT_ROOT
    if _PROJECT_ROOT is None:
        # Walk up from asw/modules to project root
        _PROJECT_ROOT = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
    return _PROJECT_ROOT

def get_agents_dir() -> str:
    return os.path.join(get_project_root(), "agents")

def get_trees_dir() -> str:
    return os.path.join(get_project_root(), "trees")

def get_specs_dir() -> str:
    return os.path.join(get_project_root(), "specs")

def get_io_dir() -> str:
    return os.path.join(get_project_root(), "io")
```

---

### 14. Type Safety Enhancements

**Current State:** Some functions use `Any` or loose typing.

**Improvements:**

```python
# Before
def classify_issue(issue, asw_id, logger):
    ...

# After
def classify_issue(
    issue: GitHubIssue,
    asw_id: str,
    logger: logging.Logger
) -> Tuple[Optional[IssueClassSlashCommand], Optional[str]]:
    ...
```

**Protocol for Stateful Objects:**
```python
from typing import Protocol

class Stateful(Protocol):
    """Protocol for objects that manage ASW state."""

    def get(self, key: str, default: Any = None) -> Any: ...
    def update(self, **kwargs) -> None: ...
    def save(self, workflow_step: Optional[str] = None) -> None: ...
    def get_working_directory(self) -> str: ...
```

---

### 15. Test Coverage Improvements

**Current Coverage Gaps:**

| Module | Current | Target | Priority |
|--------|---------|--------|----------|
| state.py | 70% | 95% | High |
| agent.py | 40% | 80% | High |
| workflow_ops.py | 50% | 85% | Medium |
| worktree_ops.py | 30% | 75% | Medium |
| github.py | 60% | 90% | Low |

**Test Patterns Needed:**

1. **State Persistence Tests**
```python
def test_app_state_roundtrip():
    """State should survive save/load cycle."""
    state = ASWAppState("test123")
    state.update(branch_name="test-branch", plan_file="specs/test.md")
    state.save()

    loaded = ASWAppState.load("test123")
    assert loaded.get("branch_name") == "test-branch"
    assert loaded.get("plan_file") == "specs/test.md"

def test_io_state_roundtrip():
    """IO State should include terraform-specific fields."""
    state = ASWIOState("test456")
    state.update(
        branch_name="test-branch",
        terraform_workspace="dev",
        infrastructure_type="terraform"
    )
    state.save()

    loaded = ASWIOState.load("test456")
    assert loaded.get("terraform_workspace") == "dev"
    assert loaded.get("infrastructure_type") == "terraform"
```

2. **Retry Logic Tests**
```python
def test_retry_on_timeout():
    """Should retry on timeout with increasing delays."""
    mock_response = [
        AgentPromptResponse(success=False, retry_code=RetryCode.TIMEOUT_ERROR),
        AgentPromptResponse(success=False, retry_code=RetryCode.TIMEOUT_ERROR),
        AgentPromptResponse(success=True, output="Success"),
    ]

    with patch('asw.modules.agent.prompt_claude_code', side_effect=mock_response):
        result = prompt_claude_code_with_retry(request, max_retries=3)
        assert result.success == True
```

3. **Worktree Isolation Tests**
```python
def test_worktree_isolation():
    """Worktrees should be completely isolated."""
    # Create two worktrees
    path1, _ = create_worktree("asw1", "branch1", logger)
    path2, _ = create_worktree("asw2", "branch2", logger)

    # Changes in one shouldn't affect the other
    write_file(f"{path1}/test.txt", "content1")
    assert not os.path.exists(f"{path2}/test.txt")
```

---

## Implementation Priority

### Quick Wins (1-2 hours each)
1. State validation before phases (#6)
2. Paths module consolidation (#13)
3. Classification caching (#2)
4. Terraform caching setup (#11)

### Medium Effort (1-2 days each)
5. Enhanced retry logic (#5)
6. Phase hooks (#9)
7. Type safety improvements (#14)
8. Cost estimation integration (#8 - IO)

### Major Initiatives (1-2 weeks each)
9. Parallel phase execution (#1)
10. Security scan phase (#8)
11. External integrations (#10)
12. Comprehensive test coverage (#15)
13. Drift detection (#8 - IO)
