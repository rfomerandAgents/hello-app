# Prepare {{PROJECT_NAME}} Website

Setup the {{PROJECT_NAME}} website for review or test.

## Variables

PORT: 3000 (Next.js default development port)

## Setup

1. Navigate to app directory:
   - Run: `cd app/`

2. Install dependencies (if needed):
   - Check if `node_modules` exists
   - If not, run: `bun install` or `npm install`

3. Clear Next.js cache (optional, for fresh start):
   - Run: `rm -rf .next`

4. Start the development server:
   - Run in background: `nohup bun dev > /dev/null 2>&1 &`
   - Or with npm: `nohup npm run dev > /dev/null 2>&1 &`
   - Wait for startup: `sleep 3`

5. Verify the website is running:
   - Check if server is running: `lsof -i :3000`
   - The website should be accessible at http://localhost:3000
   - Open browser: `open http://localhost:3000`

6. Let the user know the website is ready for review/testing

## Notes
- To stop the server: `lsof -i :3000 | grep LISTEN | awk '{print $2}' | xargs kill`
- For production build: `cd app/ && bun run build`
- Read `app/README.md` for more information about the website

