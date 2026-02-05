# MD5 Checksum Verification - Compare Local and Remote Files

Verify that a local file in the built static site matches its deployed version on the remote server by comparing MD5 checksums.

## Command Usage

```bash
/md5sum <file-path>
```

## Arguments

- `file-path` (string, required): Path to the file relative to `app/out/`. Examples:
  - `index.html`
  - `images/logo.png`
  - `pages/about/index.html`
  - `_next/static/...`

## Examples

```bash
# Check homepage
/md5sum index.html

# Check image file
/md5sum images/logo.png

# Check nested HTML
/md5sum pages/about/index.html

# Check Next.js static asset
/md5sum _next/static/chunks/main.js
```

## Instructions

You are executing the `/md5sum` command to verify that a local file matches its deployed version on https://{{PROJECT_DOMAIN}}.

### Step 1: Parse and Normalize the File Path

Extract the file path from the command argument (`$ARGUMENT`):

```bash
# Store the argument
FILE_PATH="$ARGUMENT"

# Strip leading slash if present
FILE_PATH="${FILE_PATH#/}"
```

If no argument provided, respond with:
```
Error: Missing file path argument

Usage: /md5sum <file-path>
Example: /md5sum images/logo.png
```

### Step 2: Verify Local File Exists

Check that the file exists in the local build directory:

```bash
LOCAL_FILE="app/out/${FILE_PATH}"

if [ ! -f "${LOCAL_FILE}" ]; then
  echo "Error: Local file not found: ${LOCAL_FILE}"
  echo ""
  echo "Suggestion: Make sure the file path is correct, or run 'bun run build' to rebuild the site."
  exit 1
fi
```

### Step 3: Calculate Local MD5 Checksum

Calculate the MD5 checksum of the local file, handling platform differences:

```bash
# Detect platform and use appropriate MD5 command
if command -v md5sum >/dev/null 2>&1; then
  # Linux/GitHub Actions
  LOCAL_MD5=$(md5sum "${LOCAL_FILE}" | awk '{print $1}')
elif command -v md5 >/dev/null 2>&1; then
  # macOS
  LOCAL_MD5=$(md5 -q "${LOCAL_FILE}")
else
  echo "Error: Neither md5sum nor md5 command found"
  echo "Cannot calculate checksums on this platform"
  exit 1
fi

echo "Local MD5:  ${LOCAL_MD5}"
```

### Step 4: Construct Remote URL

Build the remote URL by URL-encoding special characters if needed:

```bash
# For simple cases, construct URL directly
REMOTE_URL="https://{{PROJECT_DOMAIN}}/${FILE_PATH}"

# URL encode spaces and special characters if needed
# For now, we'll use the path as-is and rely on curl's handling
```

Display the URL being checked:
```bash
echo "Remote URL: ${REMOTE_URL}"
```

### Step 5: Fetch and Calculate Remote MD5 Checksum

Download the remote file and calculate its MD5 checksum:

```bash
# Use curl with timeout and follow redirects
# Check HTTP status and capture response
HTTP_STATUS=$(curl -s -o /tmp/remote_file_md5check -w "%{http_code}" \
  --connect-timeout 10 \
  --max-time 30 \
  -L \
  "${REMOTE_URL}" 2>&1)

# Check if curl succeeded
if [ $? -ne 0 ]; then
  echo ""
  echo "Error: Network error - could not connect to remote server"
  echo "Suggestion: Check your internet connection and try again"
  exit 1
fi

# Check HTTP status code
if [ "${HTTP_STATUS}" = "404" ]; then
  echo ""
  echo "Error: Remote file not found (404)"
  echo "The file exists locally but not on the remote server."
  echo ""
  echo "Suggestion: The site may need to be deployed. Run deployment command to push changes."
  rm -f /tmp/remote_file_md5check
  exit 1
elif [ "${HTTP_STATUS}" != "200" ]; then
  echo ""
  echo "Error: Unexpected HTTP status: ${HTTP_STATUS}"
  echo "Could not retrieve remote file"
  rm -f /tmp/remote_file_md5check
  exit 1
fi

# Calculate MD5 of downloaded file
if command -v md5sum >/dev/null 2>&1; then
  REMOTE_MD5=$(md5sum /tmp/remote_file_md5check | awk '{print $1}')
elif command -v md5 >/dev/null 2>&1; then
  REMOTE_MD5=$(md5 -q /tmp/remote_file_md5check)
fi

echo "Remote MD5: ${REMOTE_MD5}"

# Clean up temp file
rm -f /tmp/remote_file_md5check
```

