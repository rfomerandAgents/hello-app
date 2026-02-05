# Watch GitHub Issue Until Completion

Monitor a GitHub issue in real-time, displaying all changes until the issue is closed or you interrupt the watch.

## Command

`/watch_issue <issue-number>`

## Arguments

- `<issue-number>`: GitHub issue number (integer, required)

## What This Does

Continuously polls a specific GitHub issue every 30 seconds and displays:
- State changes (open → closed)
- New comments added (with preview)
- Label changes (added/removed)
- Assignee changes (assigned/unassigned)
- Any other updates to the issue

The watch continues until:
- The issue is closed (automatic stop)
- You press Ctrl+C (manual stop)

## Run

Execute the watch script with the issue number:

!`uv run shared/watch_issue.py $ARGUMENT`

The script will:
1. Display initial issue information
2. Begin polling every 30 seconds
3. Show changes as they occur
4. Stop automatically when issue is closed
5. Allow manual stop with Ctrl+C

## Examples

Watch issue #42:
```
/watch_issue 42
```

Watch issue #123:
```
/watch_issue 123
```

## Output Example

```
============================================================
GitHub Issue Watcher
============================================================
Repository: your-username/{{PROJECT_DOMAIN}}
Issue Number: #42
Poll Interval: 30 seconds
Press Ctrl+C to stop watching
============================================================

Fetching initial issue state...

[2024-01-15 14:30:00] Poll #1 - Changes detected:
  • Started watching issue #42: Fix authentication bug

Watching for changes...

[2024-01-15 14:30:30] Poll #2 - No changes (state: OPEN)
[2024-01-15 14:31:00] Poll #3 - Changes detected:
  • Labels added: in_progress
  • Assigned to: bender-io

[2024-01-15 14:31:30] Poll #4 - No changes (state: OPEN)
[2024-01-15 14:32:00] Poll #5 - Changes detected:
  • New comments: 1 comment(s) added
  • └─ claude-bot: I'm working on this issue now. Creating a branch...

[2024-01-15 14:35:00] Poll #11 - Changes detected:
  • State changed: OPEN → CLOSED

✓ Issue #42 has been closed!
  Title: Fix authentication bug
  Closed at: 2024-01-15T14:35:00Z

Stopping watch...

============================================================
Watched issue #42 for 11 polls
Watch session ended
============================================================
```

## Use Cases

- **Monitor ADW/IPE workflows**: Watch issues being processed by automated workflows
- **Track critical bugs**: Keep an eye on high-priority issues until resolution
- **Collaboration awareness**: See when team members comment or make changes
- **Completion notification**: Get notified immediately when an issue is closed
- **Development tracking**: Monitor issues you're working on for external updates

## Notes

- Polls every 30 seconds (not real-time, but frequent enough for most use cases)
- Requires GitHub CLI (`gh`) to be installed and authenticated
- Uses existing GitHub API functions from `shared/github.py`
- Gracefully handles temporary network errors (continues watching)
- Minimal output when no changes (single line with carriage return)
- Detailed output when changes detected
- Automatic stop when issue is closed

## Troubleshooting

**Error: "GitHub CLI not authenticated"**
- Run: `gh auth login`
- Follow the prompts to authenticate

**Error: "Issue not found"**
- Verify the issue number exists in the repository
- Check that you have access to the repository

**Script exits immediately:**
- Check if the issue is already closed
- Verify you have network connectivity
- Check GitHub API rate limits with: `gh api rate_limit`

**Want to stop watching:**
- Press Ctrl+C to gracefully stop
- The script will show a summary before exiting
