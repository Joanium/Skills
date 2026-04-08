---
name: Color System Design
trigger: color system, design tokens color, color palette, dark mode colors, color tokens, CSS variables colors, accessible colors, color contrast, WCAG contrast, color scheme, color theme, semantic color tokens, color design system, brand colors tokens, light dark theme
description: Build a scalable, accessible color system using semantic tokens, CSS variables, and dark mode support. Covers palette design, semantic token layers, WCAG contrast compliance, and implementation patterns.
---

# ROLE
You are a design systems engineer who has seen what happens when a codebase uses 47 different blues because developers picked colors inline. You build color systems with semantic tokens that designers and developers share the same language for, that are accessible by default, and that dark mode is built into from day one — not bolted on.

# THE TWO-LAYER MODEL

## Layer 1: Raw Palette (Scale)
```css
/*
  Raw colors — not used directly in UI components.
  These are the "paint swatches" — a complete scale for each hue.
  Naming: --color-{hue}-{shade} where shade = 50 (lightest) to 950 (darkest)
*/
:root {
  /* Brand blue scale */
  --color-blue-50:  #eff6ff;
  --color-blue-100: #dbeafe;
  --color-blue-200: #bfdbfe;
  --color-blue-300: #93c5fd;
  --color-blue-400: #60a5fa;
  --color-blue-500: #3b82f6;
  --color-blue-600: #2563eb;
  --color-blue-700: #1d4ed8;
  --color-blue-800: #1e40af;
  --color-blue-900: #1e3a8a;
  --color-blue-950: #172554;

  /* Neutral scale */
  --color-neutral-0:   #ffffff;
  --color-neutral-50:  #f8fafc;
  --color-neutral-100: #f1f5f9;
  --color-neutral-200: #e2e8f0;
  --color-neutral-300: #cbd5e1;
  --color-neutral-400: #94a3b8;
  --color-neutral-500: #64748b;
  --color-neutral-600: #475569;
  --color-neutral-700: #334155;
  --color-neutral-800: #1e293b;
  --color-neutral-900: #0f172a;
  --color-neutral-950: #020617;
  --color-neutral-1000: #000000;

  /* Semantic scales */
  --color-green-50:  #f0fdf4;
  --color-green-500: #22c55e;
  --color-green-700: #15803d;

  --color-red-50:  #fef2f2;
  --color-red-500: #ef4444;
  --color-red-700: #b91c1c;

  --color-yellow-50:  #fefce8;
  --color-yellow-500: #eab308;
  --color-yellow-700: #a16207;
}
```

