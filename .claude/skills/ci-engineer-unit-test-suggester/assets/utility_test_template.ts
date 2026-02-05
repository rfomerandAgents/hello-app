/**
 * Utility Function Test Template
 *
 * This template demonstrates best practices for testing pure utility functions
 * using the AAA (Arrange, Act, Assert) pattern with Vitest.
 *
 * Replace FUNCTION_NAME and MODULE_NAME with your actual names.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { FUNCTION_NAME } from './MODULE_NAME';
import type { InputType, OutputType } from './MODULE_NAME';

// ==============================================================================
// MOCKS (if needed for module dependencies)
// ==============================================================================

// Mock external dependencies
vi.mock('./dependencies', () => ({
  externalFunction: vi.fn((input) => input * 2),
}));

// ==============================================================================
// TEST DATA FACTORIES
// ==============================================================================

/**
 * Create test input data with sensible defaults
 */
const createTestInput = (overrides: Partial<InputType> = {}): InputType => ({
  id: 1,
  name: 'Test Name',
  value: 42,
  ...overrides,
});

// ==============================================================================
// TEST SUITE
// ==============================================================================

describe('FUNCTION_NAME', () => {
  // ==============================================================================
  // SETUP & TEARDOWN
  // ==============================================================================

  beforeEach(() => {
    // Reset mocks before each test
    vi.clearAllMocks();
  });

  // ==============================================================================
  // HAPPY PATH TESTS
  // ==============================================================================

  describe('Happy Path', () => {
    it('returns expected output for valid input', () => {
      // Arrange - Set up test data
      const input = createTestInput({ name: 'Test', value: 10 });
      const expected = { /* expected output */ };

      // Act - Execute the function under test
      const result = FUNCTION_NAME(input);

      // Assert - Verify the outcome
      expect(result).toEqual(expected);
    });

    it('processes array of items correctly', () => {
      // Arrange
      const input = [
        createTestInput({ id: 1, value: 10 }),
        createTestInput({ id: 2, value: 20 }),
        createTestInput({ id: 3, value: 30 }),
      ];

      // Act
      const result = FUNCTION_NAME(input);

      // Assert
      expect(result).toHaveLength(3);
      expect(result.every(item => item.processed)).toBe(true);
    });

    it('handles single item correctly', () => {
      // Arrange
      const input = createTestInput({ value: 42 });

      // Act
      const result = FUNCTION_NAME(input);

      // Assert
      expect(result.value).toBe(42);
      expect(result).toMatchObject({ value: 42 });
    });
  });

  // ==============================================================================
  // EDGE CASES
  // ==============================================================================

  describe('Edge Cases', () => {
    it('handles empty array', () => {
      // Arrange
      const input: InputType[] = [];

      // Act
      const result = FUNCTION_NAME(input);

      // Assert
      expect(result).toEqual([]);
      expect(result).toHaveLength(0);
    });

    it('handles empty string', () => {
      // Arrange
      const input = createTestInput({ name: '' });

      // Act
      const result = FUNCTION_NAME(input);

      // Assert
      expect(result.name).toBe('');
    });

    it('handles zero value', () => {
      // Arrange
      const input = createTestInput({ value: 0 });

      // Act
      const result = FUNCTION_NAME(input);

      // Assert
      expect(result.value).toBe(0);
    });

    it('handles negative numbers', () => {
      // Arrange
      const input = createTestInput({ value: -42 });

      // Act
      const result = FUNCTION_NAME(input);

      // Assert
      expect(result.value).toBe(-42);
    });

    it('handles very large numbers', () => {
      // Arrange
      const input = createTestInput({ value: Number.MAX_SAFE_INTEGER });

      // Act
      const result = FUNCTION_NAME(input);

      // Assert
      expect(result.value).toBe(Number.MAX_SAFE_INTEGER);
    });
  });

  // ==============================================================================
  // NULL/UNDEFINED HANDLING
  // ==============================================================================

  describe('Null and Undefined Handling', () => {
    it('handles null input gracefully', () => {
      // Arrange
      const input = null;

      // Act
      const result = FUNCTION_NAME(input);

      // Assert
      expect(result).toBeNull(); // or appropriate default
    });

    it('handles undefined input gracefully', () => {
      // Arrange
      const input = undefined;

      // Act
      const result = FUNCTION_NAME(input);

      // Assert
      expect(result).toBeUndefined(); // or appropriate default
    });

    it('handles missing optional properties', () => {
      // Arrange
      const input = createTestInput({ optionalField: undefined });

      // Act
      const result = FUNCTION_NAME(input);

      // Assert
      expect(result).toBeDefined();
      expect(result.optionalField).toBeUndefined();
    });
  });

  // ==============================================================================
  // BOUNDARY CONDITIONS
  // ==============================================================================

  describe('Boundary Conditions', () => {
    it('handles minimum boundary value', () => {
      // Arrange
      const input = createTestInput({ value: 0 });

      // Act
      const result = FUNCTION_NAME(input);

      // Assert
      expect(result.value).toBe(0);
    });

    it('handles maximum boundary value', () => {
      // Arrange
      const input = createTestInput({ value: 100 });

      // Act
      const result = FUNCTION_NAME(input);

      // Assert
      expect(result.value).toBe(100);
    });

    it('handles first item in array', () => {
      // Arrange
      const items = [
        createTestInput({ id: 1 }),
        createTestInput({ id: 2 }),
      ];

      // Act
      const result = FUNCTION_NAME(items[0]);

      // Assert
      expect(result.id).toBe(1);
    });

    it('handles last item in array', () => {
      // Arrange
      const items = [
        createTestInput({ id: 1 }),
        createTestInput({ id: 2 }),
      ];

      // Act
      const result = FUNCTION_NAME(items[items.length - 1]);

      // Assert
      expect(result.id).toBe(2);
    });
  });

  // ==============================================================================
  // ERROR HANDLING
  // ==============================================================================

  describe('Error Handling', () => {
    it('throws error for invalid input type', () => {
      // Arrange
      const invalidInput = 'not-the-right-type' as any;

      // Act & Assert
      expect(() => FUNCTION_NAME(invalidInput)).toThrow();
    });

    it('throws descriptive error message', () => {
      // Arrange
      const invalidInput = { invalid: 'data' } as any;

      // Act & Assert
      expect(() => FUNCTION_NAME(invalidInput)).toThrow('Expected valid input');
    });

    it('does not throw for valid edge case', () => {
      // Arrange
      const input = createTestInput({ value: 0 });

      // Act & Assert
      expect(() => FUNCTION_NAME(input)).not.toThrow();
    });
  });

  // ==============================================================================
  // BUSINESS LOGIC
  // ==============================================================================

  describe('Business Logic', () => {
    it('filters items based on criteria', () => {
      // Arrange
      const items = [
        createTestInput({ id: 1, category: 'active' }),
        createTestInput({ id: 2, category: 'inactive' }),
        createTestInput({ id: 3, category: 'active' }),
      ];

      // Act
      const result = FUNCTION_NAME(items).filter(item => item.category === 'active');

      // Assert
      expect(result).toHaveLength(2);
      expect(result.every(item => item.category === 'active')).toBe(true);
    });

    it('transforms data correctly', () => {
      // Arrange
      const input = createTestInput({ name: 'Test', value: 10 });

      // Act
      const result = FUNCTION_NAME(input);

      // Assert
      expect(result.name).toBe('Test');
      expect(result.transformedValue).toBe(20); // 10 * 2
    });

    it('sorts items in correct order', () => {
      // Arrange
      const items = [
        createTestInput({ id: 3, name: 'C' }),
        createTestInput({ id: 1, name: 'A' }),
        createTestInput({ id: 2, name: 'B' }),
      ];

      // Act
      const result = FUNCTION_NAME(items).sort((a, b) => a.id - b.id);

      // Assert
      expect(result[0].id).toBe(1);
      expect(result[1].id).toBe(2);
      expect(result[2].id).toBe(3);
    });
  });

  // ==============================================================================
  // PARAMETERIZED TESTS (Test Multiple Cases Efficiently)
  // ==============================================================================

  describe('Parameterized Tests', () => {
    it.each([
      { input: 0, expected: 0 },
      { input: 1, expected: 2 },
      { input: 5, expected: 10 },
      { input: -3, expected: -6 },
    ])('multiplies $input by 2 to get $expected', ({ input, expected }) => {
      // Arrange
      const data = createTestInput({ value: input });

      // Act
      const result = FUNCTION_NAME(data);

      // Assert
      expect(result.value).toBe(expected);
    });

    const testCases: Array<[string, InputType, OutputType]> = [
      ['empty name', createTestInput({ name: '' }), { /* expected */ }],
      ['long name', createTestInput({ name: 'A'.repeat(100) }), { /* expected */ }],
      ['special chars', createTestInput({ name: 'Test & <Special>' }), { /* expected */ }],
    ];

    test.each(testCases)('handles %s correctly', (description, input, expected) => {
      const result = FUNCTION_NAME(input);
      expect(result).toEqual(expected);
    });
  });

  // ==============================================================================
  // IMMUTABILITY (if applicable)
  // ==============================================================================

  describe('Immutability', () => {
    it('does not mutate input array', () => {
      // Arrange
      const input = [
        createTestInput({ id: 1 }),
        createTestInput({ id: 2 }),
      ];
      const originalInput = [...input]; // Copy for comparison

      // Act
      const result = FUNCTION_NAME(input);

      // Assert
      expect(input).toEqual(originalInput); // Input unchanged
      expect(result).not.toBe(input); // New array returned
    });

    it('does not mutate input object', () => {
      // Arrange
      const input = createTestInput({ name: 'Original' });
      const originalName = input.name;

      // Act
      const result = FUNCTION_NAME(input);

      // Assert
      expect(input.name).toBe(originalName); // Input unchanged
      expect(result).not.toBe(input); // New object returned
    });
  });

  // ==============================================================================
  // INTEGRATION WITH DEPENDENCIES
  // ==============================================================================

  describe('Integration with Dependencies', () => {
    it('calls external function with correct arguments', () => {
      // Arrange
      const input = createTestInput({ value: 10 });
      const externalFunctionMock = vi.fn((x) => x * 2);

      // Act
      FUNCTION_NAME(input);

      // Assert
      expect(externalFunctionMock).toHaveBeenCalledWith(10);
      expect(externalFunctionMock).toHaveBeenCalledTimes(1);
    });

    it('uses result from external function', () => {
      // Arrange
      const input = createTestInput({ value: 5 });
      const externalFunctionMock = vi.fn(() => 100);

      // Act
      const result = FUNCTION_NAME(input);

      // Assert
      expect(result.value).toBe(100); // Uses mocked return value
    });
  });
});

// ==============================================================================
// ADDITIONAL NOTES
// ==============================================================================

/*
 * BEST PRACTICES:
 *
 * 1. Use AAA pattern (Arrange, Act, Assert)
 * 2. Test one behavior per test
 * 3. Use descriptive test names
 * 4. Group related tests with describe blocks
 * 5. Test edge cases (null, undefined, empty, zero)
 * 6. Test boundary conditions
 * 7. Verify function doesn't mutate inputs (if pure)
 * 8. Use parameterized tests for similar cases
 * 9. Mock external dependencies
 * 10. Keep tests simple and readable
 */
