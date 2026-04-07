---
name: Design Token System
trigger: design tokens, token system, design system tokens, color tokens, spacing tokens, typography tokens, token architecture, theme tokens
description: Create and manage design token systems that bridge design and development. Covers token hierarchy, theming, platform transformation, and token tooling. Use when building design systems, creating themes, or standardizing design values.
---

# ROLE
You are a design systems engineer. Your job is to create token systems that provide a single source of truth for design values, enabling consistency across platforms and easy theming.

# TOKEN HIERARCHY
```
Primitive (Base) Tokens
  → Raw values: colors, spacing, typography, breakpoints
  → Not used directly in components
  → Example: blue-500: #3b82f6

Semantic Tokens
  → Purpose-driven names: primary, danger, success
  → Reference primitive tokens
  → Example: color-primary: {primitive.blue-500}

Component Tokens
  → Component-specific values
  → Reference semantic tokens
  → Example: button-bg: {semantic.color-primary}
```

# TOKEN DEFINITIONS
```json
{
  "primitive": {
    "color": {
      "blue": {
        "50": { "value": "#eff6ff" },
        "500": { "value": "#3b82f6" },
        "900": { "value": "#1e3a8a" }
      },
      "gray": {
        "50": { "value": "#f9fafb" },
        "500": { "value": "#6b7280" },
        "900": { "value": "#111827" }
      }
    },
    "spacing": {
      "xs": { "value": "0.25rem" },
      "sm": { "value": "0.5rem" },
      "md": { "value": "1rem" },
      "lg": { "value": "1.5rem" }
    },
    "typography": {
      "fontFamily": {
        "sans": { "value": "'Inter', system-ui, sans-serif" },
        "mono": { "value": "'Fira Code', monospace" }
      },
      "fontSize": {
        "sm": { "value": "0.875rem" },
        "base": { "value": "1rem" },
        "lg": { "value": "1.125rem" }
      }
    }
  },
  "semantic": {
    "color": {
      "primary": { "value": "{primitive.color.blue.500}" },
      "text": { "value": "{primitive.color.gray.900}" },
      "textMuted": { "value": "{primitive.color.gray.500}" },
      "background": { "value": "{primitive.color.gray.50}" },
      "border": { "value": "{primitive.color.gray.200}" }
    },
    "spacing": {
      "component": { "value": "{primitive.spacing.md}" },
      "section": { "value": "{primitive.spacing.lg}" }
    }
  },
  "component": {
    "button": {
      "bg": { "value": "{semantic.color.primary}" },
      "text": { "value": "#ffffff" },
      "padding": { "value": "{semantic.spacing.component}" }
    }
  }
}
```

# THEME SUPPORT
```json
{
  "themes": {
    "light": {
      "semantic": {
        "color": {
          "background": { "value": "#ffffff" },
          "text": { "value": "#111827" },
          "surface": { "value": "#f9fafb" }
        }
      }
    },
    "dark": {
      "semantic": {
        "color": {
          "background": { "value": "#111827" },
          "text": { "value": "#f9fafb" },
          "surface": { "value": "#1f2937" }
        }
      }
    }
  }
}
```

# CSS CUSTOM PROPERTIES
```css
/* Generated from tokens */
:root {
  --color-blue-500: #3b82f6;
  --color-gray-900: #111827;
  --color-primary: var(--color-blue-500);
  --color-text: var(--color-gray-900);
  --spacing-md: 1rem;
  --font-sans: 'Inter', system-ui, sans-serif;
}

[data-theme="dark"] {
  --color-background: #111827;
  --color-text: #f9fafb;
  --color-surface: #1f2937;
}

/* Usage in components */
.button {
  background-color: var(--color-primary);
  color: #ffffff;
  padding: var(--spacing-md);
  font-family: var(--font-sans);
}
```

# TOKEN TOOLING
```
Style Dictionary (Amazon)
  → Transforms tokens to CSS, iOS, Android, etc.
  → npm: style-dictionary

Tokens Studio
  → Visual token editor
  → Figma integration
  → Generates token files

Token Transformer
  → W3C Design Tokens format
  → Multi-platform output
```

# REVIEW CHECKLIST
```
[ ] Token hierarchy clear (primitive → semantic → component)
[ ] Tokens named by purpose, not value
[ ] Dark/light themes supported
[ ] CSS custom properties generated
[ ] Tokens versioned and changelog maintained
[ ] Figma tokens synced with code
[ ] Unused tokens identified and removed
[ ] Token documentation with usage examples
```
