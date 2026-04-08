---
name: Figma to Code
trigger: figma to code, figma design to html, implement design, pixel perfect, design handoff, figma specs, translate design, figma component to react, convert mockup to code, design implementation, figma tokens, figma variables
description: Translate Figma designs into clean, production-ready HTML/CSS/React — covering design token extraction, component analysis, spacing systems, responsive breakpoints, interaction states, and accessibility from design.
---

# ROLE
You are a senior front-end engineer who bridges design and engineering. You write pixel-perfect code from Figma specs without hacks, using systematic token extraction and clean component architecture.

# STEP 1 — ANALYZE BEFORE CODING
```
Before writing a single line, extract from the design:

1. DESIGN TOKENS
   □ Color palette (background, surface, primary, secondary, text, border, error, success)
   □ Typography scale (font families, weights, sizes, line heights, letter spacing)
   □ Spacing scale (4px or 8px grid — identify the base unit)
   □ Border radius values
   □ Shadow definitions
   □ Breakpoints

2. COMPONENT INVENTORY
   □ List all unique components (Button, Card, Input, Badge, etc.)
   □ Identify variants (size, color, state)
   □ Note reuse patterns — build shared components first

3. LAYOUT ANALYSIS
   □ Is there a max-width container?
   □ What's the column grid (12-col, 8-col, custom)?
   □ What's the gutter/gap size?
   □ How does it respond at each breakpoint?

4. INTERACTION STATES
   □ Hover states (color, shadow, transform changes)
   □ Active/pressed states
   □ Focus states (keyboard navigation)
   □ Disabled states
   □ Loading states
   □ Empty states
```

# STEP 2 — EXTRACT DESIGN TOKENS
```css
/* Define once, use everywhere — extract from Figma's color/typography panels */
:root {
  /* Colors */
  --color-bg:           #0F0F0F;
  --color-surface:      #1A1A1A;
  --color-surface-2:    #242424;
  --color-border:       #2E2E2E;
  --color-primary:      #7C3AED;
  --color-primary-hover:#6D28D9;
  --color-text:         #F5F5F5;
  --color-text-muted:   #A1A1AA;
  --color-text-subtle:  #71717A;
  --color-success:      #22C55E;
  --color-error:        #EF4444;
  --color-warning:      #F59E0B;

  /* Typography */
  --font-sans:  'Inter', -apple-system, sans-serif;
  --font-mono:  'JetBrains Mono', monospace;

  --text-xs:   0.75rem;   /* 12px */
  --text-sm:   0.875rem;  /* 14px */
  --text-base: 1rem;      /* 16px */
  --text-lg:   1.125rem;  /* 18px */
  --text-xl:   1.25rem;   /* 20px */
  --text-2xl:  1.5rem;    /* 24px */
  --text-3xl:  1.875rem;  /* 30px */
  --text-4xl:  2.25rem;   /* 36px */

  --leading-tight:  1.25;
  --leading-normal: 1.5;
  --leading-relaxed:1.625;

  /* Spacing (8px base grid) */
  --space-1:  4px;
  --space-2:  8px;
  --space-3:  12px;
  --space-4:  16px;
  --space-5:  20px;
  --space-6:  24px;
  --space-8:  32px;
  --space-10: 40px;
  --space-12: 48px;
  --space-16: 64px;

  /* Radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 9999px;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.3);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.3), 0 1px 3px rgba(0,0,0,0.2);
  --shadow-lg: 0 10px 15px rgba(0,0,0,0.3), 0 4px 6px rgba(0,0,0,0.2);
}
```

# STEP 3 — MEASURE FROM FIGMA CORRECTLY
```
Reading Figma specs:
  • Click any element → right panel shows W, H, X, Y
  • Hover between two elements → shows spacing gap
  • Click text → shows font, size, weight, line height, letter spacing
  • Click component → shows which variant is applied

Spacing discipline:
  • All padding, margin, gap values should be multiples of your base unit (4 or 8)
  • If design shows 13px gap, assume 12px (3×4) or 16px (2×8) — snap to grid
  • Exception: if Figma has explicit spacing tokens named (e.g. "spacing/4"), use those exactly

Typography:
  • Line height in Figma is often absolute px — convert to unitless ratio
    → 24px line height on 16px text = 24/16 = 1.5 (use this as unitless)
  • Letter spacing in Figma is in "%" — convert: 2% on 16px = 16 × 0.02 = 0.32px
    → In CSS: letter-spacing: 0.02em
```

# STEP 4 — COMPONENT TRANSLATION

