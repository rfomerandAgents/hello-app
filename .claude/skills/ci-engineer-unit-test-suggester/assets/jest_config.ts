import type { Config } from 'jest';
import nextJest from 'next/jest';

// Create Jest config for Next.js
const createJestConfig = nextJest({
  // Path to Next.js app
  dir: './',
});

// Jest configuration
const config: Config = {
  // Test environment (jsdom for React components)
  testEnvironment: 'jsdom',

  // Setup files (runs before each test file)
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],

  // Test file patterns
  testMatch: [
    '**/__tests__/**/*.{ts,tsx}',
    '**/*.{test,spec}.{ts,tsx}',
  ],

  // Module name mapping (path aliases)
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },

  // TypeScript transformation
  transform: {
    '^.+\\.tsx?$': ['ts-jest', {
      tsconfig: {
        jsx: 'react-jsx',
      },
    }],
  },

  // Coverage configuration
  collectCoverageFrom: [
    'lib/**/*.{ts,tsx}',
    'components/**/*.{ts,tsx}',
    'utils/**/*.{ts,tsx}',
    '!**/*.d.ts',
    '!**/*.config.*',
    '!**/node_modules/**',
    '!**/.next/**',
    '!**/coverage/**',
    '!**/test-utils/**',
  ],

  // Coverage thresholds
  coverageThreshold: {
    global: {
      statements: 70,
      branches: 65,
      functions: 70,
      lines: 70,
    },
  },

  // Coverage reporters
  coverageReporters: ['text', 'lcov', 'html'],

  // Files to ignore
  testPathIgnorePatterns: [
    '/node_modules/',
    '/.next/',
    '/dist/',
    '/coverage/',
  ],

  // Module file extensions
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json'],

  // Clear mocks between tests
  clearMocks: true,

  // Restore mocks between tests
  restoreMocks: true,

  // Reset mocks between tests
  resetMocks: true,

  // Timeout for tests
  testTimeout: 10000,

  // Verbose output
  verbose: true,
};

// Export Jest config (Next.js will merge with its defaults)
export default createJestConfig(config);
