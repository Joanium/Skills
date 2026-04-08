---
name: Component Testing
trigger: component testing, react testing library, component test, UI testing, vitest component, storybook testing, test a component, frontend unit test, test react component, vue component test, snapshot test
description: Write effective component tests for React, Vue, and other UI frameworks. Covers testing strategy, React Testing Library patterns, accessibility queries, interaction testing, mocking, and Storybook integration.
---

# ROLE
You are a senior frontend engineer. Component tests give you confidence that UI works correctly — from the user's perspective, not the implementation's perspective. Test behavior, not code structure. If you refactor internals and all tests pass, your tests are good.

# CORE PRINCIPLES
```
TEST BEHAVIOR, NOT IMPLEMENTATION:  Query by role and label, not className or testId.
THE MORE TESTS RESEMBLE USER USE:   The more confidence they give. (Guiding Testing Library principle)
ACCESSIBLE QUERIES ARE GOOD TESTS:  If you can't query by role, your component may not be accessible.
MOCK AT THE BOUNDARY:               Mock network calls, not internal functions.
ONE ASSERTION CONCEPT PER TEST:     Tests should fail for one specific reason.
```

# TEST STRATEGY — WHAT TO TEST
```
TEST THIS:
  ✓ User interactions produce correct UI changes (click, type, submit)
  ✓ Conditional rendering based on props/state (loading, error, empty states)
  ✓ Form validation messages appear correctly
  ✓ Accessible attributes (aria-*, role, label associations)
  ✓ Integration of child components (what the user sees, not which child was used)
  ✓ Edge cases: empty data, long strings, 0 items, max limits

DON'T TEST THIS:
  ✗ CSS class names (implementation detail — refactor breaks tests with no benefit)
  ✗ Internal state variable names
  ✗ Which child component is rendered (test output, not which component produced it)
  ✗ Third-party library internals (trust they work)
  ✗ Snapshot tests for large component trees (fragile, low signal)
```

# SETUP — REACT TESTING LIBRARY
```bash
# Installation
npm install -D @testing-library/react @testing-library/user-event @testing-library/jest-dom vitest jsdom

# vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: true,
  },
});

# src/test/setup.ts
import '@testing-library/jest-dom';
```

# QUERY PRIORITY — USE IN THIS ORDER
```
1. getByRole          — matches ARIA role + accessible name (BEST — reflects real accessibility)
2. getByLabelText     — matches form labels
3. getByPlaceholderText — last resort for inputs without labels
4. getByText          — visible text content
5. getByDisplayValue  — current value of form elements

6. getByTestId        — LAST RESORT — means no accessible selector exists (fix the component)

NEVER:
  ✗ document.querySelector('.submit-button')
  ✗ wrapper.find('button') (enzyme style)
  ✗ container.firstChild (fragile)
```

# BASIC PATTERNS
```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PostCard } from './PostCard';

// Describe blocks mirror component behavior areas
describe('PostCard', () => {
  const defaultPost = {
    id: '1',
    title: 'Hello World',
    body: 'This is the body.',
    likeCount: 5,
    isLiked: false,
  };

  // Render helper to reduce duplication
  const renderPostCard = (props = {}) =>
    render(<PostCard post={{ ...defaultPost, ...props }} onLike={vi.fn()} />);

  it('renders the post title and body', () => {
    renderPostCard();
    expect(screen.getByRole('heading', { name: 'Hello World' })).toBeInTheDocument();
    expect(screen.getByText('This is the body.')).toBeInTheDocument();
  });

  it('shows like count', () => {
    renderPostCard({ likeCount: 42 });
    // Match accessible button name which includes the count
    expect(screen.getByRole('button', { name: /42 likes/i })).toBeInTheDocument();
  });

  it('calls onLike with post id when like button clicked', async () => {
    const onLike = vi.fn();
    render(<PostCard post={defaultPost} onLike={onLike} />);

    await userEvent.click(screen.getByRole('button', { name: /like/i }));

    expect(onLike).toHaveBeenCalledOnce();
    expect(onLike).toHaveBeenCalledWith('1');
  });

  it('shows filled heart icon when post is already liked', () => {
    renderPostCard({ isLiked: true });
    expect(screen.getByRole('button', { name: /unlike/i })).toBeInTheDocument();
  });
});
```

# ASYNC & LOADING STATES
```typescript
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PostsList } from './PostsList';
import { fetchPosts } from '../api/posts';

vi.mock('../api/posts');

describe('PostsList', () => {
  it('shows loading state initially', () => {
    vi.mocked(fetchPosts).mockImplementation(() => new Promise(() => {})); // never resolves
    render(<PostsList />);
    expect(screen.getByRole('status', { name: /loading/i })).toBeInTheDocument();
  });

  it('renders posts after successful fetch', async () => {
    vi.mocked(fetchPosts).mockResolvedValue([
      { id: '1', title: 'First Post' },
      { id: '2', title: 'Second Post' },
    ]);

    render(<PostsList />);

    // Wait for async state update
    expect(await screen.findByText('First Post')).toBeInTheDocument();
    expect(screen.getByText('Second Post')).toBeInTheDocument();
    expect(screen.queryByRole('status')).not.toBeInTheDocument(); // loading gone
  });

  it('shows error message when fetch fails', async () => {
    vi.mocked(fetchPosts).mockRejectedValue(new Error('Network error'));

    render(<PostsList />);

    expect(await screen.findByRole('alert')).toHaveTextContent(/failed to load/i);
  });

  it('shows empty state when no posts returned', async () => {
    vi.mocked(fetchPosts).mockResolvedValue([]);

    render(<PostsList />);

    expect(await screen.findByText(/no posts yet/i)).toBeInTheDocument();
  });
});
```

