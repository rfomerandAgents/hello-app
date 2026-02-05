<!--
=============================================================================
/feature-commented - Heavily Commented Feature Planning Command
=============================================================================

PURPOSE:
This command is identical to /feature but includes detailed inline comments
explaining every line, section, and instruction. It serves as:
- Educational documentation for understanding how feature planning works
- Template for creating new similar commands
- Reference for command structure and Claude Code prompt engineering

USAGE:
/feature-commented <issue-number> <adw-id> <issue-json>

ARGUMENTS:
- issue-number: GitHub issue number (e.g., 42)
- adw-id: Application Developer Workflow ID (e.g., adw-abc123)
- issue-json: JSON string containing issue title and body

OUTPUT:
Creates a detailed feature implementation plan saved to:
specs/issue-{issue-number}-adw-{adw-id}-sdlc_planner-{descriptive-name}.md

MAINTENANCE:
- Keep in sync with /feature for functionality
- Update comments when command structure changes
- Comments explain WHAT and WHY, not just WHAT
=============================================================================
-->

<!-- SECTION: Command Title -->
<!-- This H1 header serves as the command's display name in Claude Code -->
# Feature Planning

<!-- SECTION: Command Description -->
<!--
High-level instruction that sets the context for what this command does.
Key points:
- Creates a PLAN (not implementation itself)
- Uses a specific "Plan Format" template (defined below)
- Follows "Instructions" for guidance (defined below)
- Scopes work to "Relevant Files" (defined below)
-->
Create a new plan to implement the `Feature` using the exact specified markdown `Plan Format`. Follow the `Instructions` to create the plan use the `Relevant Files` to focus on the right files.

<!-- SECTION: Variable Declarations -->
<!--
Variables define command-line arguments passed to the slash command.
Syntax: variable_name: $N where N is the argument position (1-indexed)

These variables can be referenced throughout the command using {variable_name}
-->
## Variables

<!-- VARIABLE: issue_number -->
<!-- $1: First command-line argument - GitHub issue number (e.g., 42) -->
<!-- Used in: filename generation, metadata, issue extraction -->
issue_number: $1

<!-- VARIABLE: adw_id -->
<!-- $2: Second command-line argument - ADW workflow identifier (e.g., adw-abc123) -->
<!-- Used in: filename generation, metadata, workflow tracking -->
adw_id: $2

<!-- VARIABLE: issue_json -->
<!-- $3: Third command-line argument - JSON string with issue details -->
<!-- Format: {"title": "Issue Title", "body": "Issue description..."} -->
<!-- Used in: Feature extraction section to get issue title and body -->
issue_json: $3

<!-- SECTION: Instructions -->
<!--
This section provides detailed guidance to Claude on HOW to create the plan.
Instructions are executed in order and include:
- Context setting (what are we doing, what are we NOT doing)
- File creation and naming conventions
- Research and analysis requirements
- Important constraints and patterns to follow
- Integration with other systems (E2E tests, conditional docs)

IMPORTANT PATTERN: Many instructions use "IMPORTANT:" prefix to emphasize
critical requirements that must not be overlooked.
-->
## Instructions

<!-- INSTRUCTION 1: Set Context - What We're Doing -->
<!--
Clarifies that this command creates a PLAN, not an implementation.
This prevents Claude from trying to write actual feature code.
Emphasizes we're adding NEW functionality (not fixing/modifying existing).
-->
- IMPORTANT: You're writing a plan to implement a net new feature based on the `Feature` that will add value to the application.

<!-- INSTRUCTION 2: Reinforce Planning vs Implementation -->
<!--
Further reinforcement of planning vs implementation distinction.
The feature description is INPUT, the plan following "Plan Format" is OUTPUT.
This is critical to prevent scope creep into implementation.
-->
- IMPORTANT: The `Feature` describes the feature that will be implemented but remember we're not implementing a new feature, we're creating the plan that will be used to implement the feature based on the `Plan Format` below.

<!-- INSTRUCTION 3: File Creation and Naming Convention -->
<!--
Specifies WHERE to save the plan and HOW to name it.
Naming pattern: issue-{issue_number}-adw-{adw_id}-sdlc_planner-{descriptive-name}.md
- issue-{issue_number}: Links to GitHub issue
- adw-{adw_id}: Links to workflow
- sdlc_planner: Indicates this is a planning document
- {descriptive-name}: Human-readable feature identifier (kebab-case)