## Button Component (React)
```tsx
// Extract from Figma: sizes, colors, states
type ButtonProps = {
  children: React.ReactNode
  variant?: 'primary' | 'secondary' | 'ghost' | 'destructive'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  disabled?: boolean
  onClick?: () => void
}

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  loading,
  disabled,
  onClick
}: ButtonProps) {
  return (
    <button
      className={`btn btn--${variant} btn--${size}`}
      disabled={disabled || loading}
      onClick={onClick}
    >
      {loading && <Spinner className="btn__spinner" />}
      <span className={loading ? 'btn__text--loading' : ''}>{children}</span>
    </button>
  )
}
```
```css
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  border: none;
  cursor: pointer;
  font-family: var(--font-sans);
  font-weight: 500;
  transition: background 150ms, transform 100ms, box-shadow 150ms;
  border-radius: var(--radius-md);
}

/* Sizes — from Figma specs */
.btn--sm  { padding: 6px 12px; font-size: var(--text-sm); height: 32px; }
.btn--md  { padding: 10px 20px; font-size: var(--text-base); height: 40px; }
.btn--lg  { padding: 14px 28px; font-size: var(--text-lg); height: 48px; }

/* Variants */
.btn--primary {
  background: var(--color-primary);
  color: #fff;
}
.btn--primary:hover:not(:disabled) {
  background: var(--color-primary-hover);
}
.btn--primary:active:not(:disabled) {
  transform: scale(0.98);
}

.btn--secondary {
  background: var(--color-surface-2);
  color: var(--color-text);
  border: 1px solid var(--color-border);
}
.btn--secondary:hover:not(:disabled) {
  background: var(--color-surface);
  border-color: #444;
}

.btn--ghost {
  background: transparent;
  color: var(--color-text-muted);
}
.btn--ghost:hover:not(:disabled) {
  background: var(--color-surface-2);
  color: var(--color-text);
}

/* States */
.btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.btn:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
```

## Card Component
```css
/* Figma: surface background, 1px border, md radius, md shadow, 24px padding */
.card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  box-shadow: var(--shadow-sm);
}

.card--interactive {
  cursor: pointer;
  transition: border-color 150ms, box-shadow 150ms, transform 150ms;
}
.card--interactive:hover {
  border-color: #444;
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}
```

# RESPONSIVE IMPLEMENTATION
```css
/* Extract breakpoints from Figma frames */
:root {
  --bp-sm:  480px;
  --bp-md:  768px;
  --bp-lg:  1024px;
  --bp-xl:  1280px;
  --bp-2xl: 1536px;
}

/* Mobile-first */
.container {
  width: 100%;
  padding: 0 var(--space-4);
  margin: 0 auto;
}
@media (min-width: 768px) {
  .container { padding: 0 var(--space-8); }
}
@media (min-width: 1280px) {
  .container { max-width: 1280px; padding: 0 var(--space-12); }
}
```

# TYPOGRAPHY FROM FIGMA
```css
/* Map Figma text styles to CSS classes */
.heading-1 {
  font-family: var(--font-sans);
  font-size: var(--text-4xl);
  font-weight: 700;
  line-height: 1.15;
  letter-spacing: -0.02em;
  color: var(--color-text);
}

.heading-2 {
  font-size: var(--text-3xl);
  font-weight: 600;
  line-height: 1.25;
  letter-spacing: -0.01em;
}

.body-lg {
  font-size: var(--text-lg);
  line-height: var(--leading-relaxed);
  color: var(--color-text);
}

.body {
  font-size: var(--text-base);
  line-height: var(--leading-normal);
  color: var(--color-text-muted);
}

.caption {
  font-size: var(--text-sm);
  line-height: 1.4;
  color: var(--color-text-subtle);
}
```

# ACCESSIBILITY FROM DESIGN
```
For every interactive element from Figma, implement:

□ Keyboard navigation — :focus-visible outline (matches brand primary color)
□ ARIA labels — icon buttons need aria-label
□ Color contrast — WCAG AA requires 4.5:1 for normal text, 3:1 for large text
  → Test with: https://webaim.org/resources/contrastchecker/
□ Don't rely on color alone — add icon/text for error/success states
□ Touch targets — minimum 44×44px (even if visually smaller)
□ Disabled states — use disabled attribute, not just opacity
□ Loading states — add aria-busy="true" and aria-label update
```

# COMMON MISTAKES TO AVOID
```
✗ Magic numbers — no hardcoded 13px, 27px values. Snap to your spacing scale
✗ Skipping :focus-visible — keyboard users can't navigate
✗ Implementing hover without active state — feels unresponsive on click
✗ Hardcoding colors inline — always use CSS custom properties
✗ Missing transition on interactive states — snappy changes feel broken
✗ Building full page before components — build atoms (button, input, badge) first
✗ px for font sizes — use rem so users can scale text via browser settings
✗ Ignoring empty/loading/error states — designs usually only show happy path
✗ Not testing on actual device sizes — design looks different on real viewport
```
