# Start the {{PROJECT_NAME}} Website

## Variables

PORT: Default to 3000 (Next.js default development port)

## Workflow

1. Check if a process is already running on port 3000:
   - Run: `lsof -i :3000`

2. If a process is running:
   - Just open it in the browser with `open http://localhost:3000`
   - Let the user know the website is already running

3. If no process is running on port 3000:
   - Navigate to app directory: `cd app/`
   - Check if dependencies are installed:
     - If `node_modules` doesn't exist, run `bun install` or `npm install`
   - Start the development server in background:
     - Run: `nohup bun dev > /dev/null 2>&1 &` or `nohup npm run dev > /dev/null 2>&1 &`
   - Wait for server to start: `sleep 3`
   - Open browser: `open http://localhost:3000`

4. Let the user know that the {{PROJECT_NAME}} website is running on http://localhost:3000 and the browser is open.

## Notes
- To stop the server: Find the process with `lsof -i :3000` and kill it with `kill <PID>`
- For production build: `cd app/ && bun run build`