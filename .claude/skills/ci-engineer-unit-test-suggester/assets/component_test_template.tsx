/**
 * Component Test Template
 *
 * This template demonstrates best practices for testing React components
 * with React Testing Library and Vitest.
 *
 * Replace COMPONENT_NAME with your actual component name.
 */

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import COMPONENT_NAME from './COMPONENT_NAME';
import type { Props } from './COMPONENT_NAME';

// ==============================================================================
// MOCKS
// ==============================================================================

// Mock child components to isolate test
vi.mock('./ChildComponent', () => ({
  default: ({ someProp }: { someProp: string }) => (
    <div data-testid="child-component">Child: {someProp}</div>
  ),
}));

// Mock Next.js modules
vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock('next/image', () => ({
  default: (props: any) => <img {...props} />,
}));

// Mock external dependencies
vi.mock('@/lib/utils', () => ({
  formatDate: vi.fn((date) => date.toISOString()),
}));

// ==============================================================================
// TEST DATA FACTORIES
// ==============================================================================

/**
 * Create test props with sensible defaults
 * Override specific props as needed
 */
const createTestProps = (overrides: Partial<Props> = {}): Props => ({
  // Required props
  id: 1,
  title: 'Test Title',
  description: 'Test description',

  // Optional props with defaults
  isActive: false,
  items: [],

  // Merge overrides
  ...overrides,
});

// ==============================================================================
// TEST SUITE
// ==============================================================================

