# E2E Test: {{TEST_NAME}}

Test that {{FEATURE_DESCRIPTION}}.

## User Story

As a {{USER_ROLE}}
I want to {{USER_ACTION}}
So that {{USER_BENEFIT}}

## Prerequisites

- Application running at `http://localhost:3000`
- Test data loaded (if applicable)

## Test Steps

1. Navigate to `http://localhost:3000/{{PATH}}`
2. Take a screenshot of the initial page state
3. **Verify** the page loads correctly
4. **Verify** expected content is displayed:
   - Item 1
   - Item 2
5. **Interact** with the feature (click, type, etc.)
6. Take a screenshot of the result
7. **Verify** the expected outcome

## Expected Results

- [ ] Page loads without errors
- [ ] Content displays correctly
- [ ] Interaction produces expected result
- [ ] No console errors

## Screenshots

Screenshots will be saved to `app_docs/assets/` with naming:
- `01_{{test_name}}_initial.png`
- `02_{{test_name}}_result.png`

## Notes

Add any additional context or edge cases to test.