## Layer 2: Semantic Tokens (What Components Use)
```css
/*
  Semantic tokens — the "design vocabulary".
  Components use ONLY these — never raw palette values directly.
  This layer is what changes between light mode and dark mode.
*/

/* Light mode (default) */
:root {
  /* Surfaces */
  --color-bg-base:        var(--color-neutral-0);      /* main page background */
  --color-bg-subtle:      var(--color-neutral-50);     /* slightly off-white panels */
  --color-bg-muted:       var(--color-neutral-100);    /* disabled, placeholder areas */
  --color-bg-elevated:    var(--color-neutral-0);      /* cards, modals above base */

  /* Borders */
  --color-border-default: var(--color-neutral-200);
  --color-border-strong:  var(--color-neutral-300);
  --color-border-subtle:  var(--color-neutral-100);

  /* Text */
  --color-text-primary:   var(--color-neutral-900);    /* main readable text */
  --color-text-secondary: var(--color-neutral-600);    /* labels, captions */
  --color-text-muted:     var(--color-neutral-400);    /* placeholders, disabled */
  --color-text-inverse:   var(--color-neutral-0);      /* text on dark backgrounds */
  --color-text-link:      var(--color-blue-600);
  --color-text-link-hover:var(--color-blue-700);

  /* Brand / Interactive */
  --color-primary:        var(--color-blue-600);
  --color-primary-hover:  var(--color-blue-700);
  --color-primary-active: var(--color-blue-800);
  --color-primary-subtle: var(--color-blue-50);
  --color-primary-text:   var(--color-neutral-0);      /* text ON primary button */

  /* Status */
  --color-success:        var(--color-green-700);
  --color-success-bg:     var(--color-green-50);
  --color-error:          var(--color-red-700);
  --color-error-bg:       var(--color-red-50);
  --color-warning:        var(--color-yellow-700);
  --color-warning-bg:     var(--color-yellow-50);
  --color-info:           var(--color-blue-700);
  --color-info-bg:        var(--color-blue-50);

  /* Interactive states */
  --color-focus-ring:     var(--color-blue-500);
  --color-overlay:        rgba(0, 0, 0, 0.5);          /* modal backdrop */
}

/* Dark mode — override semantic tokens only */
@media (prefers-color-scheme: dark) {
  :root {
    --color-bg-base:        var(--color-neutral-950);
    --color-bg-subtle:      var(--color-neutral-900);
    --color-bg-muted:       var(--color-neutral-800);
    --color-bg-elevated:    var(--color-neutral-900);

    --color-border-default: var(--color-neutral-800);
    --color-border-strong:  var(--color-neutral-700);
    --color-border-subtle:  var(--color-neutral-900);

    --color-text-primary:   var(--color-neutral-50);
    --color-text-secondary: var(--color-neutral-400);
    --color-text-muted:     var(--color-neutral-600);
    --color-text-inverse:   var(--color-neutral-900);
    --color-text-link:      var(--color-blue-400);
    --color-text-link-hover:var(--color-blue-300);

    --color-primary:        var(--color-blue-500);
    --color-primary-hover:  var(--color-blue-400);
    --color-primary-active: var(--color-blue-300);
    --color-primary-subtle: rgba(59, 130, 246, 0.15);

    --color-success:        var(--color-green-500);
    --color-success-bg:     rgba(34, 197, 94, 0.15);
    --color-error:          var(--color-red-500);
    --color-error-bg:       rgba(239, 68, 68, 0.15);
    --color-warning:        var(--color-yellow-500);
    --color-warning-bg:     rgba(234, 179, 8, 0.15);
    --color-info:           var(--color-blue-400);
    --color-info-bg:        rgba(59, 130, 246, 0.15);
  }
}

/* Class-based dark mode (for user toggle) */
[data-theme="dark"] {
  /* same overrides as above */
}
```

# COMPONENT USAGE (Use Semantic Tokens Only)
```css
/* Button — uses semantic tokens, works in both modes automatically */
.btn-primary {
  background-color: var(--color-primary);
  color: var(--color-primary-text);
  border: 1px solid var(--color-primary);
}
.btn-primary:hover {
  background-color: var(--color-primary-hover);
  border-color: var(--color-primary-hover);
}

/* Card */
.card {
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border-default);
  color: var(--color-text-primary);
}

/* Input */
.input {
  background: var(--color-bg-base);
  border: 1px solid var(--color-border-default);
  color: var(--color-text-primary);
}
.input::placeholder { color: var(--color-text-muted); }
.input:focus {
  border-color: var(--color-primary);
  outline: 2px solid var(--color-focus-ring);
  outline-offset: 1px;
}

/* Status badges */
.badge-success {
  background: var(--color-success-bg);
  color: var(--color-success);
}
.badge-error {
  background: var(--color-error-bg);
  color: var(--color-error);
}
```

# WCAG CONTRAST REQUIREMENTS

## Contrast Ratios
```
WCAG AA (minimum):
  Normal text (< 18px regular, < 14px bold):  4.5:1 contrast ratio
  Large text (≥ 18px regular, ≥ 14px bold):  3:1 contrast ratio
  UI components (buttons, inputs, icons):      3:1

WCAG AAA (enhanced):
  Normal text:  7:1
  Large text:   4.5:1

Test your colors:
  https://webaim.org/resources/contrastchecker/
  npx contrast-ratio "#1e293b" "#ffffff"

Common light mode combos:
  neutral-900 on neutral-0:    21:1  ✓ AAA
  neutral-600 on neutral-0:    5.9:1 ✓ AA
  blue-600 on neutral-0:       4.6:1 ✓ AA (barely — prefer blue-700 for safety)
  neutral-400 on neutral-0:    2.9:1 ✗ FAIL — do not use for body text

Common dark mode combos:
  neutral-50 on neutral-950:   19:1  ✓ AAA
  neutral-400 on neutral-950:  5.1:1 ✓ AA
  blue-400 on neutral-950:     5.9:1 ✓ AA
  neutral-600 on neutral-950:  2.4:1 ✗ FAIL — do not use
```

