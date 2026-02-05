# Claude Code Project Instructions

Add your project-specific Claude Code instructions here.

## Project Context

- **Project Name**: {{PROJECT_NAME}}
- **Description**: {{PROJECT_DESCRIPTION}}
- **Repository**: {{GITHUB_REPO_URL}}

## Common Instructions

### Code Style

- Follow existing code patterns in the repository
- Use TypeScript for frontend code
- Use Python 3.10+ for backend automation
- Follow PEP 8 for Python code
- Use Prettier/ESLint for JavaScript/TypeScript

### Development Workflow

- Always run tests before committing
- Use semantic commit messages
- Create feature branches for new work
- Update documentation for significant changes

### Infrastructure

- Use Terraform for infrastructure as code
- Never commit secrets or API keys
- Use environment variables for configuration
- Test infrastructure changes in dev environment first

### AI Developer Workflow

- Use `/bug` for bug fixes
- Use `/feature` for new features
- Use `/chore` for maintenance tasks
- Always include issue number in commits

## Project-Specific Instructions

Add specific instructions for your project here:

- MCP server configuration (if applicable)
- API integration details
- Testing requirements
- Deployment procedures
- Any other project-specific context

## Tools and Commands

Available slash commands:

- `/install` - Install all project dependencies
- `/prime` - Load project context
- `/bug <issue>` - Process bug fix
- `/feature <issue>` - Implement feature
- `/chore <issue>` - Process maintenance task

## Resources

- [ADW Documentation](adws/README.md)
- [IPE Documentation](ipe/README.md)
- [Terraform Documentation](io/terraform/README.md)
- [Application Documentation](app/README.md)