Examples of {descriptive-name}:
- "add-auth-system" (new authentication)
- "implement-search" (search functionality)
- "create-dashboard" (dashboard feature)
-->
- Create the plan in the `specs/` directory with filename: `issue-{issue_number}-adw-{adw_id}-sdlc_planner-{descriptive-name}.md`
  - Replace `{descriptive-name}` with a short, descriptive name based on the feature (e.g., "add-auth-system", "implement-search", "create-dashboard")

<!-- INSTRUCTION 4: Template Adherence -->
<!--
Commands Claude to use the exact structure defined in "Plan Format" section.
This ensures consistency across all feature plans.
-->
- Use the `Plan Format` below to create the plan.

<!-- INSTRUCTION 5: Codebase Research Requirement -->
<!--
CRITICAL: Requires thorough codebase exploration BEFORE planning.
This prevents generic plans and ensures plans are grounded in actual codebase.
Things to research:
- Existing patterns (how similar features are implemented)
- Architecture (how components are organized)
- Conventions (naming, file structure, code style)
-->
- Research the codebase to understand existing patterns, architecture, and conventions before planning the feature.

<!-- INSTRUCTION 6: Placeholder Replacement -->
<!--
Every <placeholder> in the template MUST be replaced with actual content.
"Add as much detail as needed" - plans should be comprehensive, not minimal.
This ensures plans are actionable and complete.
-->
- IMPORTANT: Replace every <placeholder> in the `Plan Format` with the requested value. Add as much detail as needed to implement the feature successfully.

<!-- INSTRUCTION 7: Deep Thinking Requirement -->
<!--
Invokes Claude's reasoning capabilities for complex analysis.
"THINK HARD" emphasizes need for thoughtful design, not quick surface-level plans.
Consider: requirements, edge cases, design tradeoffs, implementation approach.
-->
- Use your reasoning model: THINK HARD about the feature requirements, design, and implementation approach.

<!-- INSTRUCTION 8: Pattern Following -->
<!--
Encourages reusing existing code patterns instead of inventing new ones.
"Don't reinvent the wheel" - leverage what already works.
Benefits: consistency, maintainability, fewer bugs.
-->
- Follow existing patterns and conventions in the codebase. Don't reinvent the wheel.

<!-- INSTRUCTION 9: Design Principles -->
<!--
Sets architectural standards for the feature plan.
- Extensibility: Easy to add new capabilities later
- Maintainability: Easy to understand and modify
These principles guide design decisions in the plan.
-->
- Design for extensibility and maintainability.

<!-- INSTRUCTION 10: Dependency Management -->
<!--
If the feature requires external libraries:
- Use `uv add` command (Python package manager for this project)
- Document new dependencies in "Notes" section
This ensures dependencies are tracked and transparent.
-->
- If you need a new library, use `uv add` and be sure to report it in the `Notes` section of the `Plan Format`.

<!-- INSTRUCTION 11: Code Style Constraint -->
<!--
Project-specific constraint: avoid Python decorators.
"Keep it simple" - prefer explicit code over magic/metaprogramming.
This is a codebase convention that plans must respect.
-->
- Don't use decorators. Keep it simple.

<!-- INSTRUCTION 12: E2E Testing Integration (Complex Multi-Part) -->
<!--
CONDITIONAL INSTRUCTION: Only applies if feature has UI components.

When feature includes UI/user interactions, the plan must:
1. Add a task to CREATE an E2E test file (not the test itself, just a task for it)
2. Add E2E test validation to Validation Commands
3. Include E2E test documentation in Relevant Files
4. List the new E2E test file in New Files section

Why this matters:
- UI features need end-to-end validation
- E2E tests prove features work from user perspective
- Tests serve as documentation of expected behavior

E2E test file naming: `.claude/commands/e2e/test_<descriptive_name>.md`
E2E test examples: test_basic_query.md, test_complex_query.md
-->
- IMPORTANT: If the feature includes UI components or user interactions:
  - Add a task in the `Step by Step Tasks` section to create a separate E2E test file in `.claude/commands/e2e/test_<descriptive_name>.md` based on examples in that directory
  - Add E2E test validation to your Validation Commands section
  - IMPORTANT: When you fill out the `Plan Format: Relevant Files` section, add an instruction to read `.claude/commands/test_e2e.md`, and `.claude/commands/e2e/test_basic_query.md` to understand how to create an E2E test file. List your new E2E test file to the `Plan Format: New Files` section.
  - To be clear, we're not creating a new E2E test file, we're creating a task to create a new E2E test file in the `Plan Format` below