## JavaScript: Check Contrast at Runtime
```javascript
function relativeLuminance(hex) {
  const rgb = parseInt(hex.replace('#', ''), 16);
  const r = (rgb >> 16) & 0xff;
  const g = (rgb >>  8) & 0xff;
  const b = (rgb >>  0) & 0xff;

  const srgb = [r, g, b].map(v => {
    v /= 255;
    return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
  });

  return 0.2126 * srgb[0] + 0.7152 * srgb[1] + 0.0722 * srgb[2];
}

function contrastRatio(hex1, hex2) {
  const l1 = relativeLuminance(hex1);
  const l2 = relativeLuminance(hex2);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

const ratio = contrastRatio('#2563eb', '#ffffff');
console.log(`Contrast: ${ratio.toFixed(2)}:1`);
console.log(`AA pass: ${ratio >= 4.5}`);
```

# DARK MODE TOGGLE (JavaScript)
```typescript
type Theme = 'light' | 'dark' | 'system';

class ThemeManager {
  private current: Theme;

  constructor() {
    this.current = (localStorage.getItem('theme') as Theme) ?? 'system';
    this.apply();

    // Listen for OS theme changes
    window.matchMedia('(prefers-color-scheme: dark)')
      .addEventListener('change', () => {
        if (this.current === 'system') this.apply();
      });
  }

  set(theme: Theme) {
    this.current = theme;
    localStorage.setItem('theme', theme);
    this.apply();
  }

  private apply() {
    const isDark = this.current === 'dark' ||
      (this.current === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);

    document.documentElement.dataset.theme = isDark ? 'dark' : 'light';
    document.documentElement.style.colorScheme = isDark ? 'dark' : 'light';
  }

  get(): Theme { return this.current; }
  isDark(): boolean { return document.documentElement.dataset.theme === 'dark'; }
}

export const theme = new ThemeManager();
```

# COLOR SYSTEM ANTI-PATTERNS
```
X  Using raw palette values in components:
   color: var(--color-blue-600)  ← will not adapt in dark mode
   color: var(--color-text-link) ← correct — semantic token

X  Hardcoding hex in components:
   background: #1e293b  ← use a variable

X  Using opacity to create variants:
   color: rgba(0, 0, 0, 0.5)  ← unpredictable on colored backgrounds
   color: var(--color-text-secondary)  ← correct

X  Too many semantic tokens — you do not need --color-sidebar-nav-item-active-hover
   Start with ~20 semantic tokens, add only when you genuinely need it

X  No focus ring — keyboard users are blind without it
   Always define --color-focus-ring and use it on :focus-visible

X  Skipping dark mode contrast checks — light mode passing does not mean dark mode passes
   Test BOTH modes against WCAG before shipping
```

# CHECKLIST
```
[ ] Two-layer model: raw palette + semantic tokens (components use semantic only)
[ ] Dark mode defined as overrides on semantic layer — not a separate component
[ ] System preference respected (prefers-color-scheme) and user override supported
[ ] All text/background combos checked against WCAG AA (4.5:1 for body text)
[ ] Focus ring color defined and visible against all backgrounds
[ ] Status colors (success/error/warning/info) defined for both modes
[ ] Color naming semantic: --color-text-primary not --color-dark-gray
[ ] No hex values in component CSS — only CSS variables
[ ] colorScheme property set (tells browser to style scrollbars, inputs correctly)
[ ] Color palette documented with usage guidance for new team members