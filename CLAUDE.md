# Claude Code Project Instructions

## Project Context

- **Project Name**: Hello App
- **Description**: A simple Hello World web application
- **Repository**: https://github.com/rfomerandAgents/hello-app

## Quick Start

- Use `/install` to discover project structure and install dependencies
- Use `/prime` to load project context (driven by `/install` findings)

## Development Workflow

### For Application Code (ASW App)
```bash
# Full SDLC workflow
uv run asw/app/asw_app_sdlc_iso.py <issue-number>
```

### For Infrastructure Code (ASW IO)
```bash
# Full SDLC workflow
uv run asw/io/asw_io_sdlc_iso.py <issue-number>
```

## Code Style

- Follow existing code patterns in the repository
- Use TypeScript for frontend code
- Use Python 3.10+ for backend automation
- Follow PEP 8 for Python code
- Use Prettier/ESLint for JavaScript/TypeScript

## Common Instructions

### Development
- Always run tests before committing
- Use semantic commit messages
- Create feature branches for new work
- Update documentation for significant changes

### Infrastructure
- Use Terraform for infrastructure as code
- Never commit secrets or API keys
- Use environment variables for configuration
- Test infrastructure changes in dev/sandbox first

### Agentic Software Workflow
- Use `/bug` for bug fixes
- Use `/feature` for new features
- Use `/chore` for maintenance tasks
- Always include issue number in commits

## Tools and Commands

Available slash commands:

- `/install` - Install all project dependencies
- `/prime` - Load project context
- `/bug <issue>` - Process bug fix
- `/feature <issue>` - Implement feature
- `/chore <issue>` - Process maintenance task
- `/commit` - Create a commit with semantic message

## Project-Specific Instructions

<!-- Add your project-specific instructions here -->

## Resources

- [ASW Documentation](asw/README.md)
- [Terraform Documentation](terraform/README.md)
- [Application Documentation](app/README.md)