### Step 6: Compare Checksums and Report

Compare the checksums and provide clear feedback:

```bash
echo ""

if [ "${LOCAL_MD5}" = "${REMOTE_MD5}" ]; then
  echo "✓ MATCH - Local and remote files are identical"
  echo ""
  echo "The deployed version matches your local build."
  exit 0
else
  echo "✗ MISMATCH - Files differ"
  echo ""
  echo "The local file differs from the deployed version."
  echo ""
  echo "Possible reasons:"
  echo "  1. Changes were made locally but not deployed yet"
  echo "  2. Remote cache may be serving an older version"
  echo "  3. Build artifacts differ between local and deployment"
  echo ""
  echo "Suggestions:"
  echo "  - Rebuild locally: bun run build"
  echo "  - Deploy changes: /terraform_deploy (or your deployment command)"
  echo "  - Wait for CDN cache to clear (if Cloudflare is caching)"
  exit 1
fi
```

## Error Handling Summary

Handle these scenarios gracefully:

1. **No argument provided**: Show usage and examples
2. **Local file missing**: Suggest running build or checking path
3. **Network timeout**: Suggest checking internet connection
4. **Remote 404**: Explain file not deployed, suggest deployment
5. **Remote other error**: Display HTTP status and suggest investigation
6. **MD5 command unavailable**: Error message about platform support
7. **Checksum mismatch**: Provide actionable suggestions

## Output Format

### Success (Match)
```
Local MD5:  abc123def456...
Remote URL: https://{{PROJECT_DOMAIN}}/images/logo.png
Remote MD5: abc123def456...

✓ MATCH - Local and remote files are identical

The deployed version matches your local build.
```

### Mismatch
```
Local MD5:  abc123def456...
Remote URL: https://{{PROJECT_DOMAIN}}/index.html
Remote MD5: xyz789uvw012...

✗ MISMATCH - Files differ

The local file differs from the deployed version.

Possible reasons:
  1. Changes were made locally but not deployed yet
  2. Remote cache may be serving an older version
  3. Build artifacts differ between local and deployment

Suggestions:
  - Rebuild locally: bun run build
  - Deploy changes: /terraform_deploy (or your deployment command)
  - Wait for CDN cache to clear (if Cloudflare is caching)
```

### Error
```
Error: Local file not found: app/out/nonexistent.png

Suggestion: Make sure the file path is correct, or run 'bun run build' to rebuild the site.
```

## Platform Compatibility

| Platform | MD5 Command | Supported |
|----------|-------------|-----------|
| macOS | `md5 -q` | Yes |
| Linux | `md5sum` | Yes |
| GitHub Actions | `md5sum` | Yes |
| Windows (Git Bash) | `md5sum` | Yes |

## Use Cases

- **Pre-deployment verification**: Check if local changes match what's deployed
- **Deployment validation**: Confirm deployment succeeded
- **Cache troubleshooting**: Verify CDN cache has updated
- **Bug investigation**: Check if production file matches expected version
- **Asset verification**: Confirm images/CSS/JS files are current

## Notes

- Checksums are calculated on the final file content, not the filename
- Binary files (images, fonts) and text files both work correctly
- gzip compression is handled transparently by curl
- Cloudflare cache may cause mismatches for recently deployed files
- The command respects URL case-sensitivity (nginx is case-sensitive)
