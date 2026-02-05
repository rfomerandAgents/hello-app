# Install Worktree

**Note**: This command is designed for the legacy application structure (backend/frontend separation).

For the current {{PROJECT_NAME}} Next.js website, worktree setup is simpler as there's only one application running on port 3000.

## Legacy Parameters (Not applicable to current app)
- Worktree path: {0}
- Backend port: {1} (Legacy - not used in current Next.js app)
- Frontend port: {2} (Legacy - use 3000 for Next.js)

## Read
- .env (from parent repo, if exists)
- .mcp.json (from parent repo)
- playwright-mcp-config.json (from parent repo)

## Steps

1. **Navigate to worktree directory**
   ```bash
   cd {0}
   ```

2. **Copy environment files (if needed)**
   - Copy `.env` from parent repo if it exists
   - Note: Next.js app uses default port 3000, no custom port configuration needed

3. **Copy and configure MCP files**
   - Copy `.mcp.json` from parent repo if it exists
   - Copy `playwright-mcp-config.json` from parent repo if it exists
   - These files are needed for Model Context Protocol and Playwright automation

   After copying, update paths to use absolute paths:
   - Get the absolute worktree path: `WORKTREE_PATH=$(pwd)`
   - Update `.mcp.json`:
     - Find the line containing `"./playwright-mcp-config.json"`
     - Replace it with `"${WORKTREE_PATH}/playwright-mcp-config.json"`
     - Use a JSON-aware tool or careful string replacement to maintain valid JSON
   - Update `playwright-mcp-config.json`:
     - Find the line containing `"dir": "./videos"`
     - Replace it with `"dir": "${WORKTREE_PATH}/videos"`
     - Create the videos directory: `mkdir -p ${WORKTREE_PATH}/videos`
   - This ensures MCP configuration works correctly regardless of execution context

4. **Install Next.js website dependencies**
   ```bash
   cd app/ && bun install
   ```
   or
   ```bash
   cd app/ && npm install
   ```

## Error Handling
- If parent .env files don't exist, create minimal versions from .env.sample files
- Ensure all paths are absolute to avoid confusion

## Report
- List all files created/modified (including MCP configuration files)
- Confirm Next.js dependencies installed in app/
- Note: Website runs on default port 3000
- Note any missing parent .env files that need user attention
- Note any missing MCP configuration files
- Show the updated absolute paths in:
  - `.mcp.json` (should show full path to playwright-mcp-config.json)
  - `playwright-mcp-config.json` (should show full path to videos directory)
- Confirm videos directory was created