<!-- INSTRUCTION 13: Respect File Scoping -->
<!--
Enforces focus on files listed in "Relevant Files" section.
Prevents unnecessary exploration of irrelevant code.
This improves efficiency and keeps plans focused.
-->
- Respect requested files in the `Relevant Files` section.

<!-- INSTRUCTION 14: Start with README -->
<!--
README.md should be the FIRST file read during research.
Why: Provides high-level context, architecture overview, setup instructions.
This orients the planning process before diving into specific code.
-->
- Start your research by reading the `README.md` file.

<!-- SECTION: Relevant Files -->
<!--
This section SCOPES Claude's exploration to specific files and directories.
Purpose:
- Prevents Claude from reading irrelevant files (saves tokens, improves focus)
- Directs attention to areas of codebase relevant to feature development
- Establishes a starting point for research

Pattern: "Focus on... Ignore all other files"
- Explicit inclusion (what TO read)
- Explicit exclusion (what NOT to read)

Note: app_docs/ directory contains feature-specific documentation discoverable through
glob patterns and grep searches - no static index file needed
-->
## Relevant Files

<!--
Primary scoping instruction: Read these files for context and implementation
-->
Focus on the following files:

<!-- FILE: README.md -->
<!-- Project overview, setup instructions, architecture summary -->
<!-- READ FIRST: Provides high-level context for the entire codebase -->
- `README.md` - Contains the project overview and instructions.