# FORM TESTING
```typescript
describe('ContactForm', () => {
  it('submits form with correct data', async () => {
    const onSubmit = vi.fn();
    render(<ContactForm onSubmit={onSubmit} />);

    // Use userEvent for realistic interaction (fires all events: focus, input, blur)
    await userEvent.type(screen.getByLabelText(/name/i), 'Alice');
    await userEvent.type(screen.getByLabelText(/email/i), 'alice@example.com');
    await userEvent.type(screen.getByLabelText(/message/i), 'Hello there');
    await userEvent.click(screen.getByRole('button', { name: /send/i }));

    expect(onSubmit).toHaveBeenCalledWith({
      name: 'Alice',
      email: 'alice@example.com',
      message: 'Hello there',
    });
  });

  it('shows validation errors for empty submission', async () => {
    render(<ContactForm onSubmit={vi.fn()} />);

    await userEvent.click(screen.getByRole('button', { name: /send/i }));

    expect(screen.getByText(/name is required/i)).toBeInTheDocument();
    expect(screen.getByText(/email is required/i)).toBeInTheDocument();
  });

  it('shows invalid email error', async () => {
    render(<ContactForm onSubmit={vi.fn()} />);

    await userEvent.type(screen.getByLabelText(/email/i), 'not-an-email');
    await userEvent.tab(); // blur triggers validation

    expect(screen.getByText(/valid email/i)).toBeInTheDocument();
  });

  it('disables submit button while submitting', async () => {
    const onSubmit = vi.fn(() => new Promise(() => {})); // never resolves
    render(<ContactForm onSubmit={onSubmit} />);

    await userEvent.type(screen.getByLabelText(/name/i), 'Alice');
    await userEvent.click(screen.getByRole('button', { name: /send/i }));

    expect(screen.getByRole('button', { name: /send/i })).toBeDisabled();
  });
});
```

# CUSTOM HOOKS TESTING
```typescript
import { renderHook, act } from '@testing-library/react';
import { useCounter } from './useCounter';

describe('useCounter', () => {
  it('starts at initial value', () => {
    const { result } = renderHook(() => useCounter(5));
    expect(result.current.count).toBe(5);
  });

  it('increments count', () => {
    const { result } = renderHook(() => useCounter(0));
    act(() => result.current.increment());
    expect(result.current.count).toBe(1);
  });

  it('does not exceed maximum', () => {
    const { result } = renderHook(() => useCounter(9, { max: 10 }));
    act(() => { result.current.increment(); result.current.increment(); });
    expect(result.current.count).toBe(10); // capped, not 11
  });
});
```

# CONTEXT & PROVIDERS
```typescript
// Test wrapper with all providers
function renderWithProviders(ui: ReactElement, options = {}) {
  function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
        <AuthProvider>
          <ThemeProvider theme="light">
            {children}
          </ThemeProvider>
        </AuthProvider>
      </QueryClientProvider>
    );
  }
  return render(ui, { wrapper: Wrapper, ...options });
}

// Use in tests
it('shows admin panel for admin users', () => {
  renderWithProviders(<Dashboard />, {
    wrapper: ({ children }) => (
      <AuthProvider initialUser={{ role: 'admin' }}>
        {children}
      </AuthProvider>
    )
  });
  expect(screen.getByText(/admin panel/i)).toBeInTheDocument();
});
```

# STORYBOOK INTEGRATION
```typescript
// Post.stories.tsx — stories double as visual tests + interaction tests
import type { Meta, StoryObj } from '@storybook/react';
import { expect, userEvent, within } from '@storybook/test';
import { PostCard } from './PostCard';

const meta: Meta<typeof PostCard> = {
  component: PostCard,
  args: {
    post: { id: '1', title: 'Hello', body: 'World', likeCount: 0, isLiked: false },
    onLike: fn(),
  },
};
export default meta;

export const Default: StoryObj = {};

export const Liked: StoryObj = {
  args: { post: { ...meta.args!.post, isLiked: true, likeCount: 1 } },
};

// Interaction test — runs in Storybook and in CI via test-storybook
export const LikeInteraction: StoryObj = {
  play: async ({ canvasElement, args }) => {
    const canvas = within(canvasElement);
    await userEvent.click(canvas.getByRole('button', { name: /like/i }));
    await expect(args.onLike).toHaveBeenCalledWith('1');
  },
};
```

# COVERAGE CHECKLIST
```
For each component, ensure tests cover:
  [ ] Happy path render with typical props
  [ ] All conditional render paths (if/else, loading/error/empty/populated)
  [ ] All user interactions (click, type, submit, keyboard navigation)
  [ ] Edge case props (0 items, max-length strings, null/undefined optional props)
  [ ] Error states and recovery
  [ ] Accessible attributes are correct (labels, roles, aria-*)
  [ ] Integration with parent (props passed correctly)
```
