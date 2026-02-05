/// <reference types="vitest" />
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    // Use global test APIs (describe, it, expect) without imports
    globals: true,

    // Use jsdom for React component testing (simulates browser environment)
    environment: 'jsdom',

    // Setup file runs before each test file
    setupFiles: ['./vitest.setup.ts'],

    // Pattern for test files
    include: ['**/*.{test,spec}.{ts,tsx}'],

    // Exclude patterns
    exclude: [
      'node_modules',
      'dist',
      '.next',
      'coverage',
      '**/*.d.ts',
    ],

    // Coverage configuration
    coverage: {
      // Coverage provider (v8 is faster, istanbul is more accurate)
      provider: 'v8', // or 'istanbul'

      // Reporters for coverage output
      reporter: ['text', 'json', 'html', 'lcov'],

      // Coverage thresholds (CI fails if below these)
      thresholds: {
        statements: 70,
        branches: 65,
        functions: 70,
        lines: 70,
      },

      // Automatically update thresholds as coverage improves
      thresholdAutoUpdate: false,

      // Files to exclude from coverage
      exclude: [
        'node_modules/',
        'dist/',
        '.next/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/test-utils/**',
        '**/*.test.ts',
        '**/*.test.tsx',
        'coverage/**',
      ],

      // Only include source files in coverage
      include: [
        'lib/**/*.ts',
        'components/**/*.tsx',
        'utils/**/*.ts',
      ],
    },

    // Timeout for tests (milliseconds)
    testTimeout: 10000,

    // Timeout for hooks (beforeAll, afterAll, etc.)
    hookTimeout: 10000,

    // Clear mocks between tests
    clearMocks: true,

    // Restore mocks between tests
    restoreMocks: true,

    // Reset mocks between tests
    resetMocks: true,
  },

  // Path aliases (match tsconfig.json)
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './'),
    },
  },
});