describe('COMPONENT_NAME', () => {
  // ==============================================================================
  // SETUP & TEARDOWN
  // ==============================================================================

  beforeEach(() => {
    // Clear all mocks before each test
    vi.clearAllMocks();
  });

  // ==============================================================================
  // CORE RENDERING TESTS
  // ==============================================================================

  describe('Core Rendering', () => {
    it('renders component with required props', () => {
      // Arrange
      const props = createTestProps({ title: 'My Title' });

      // Act
      render(<COMPONENT_NAME {...props} />);

      // Assert
      expect(screen.getByRole('heading', { name: /my title/i })).toBeInTheDocument();
    });

    it('renders description text', () => {
      // Arrange
      const props = createTestProps({ description: 'Test description content' });

      // Act
      render(<COMPONENT_NAME {...props} />);

      // Assert
      expect(screen.getByText('Test description content')).toBeInTheDocument();
    });

    it('renders with accessible markup', () => {
      // Arrange
      const props = createTestProps();

      // Act
      render(<COMPONENT_NAME {...props} />);

      // Assert - Use accessible queries
      expect(screen.getByRole('main')).toBeInTheDocument();
    });
  });

  // ==============================================================================
  // CONDITIONAL RENDERING
  // ==============================================================================

  describe('Conditional Rendering', () => {
    it('renders optional section when data is present', () => {
      // Arrange
      const props = createTestProps({ items: ['Item 1', 'Item 2'] });

      // Act
      render(<COMPONENT_NAME {...props} />);

      // Assert
      expect(screen.getByRole('list')).toBeInTheDocument();
      expect(screen.getByText('Item 1')).toBeInTheDocument();
    });

    it('does not render optional section when data is missing', () => {
      // Arrange
      const props = createTestProps({ items: [] });

      // Act
      render(<COMPONENT_NAME {...props} />);

      // Assert - Use queryBy for absence checks
      expect(screen.queryByRole('list')).not.toBeInTheDocument();
    });

    it('shows active state when isActive is true', () => {
      // Arrange
      const props = createTestProps({ isActive: true });

      // Act
      render(<COMPONENT_NAME {...props} />);

      // Assert
      expect(screen.getByTestId('active-indicator')).toBeInTheDocument();
    });

    it('hides active state when isActive is false', () => {
      // Arrange
      const props = createTestProps({ isActive: false });

      // Act
      render(<COMPONENT_NAME {...props} />);

      // Assert
      expect(screen.queryByTestId('active-indicator')).not.toBeInTheDocument();
    });
  });

  // ==============================================================================
  // USER INTERACTIONS
  // ==============================================================================

  describe('User Interactions', () => {
    it('calls onClick handler when button is clicked', async () => {
      // Arrange
      const user = userEvent.setup();
      const onClickMock = vi.fn();
      const props = createTestProps({ onClick: onClickMock });

      // Act
      render(<COMPONENT_NAME {...props} />);
      const button = screen.getByRole('button', { name: /click me/i });
      await user.click(button);

      // Assert
      expect(onClickMock).toHaveBeenCalledTimes(1);
    });

    it('updates input value when user types', async () => {
      // Arrange
      const user = userEvent.setup();
      const props = createTestProps();

      // Act
      render(<COMPONENT_NAME {...props} />);
      const input = screen.getByRole('textbox', { name: /search/i });
      await user.type(input, 'test query');

      // Assert
      expect(input).toHaveValue('test query');
    });

    it('toggles checkbox when clicked', async () => {
      // Arrange
      const user = userEvent.setup();
      const props = createTestProps();

      // Act
      render(<COMPONENT_NAME {...props} />);
      const checkbox = screen.getByRole('checkbox', { name: /enable/i });

      // Initially unchecked
      expect(checkbox).not.toBeChecked();

      // Click to check
      await user.click(checkbox);
      expect(checkbox).toBeChecked();

      // Click to uncheck
      await user.click(checkbox);
      expect(checkbox).not.toBeChecked();
    });
  });

  // ==============================================================================
  // CHILD COMPONENTS
  // ==============================================================================

  describe('Child Components', () => {
    it('renders child component with correct props', () => {
      // Arrange
      const props = createTestProps({ childProp: 'test value' });

      // Act
      render(<COMPONENT_NAME {...props} />);

      // Assert
      expect(screen.getByTestId('child-component')).toBeInTheDocument();
      expect(screen.getByText(/child: test value/i)).toBeInTheDocument();
    });
  });

  // ==============================================================================
  // ACCESSIBILITY
  // ==============================================================================

  describe('Accessibility', () => {
    it('has accessible heading hierarchy', () => {
      // Arrange
      const props = createTestProps();

      // Act
      render(<COMPONENT_NAME {...props} />);

      // Assert
      const headings = screen.getAllByRole('heading');
      expect(headings).toHaveLength(2);
      expect(headings[0]).toHaveAttribute('aria-level', '1'); // h1
      expect(headings[1]).toHaveAttribute('aria-level', '2'); // h2
    });

    it('provides alt text for images', () => {
      // Arrange
      const props = createTestProps({ imageAlt: 'Descriptive alt text' });

      // Act
      render(<COMPONENT_NAME {...props} />);

      // Assert
      const image = screen.getByRole('img', { name: /descriptive alt text/i });
      expect(image).toBeInTheDocument();
    });

    it('associates labels with form inputs', () => {
      // Arrange
      const props = createTestProps();

      // Act
      render(<COMPONENT_NAME {...props} />);

      // Assert - getByLabelText verifies label association
      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    });
  });

  // ==============================================================================
  // EDGE CASES
  // ==============================================================================

  describe('Edge Cases', () => {
    it('handles empty array gracefully', () => {
      // Arrange
      const props = createTestProps({ items: [] });

      // Act
      render(<COMPONENT_NAME {...props} />);

      // Assert - Component should not crash
      expect(screen.queryByRole('list')).not.toBeInTheDocument();
    });

    it('handles very long title', () => {
      // Arrange
      const longTitle = 'A'.repeat(200);
      const props = createTestProps({ title: longTitle });

      // Act
      render(<COMPONENT_NAME {...props} />);

      // Assert
      expect(screen.getByRole('heading', { name: new RegExp(longTitle) })).toBeInTheDocument();
    });

    it('handles special characters in text', () => {
      // Arrange
      const props = createTestProps({ description: 'Test & Special <Characters>' });

      // Act
      render(<COMPONENT_NAME {...props} />);

      // Assert
      expect(screen.getByText(/test & special <characters>/i)).toBeInTheDocument();
    });
  });

  // ==============================================================================
  // ASYNC BEHAVIOR (if applicable)
  // ==============================================================================

  describe('Async Behavior', () => {
    it('shows loading state initially', async () => {
      // Arrange
      const props = createTestProps({ isLoading: true });

      // Act
      render(<COMPONENT_NAME {...props} />);

      // Assert
      expect(screen.getByText(/loading/i)).toBeInTheDocument();
    });

    it('shows data after loading completes', async () => {
      // Arrange
      const props = createTestProps({ isLoading: false, data: 'Test Data' });

      // Act
      render(<COMPONENT_NAME {...props} />);

      // Assert - Use findBy for async elements
      const content = await screen.findByText(/test data/i);
      expect(content).toBeInTheDocument();
    });
  });
});