<!-- DIRECTORY: app/** -->
<!-- Main application codebase for {{PROJECT_NAME}} website -->
<!-- Technology: Next.js (React framework for server-rendered applications) -->
<!-- Scope: All frontend code, pages, components, styles, utilities -->
- `app/**` - Contains the {{PROJECT_NAME}} Next.js website codebase.

<!-- DIRECTORY: app/components/** -->
<!-- Reusable React components (UI building blocks) -->
<!-- Pattern: Component-per-file, typically with .tsx extension -->
<!-- Usage: Import and compose components to build pages -->
- `app/components/**` - Contains the React components for the website.

<!-- DIRECTORY: asw/app/** -->
<!-- Application Developer Workflow automation scripts -->
<!-- Technology: Python scripts with astral uv (single-file scripts) -->
<!-- Usage: Run with `uv run asw/app/script_name.py` -->
<!-- Scope: Workflow automation, not typically modified for app features -->
- `asw/app/**` - Contains the Agentic Software Workflow - App (ASW App) scripts.

<!-- INTEGRATION: Dynamic Documentation Discovery -->
<!--
DYNAMIC DOCUMENTATION DISCOVERY APPROACH
Instead of maintaining a static index file, we discover relevant documentation dynamically:

1. List app_docs/ directory to see available documentation files
   - Files follow pattern: {type}-{adw_id}-{description}.md
   - Types: feature, bug, chore

2. Use grep to find docs mentioning specific components, files, or concepts
   - Example: grep -l "ItemDetails" app_docs/*.md
   - Example: grep -l "Gallery" app_docs/*.md

3. Read Overview sections to determine relevance
   - Each app_docs file has standardized sections
   - Quick scanning determines if documentation is relevant

Benefits:
- Eliminates merge conflicts from parallel PRs updating a central index
- Documentation is self-contained in app_docs/ files
- Flexible discovery based on actual task needs
-->
- Search for relevant documentation in `app_docs/` directory:
  - Use `ls app_docs/` to see available documentation files
  - File naming: `{type}-{adw_id}-{description}.md` where type is feature, bug, or chore
  - Use `grep -l "<keyword>" app_docs/*.md` to find docs mentioning specific components
  - Read the Overview section of matching files to determine relevance

<!--
Explicit exclusion: Don't waste tokens on irrelevant files
This is important for:
- Performance (fewer files to read = faster execution)
- Focus (prevents distraction by unrelated code)
- Token efficiency (Claude has limited context window)
-->
Ignore all other files in the codebase.

<!-- SECTION: Plan Format -->
<!--
CRITICAL SECTION: This defines the EXACT STRUCTURE of the output plan.

Template Structure:
- Markdown format with specific sections
- Placeholders in angle brackets: <placeholder>
- Variable interpolation in curly braces: {variable_name}
- Triple backticks denote the template boundaries

Claude's Task:
1. Read this template
2. Replace ALL placeholders with actual content
3. Substitute ALL variables with their values
4. Output the completed plan to specs/ directory

Template Sections (in order):
1. Title (H1)
2. Metadata (issue tracking)
3. Feature Description (what it does)
4. User Story (user perspective)
5. Problem Statement (what problem it solves)
6. Solution Statement (how it solves it)
7. Relevant Files (implementation scope)
8. Implementation Plan (3 phases)
9. Step by Step Tasks (actionable steps)
10. Testing Strategy (unit tests, edge cases)
11. Acceptance Criteria (definition of done)
12. Validation Commands (verification steps)
13. Notes (additional context)
-->
## Plan Format

<!--
TEMPLATE START: Everything between the triple backticks is the template
-->
```md
<!-- TEMPLATE SECTION 1: Title -->
<!-- Format: "Feature: <feature name>" -->
<!-- Example: "Feature: User Authentication System" -->
# Feature: <feature name>

<!-- TEMPLATE SECTION 2: Metadata -->
<!--
Links plan back to GitHub issue and ADW workflow.
Uses backticks for code formatting.
Values come from command variables $1, $2, $3.
-->
## Metadata
issue_number: `{issue_number}` <!-- From $1: GitHub issue # -->
adw_id: `{adw_id}` <!-- From $2: ADW workflow ID -->
issue_json: `{issue_json}` <!-- From $3: Full issue JSON -->

<!-- TEMPLATE SECTION 3: Feature Description -->
<!--
Comprehensive explanation of the feature.
Should include:
- What the feature does (functionality)
- Why it's valuable (business value)
- Who it's for (target users)
- How it fits into the application (integration context)

NOT just a repeat of the issue title - add analysis and context.
-->
## Feature Description
<describe the feature in detail, including its purpose and value to users>

<!-- TEMPLATE SECTION 4: User Story -->
<!--
Standard user story format following Agile methodology.
Pattern: "As a [user type], I want to [action], So that [benefit]"

Example:
As a website visitor
I want to search content by keyword
So that I can quickly find relevant information

This provides user-centric context for the feature.
-->
## User Story
As a <type of user>
I want to <action/goal>
So that <benefit/value>

<!-- TEMPLATE SECTION 5: Problem Statement -->
<!--
Articulates the PROBLEM this feature solves.
Should answer:
- What's not working or missing?
- What pain point does this address?
- What opportunity does this unlock?

Be specific and concrete, not vague.
-->
## Problem Statement
<clearly define the specific problem or opportunity this feature addresses>

<!-- TEMPLATE SECTION 6: Solution Statement -->
<!--
Describes HOW the feature solves the problem.
Should include:
- High-level approach/strategy
- Key technical decisions
- How it addresses the problem statement

This bridges problem → implementation.
-->
## Solution Statement
<describe the proposed solution approach and how it solves the problem>

<!-- TEMPLATE SECTION 7: Relevant Files -->
<!--
Lists EXISTING and NEW files involved in implementation.

For existing files:
- File path
- Why it's relevant (what role it plays)
- What might be modified

For new files (H3 "New Files" subsection):
- File path
- Purpose of new file
- What it will contain

This scopes the implementation and shows file organization.
-->
## Relevant Files
Use these files to implement the feature:

<find and list the files that are relevant to the feature describe why they are relevant in bullet points. If there are new files that need to be created to implement the feature, list them in an h3 'New Files' section.>

<!-- TEMPLATE SECTION 8: Implementation Plan (3 Phases) -->
<!--
High-level roadmap organized into 3 phases.
This provides structure before detailed tasks.

Phase 1: Foundation
- Prerequisites and setup
- Shared utilities or infrastructure
- Database schema changes
- Type definitions

Phase 2: Core Implementation
- Main feature logic
- Business logic
- UI components (if applicable)
- Primary functionality

Phase 3: Integration
- Connect to existing features
- Testing and validation
- Documentation
- Performance optimization

Each phase description should be 2-4 sentences outlining major work.
-->
## Implementation Plan
### Phase 1: Foundation
<describe the foundational work needed before implementing the main feature>

### Phase 2: Core Implementation
<describe the main implementation work for the feature>

### Phase 3: Integration
<describe how the feature will integrate with existing functionality>

<!-- TEMPLATE SECTION 9: Step by Step Tasks -->
<!--
MOST DETAILED SECTION: Granular, ordered, actionable tasks.

Structure:
- H3 headers for task groups (e.g., "### Create Database Models")
- Bullet points for specific steps
- Order matters: top to bottom execution

Task Granularity:
- Each task should be completable in one sitting
- Include "what to do" and "where to do it"
- Reference specific files and functions

Special Requirements:
1. Start with foundational work (shared utilities, types, etc.)
2. Include test creation THROUGHOUT (not just at end)
3. For UI features: Add E2E test file creation task
4. Last task MUST be running Validation Commands

Task Format Example:
### Create Search Component
- Create `app/components/ItemSearch.tsx`
- Add search input field with debounced onChange
- Implement search results display
- Add loading and error states
- Write unit tests for search logic
-->
## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

<list step by step tasks as h3 headers plus bullet points. use as many h3 headers as needed to implement the feature. Order matters, start with the foundational shared changes required then move on to the specific implementation. Include creating tests throughout the implementation process.>

<!--
CONDITIONAL: If feature has UI components
Add early task to create E2E test file.
The test file itself is a markdown document that guides manual/automated testing.
It should specify exact steps to validate the feature works.
-->
<If the feature affects UI, include a task to create a E2E test file (like `.claude/commands/e2e/test_basic_query.md` and `.claude/commands/e2e/test_complex_query.md`) as one of your early tasks. That e2e test should validate the feature works as expected, be specific with the steps to demonstrate the new functionality. We want the minimal set of steps to validate the feature works as expected and screen shots to prove it if possible.>

<!--
FINAL TASK: Always end with validation
This ensures the plan includes verification steps.
-->
<Your last step should be running the `Validation Commands` to validate the feature works correctly with zero regressions.>

<!-- TEMPLATE SECTION 10: Testing Strategy -->
<!--
Defines how the feature will be tested.

Unit Tests:
- What components/functions need unit tests?
- What behaviors should tests verify?
- Test file locations and naming

Edge Cases:
- Boundary conditions (empty input, max length, etc.)
- Error scenarios (network failures, invalid data, etc.)
- Unusual usage patterns
- Performance edge cases (large datasets, etc.)

This guides test-driven development approach.
-->
## Testing Strategy
### Unit Tests
<describe unit tests needed for the feature>

### Edge Cases
<list edge cases that need to be tested>

<!-- TEMPLATE SECTION 11: Acceptance Criteria -->
<!--
DEFINITION OF DONE: Specific, measurable criteria.

Format: Bullet list of objective statements.
Each criterion should be:
- Testable (can verify it's met)
- Specific (no ambiguity)
- Measurable (pass/fail, not subjective)

Example criteria:
- [ ] Search returns results within 500ms
- [ ] All TypeScript checks pass with no errors
- [ ] E2E test demonstrates successful search flow
- [ ] Component renders correctly on mobile and desktop

These criteria determine when the feature is complete.
-->
## Acceptance Criteria
<list specific, measurable criteria that must be met for the feature to be considered complete>

<!-- TEMPLATE SECTION 12: Validation Commands -->
<!--
EXECUTABLE COMMANDS to verify feature works correctly.

Purpose:
- Prove implementation is complete
- Catch regressions
- Validate code quality
- Ensure production readiness

Command Requirements:
- Must be copy-pasteable (exact commands)
- Must run without errors when feature is complete
- Should cover end-to-end functionality

Standard Validation Commands (ALWAYS INCLUDED):
1. TypeScript check: Validates type safety
2. Lint check: Validates code style/quality
3. Build check: Validates production build works

Additional Commands (feature-specific):
- E2E test execution (if UI feature)
- API endpoint testing (if backend feature)
- Performance benchmarks (if performance-critical)
-->
## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

<list commands you'll use to validate with 100% confidence the feature is implemented correctly with zero regressions. every command must execute without errors so be specific about what you want to run to validate the feature works as expected. Include commands to test the feature end-to-end.>

<!--
CONDITIONAL: E2E test validation
If the plan includes E2E test creation, add validation step to read and execute it.
Format: Read test_e2e.md for instructions, then execute the feature-specific test.
-->
<If you created an E2E test, include the following validation step: `Read .claude/commands/test_e2e.md`, then read and execute your new E2E `.claude/commands/e2e/test_<descriptive_name>.md` test file to validate this functionality works.>

<!-- REQUIRED: TypeScript Type Check -->
<!-- Validates all types are correct, no type errors introduced -->
<!-- --noEmit: Check only, don't generate output files -->
- `cd app/ && bun tsc --noEmit` - Run TypeScript type check to validate the feature works with zero regressions

<!-- REQUIRED: Linting -->
<!-- Validates code style, best practices, potential bugs -->
<!-- Next.js includes ESLint configuration -->
- `cd app/ && bun run lint` - Run Next.js linting to validate code quality

<!-- REQUIRED: Production Build -->
<!-- Validates feature works in production mode, no build errors -->
<!-- Catches issues that only appear in optimized builds -->
- `cd app/ && bun run build` - Run production build to validate the feature works with zero regressions

<!-- TEMPLATE SECTION 13: Notes -->
<!--
OPTIONAL: Additional context, considerations, future work.

What to include:
- Future enhancements or extensions
- Known limitations or tradeoffs
- Dependencies or prerequisites
- Links to relevant documentation
- Performance considerations
- Security considerations

This section is freeform and optional but valuable for context.
-->
## Notes
<optionally list any additional notes, future considerations, or context that are relevant to the feature that will be helpful to the developer>
```
<!--
TEMPLATE END: Above triple backtick closes the template
-->

<!-- SECTION: Feature Extraction -->
<!--
This section tells Claude WHERE to get the feature information.

Source: {issue_json} variable (from $3 command argument)

JSON Structure:
{
  "title": "Issue title from GitHub",
  "body": "Issue description/body from GitHub"
}

Extraction Process:
1. Parse the issue_json string as JSON
2. Extract the "title" field → Use as feature name
3. Extract the "body" field → Use as feature description/requirements
4. Use these to fill in the plan template

Example:
If issue_json = '{"title": "Add search feature", "body": "Users need to search content by keyword..."}'
Then:
- Feature name: "Add search feature"
- Feature description: Content from body field
-->
## Feature

<!--
INSTRUCTION: Parse issue_json and extract title and body fields
-->
Extract the feature details from the `issue_json` variable (parse the JSON and use the title and body fields).

<!-- SECTION: Report -->
<!--
This section specifies HOW Claude should report completion.

Requirement: Return ONLY the file path, nothing else.

Why this matters:
- Output is parsed by automation scripts
- Extra text would break parsing
- File path is used to track the plan for next workflow steps

Format: specs/issue-{N}-adw-{ID}-sdlc_planner-{name}.md
Example: specs/issue-42-adw-abc123-sdlc_planner-add-search.md

What NOT to include:
- No "I created the file at..."
- No "Here is the plan:"
- No summary or explanation
- JUST the file path

This allows the calling script to capture the path and pass it to the next step.
-->
## Report

<!--
CRITICAL INSTRUCTION: Output format must be EXACTLY the file path, nothing more.
This is typically the last line Claude outputs after creating the plan.
-->
- IMPORTANT: Return exclusively the path to the plan file created and nothing else.

<!--
=============================================================================
END OF /feature-commented COMMAND
=============================================================================

SUMMARY:
This command guides Claude through creating a comprehensive feature implementation
plan following the ADW (Application Developer Workflow) methodology.

KEY SECTIONS:
1. Variables - Command-line arguments
2. Instructions - How to create the plan
3. Relevant Files - What codebase files to read
4. Plan Format - Output template structure
5. Feature - Where to get feature details
6. Report - How to report completion

MAINTENANCE NOTES:
- Keep in sync with /feature for functionality
- Update comments when instructions change
- Ensure all placeholders and variables are documented
- Test command after modifications

RELATED COMMANDS:
- /feature - Original version without comments
- /bug - Similar structure for bug fixes
- /chore - Similar structure for maintenance tasks
- /feature-commented - This command (heavily commented for education)

VERSION: 1.0.0
CREATED: 2025-11-12
BASED ON: .claude/commands/feature.md
=============================================================================
-->
