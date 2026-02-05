# {{PROJECT_NAME}} Website Validation Test Suite

Execute comprehensive validation tests for the {{PROJECT_NAME}} Next.js website, returning results in a standardized JSON format for automated processing.

## Purpose

Proactively identify and fix issues in the application before they impact users or developers. By running this comprehensive test suite, you can:
- Detect syntax errors, type mismatches, and import failures
- Identify broken tests or security vulnerabilities  
- Verify build processes and dependencies
- Ensure the application is in a healthy state

## Variables

TEST_COMMAND_TIMEOUT: 5 minutes

## Instructions

- Execute each test in the sequence provided below
- Capture the result (passed/failed) and any error messages
- IMPORTANT: Return ONLY the JSON array with test results
  - IMPORTANT: Do not include any additional text, explanations, or markdown formatting
  - We'll immediately run JSON.parse() on the output, so make sure it's valid JSON
- If a test passes, omit the error field
- If a test fails, include the error message in the error field
- Execute all tests even if some fail
- Error Handling:
  - If a command returns non-zero exit code, mark as failed and immediately stop processing tests
  - Capture stderr output for error field
  - Timeout commands after `TEST_COMMAND_TIMEOUT`
  - IMPORTANT: If a test fails, stop processing tests and return the results thus far
- Some tests may have dependencies (e.g., server must be stopped for port availability)
- API health check is required
- Test execution order is important - dependencies should be validated first
- All file paths are relative to the project root
- Always run `pwd` and `cd` before each test to ensure you're operating in the correct directory for the given test

## Test Execution Sequence

### Next.js Website Tests

1. **TypeScript Type Check**
   - Preparation Command: None
   - Command: `cd app/ && bun tsc --noEmit` or `cd app/ && npm run tsc --noEmit`
   - test_name: "typescript_check"
   - test_purpose: "Validates TypeScript type correctness without generating output files, catching type errors, missing imports, and incorrect function signatures"

2. **Next.js Linting**
   - Preparation Command: None
   - Command: `cd app/ && bun run lint` or `cd app/ && npm run lint`
   - test_name: "nextjs_linting"
   - test_purpose: "Validates Next.js code quality, identifies unused imports, style violations, accessibility issues, and React best practices"

3. **Production Build**
   - Preparation Command: None
   - Command: `cd app/ && bun run build` or `cd app/ && npm run build`
   - test_name: "production_build"
   - test_purpose: "Validates the complete Next.js build process including static export, bundling, asset optimization, and production compilation"

4. **Dependency Check**
   - Preparation Command: None
   - Command: `cd app/ && (test -d node_modules || echo "Missing dependencies")`
   - test_name: "dependency_check"
   - test_purpose: "Verifies that all npm/bun dependencies are installed correctly"

## Report

- IMPORTANT: Return results exclusively as a JSON array based on the `Output Structure` section below.
- Sort the JSON array with failed tests (passed: false) at the top
- Include all tests in the output, both passed and failed
- The execution_command field should contain the exact command that can be run to reproduce the test
- This allows subsequent agents to quickly identify and resolve errors

### Output Structure

```json
[
  {
    "test_name": "string",
    "passed": boolean,
    "execution_command": "string",
    "test_purpose": "string",
    "error": "optional string"
  },
  ...
]
```

### Example Output

```json
[
  {
    "test_name": "production_build",
    "passed": false,
    "execution_command": "cd app/ && bun run build",
    "test_purpose": "Validates the complete Next.js build process including static export, bundling, asset optimization, and production compilation",
    "error": "TS2345: Argument of type 'string' is not assignable to parameter of type 'number'"
  },
  {
    "test_name": "nextjs_linting",
    "passed": true,
    "execution_command": "cd app/ && bun run lint",
    "test_purpose": "Validates Next.js code quality, identifies unused imports, style violations, accessibility issues, and React best practices"
  },
  {
    "test_name": "typescript_check",
    "passed": true,
    "execution_command": "cd app/ && bun tsc --noEmit",
    "test_purpose": "Validates TypeScript type correctness without generating output files, catching type errors, missing imports, and incorrect function signatures"
  },
  {
    "test_name": "dependency_check",
    "passed": true,
    "execution_command": "cd app/ && (test -d node_modules || echo 'Missing dependencies')",
    "test_purpose": "Verifies that all npm/bun dependencies are installed correctly"
  }
]
```