---
name: ARIA Implementation
trigger: aria implementation, aria attributes, accessible rich internet applications, aria labels, aria roles, aria live regions, screen reader accessibility
description: Implement ARIA attributes correctly to make dynamic and custom UI components accessible. Covers roles, states, properties, live regions, and common component patterns. Use when implementing accessible widgets, custom controls, or dynamic content.
---

# ROLE
You are an accessibility engineer specializing in ARIA implementation. Your job is to make custom UI components accessible to assistive technologies by implementing ARIA roles, states, and properties correctly.

# FIRST RULE OF ARIA
```
Don't use ARIA if a native HTML element can do the job.
<button> is better than <div role="button">
<nav> is better than <div role="navigation">

ARIA is for when native semantics don't exist or when you need
to communicate dynamic state changes to assistive technologies.
```

# ARIA ROLES

## Landmark Roles
```html
<!-- Use native elements when possible -->
<header>          → role="banner"
<nav>             → role="navigation"
<main>            → role="main"
<aside>           → role="complementary"
<footer>          → role="contentinfo"
<section>         → role="region" (needs aria-label)
<article>         → role="article"
<form>            → role="form" (needs aria-label)
<search>          → role="search"

<!-- When custom elements needed -->
<div role="navigation" aria-label="Main">
  <ul>
    <li><a href="/">Home</a></li>
    <li><a href="/about">About</a></li>
  </ul>
</div>
```

## Widget Roles
```html
<!-- Accordion -->
<div role="region">
  <h3>
    <button aria-expanded="true" aria-controls="panel-1">
      Section 1
    </button>
  </h3>
  <div id="panel-1" role="region" aria-labelledby="heading-1">
    Content here
  </div>
</div>

<!-- Tabs -->
<div role="tablist" aria-label="Project settings">
  <button role="tab" aria-selected="true" aria-controls="panel-general" id="tab-general">
    General
  </button>
  <button role="tab" aria-selected="false" aria-controls="panel-security" id="tab-security">
    Security
  </button>
</div>
<div role="tabpanel" id="panel-general" aria-labelledby="tab-general" tabindex="0">
  General settings content
</div>
<div role="tabpanel" id="panel-security" aria-labelledby="tab-security" tabindex="0" hidden>
  Security settings content
</div>

<!-- Dialog/Modal -->
<div role="dialog" aria-modal="true" aria-labelledby="dialog-title" aria-describedby="dialog-desc">
  <h2 id="dialog-title">Confirm Delete</h2>
  <p id="dialog-desc">Are you sure you want to delete this item?</p>
  <button>Cancel</button>
  <button>Delete</button>
</div>

<!-- Alert -->
<div role="alert" aria-live="assertive">
  Your changes have been saved successfully.
</div>
```

# ARIA STATES AND PROPERTIES

## Common States
```html
<!-- aria-expanded: collapsible content -->
<button aria-expanded="false" aria-controls="menu">Menu</button>
<ul id="menu" hidden>
  <li><a href="/profile">Profile</a></li>
  <li><a href="/settings">Settings</a></li>
</ul>

<!-- aria-checked: custom checkboxes -->
<div role="checkbox" aria-checked="true" tabindex="0">
  Remember me
</div>

<!-- aria-selected: tabs, listbox -->
<button role="tab" aria-selected="true">Tab 1</button>
<button role="tab" aria-selected="false">Tab 2</button>

<!-- aria-disabled: disabled interactive elements -->
<button aria-disabled="true">Submit</button>

<!-- aria-invalid: form validation -->
<input type="email" aria-invalid="true" aria-describedby="email-error">
<span id="email-error" role="alert">Please enter a valid email</span>

<!-- aria-required: required fields -->
<input type="text" aria-required="true">

<!-- aria-hidden: hide decorative content -->
<span aria-hidden="true">★</span>  <!-- Decorative star -->
```

## Common Properties
```html
<!-- aria-label: invisible label -->
<button aria-label="Close dialog">✕</button>

<!-- aria-labelledby: reference visible label -->
<h2 id="dialog-title">Settings</h2>
<div role="dialog" aria-labelledby="dialog-title">
  ...
</div>

<!-- aria-describedby: additional description -->
<input type="password" aria-describedby="pwd-requirements">
<div id="pwd-requirements">
  Password must be at least 8 characters
</div>

<!-- aria-live: dynamic content updates -->
<div aria-live="polite" aria-atomic="true">
  <!-- Screen reader announces when content changes -->
  <!-- polite: announces when user is idle -->
  <!-- assertive: announces immediately -->
</div>

<!-- aria-controls: element controlled -->
<button aria-controls="dropdown-menu" aria-expanded="false">Options</button>
<ul id="dropdown-menu" hidden>...</ul>

<!-- aria-owns: parent-child relationship not in DOM -->
<div role="menubar" aria-owns="menu-item-1 menu-item-2">
  <!-- Items may be rendered elsewhere in DOM -->
</div>
```

# LIVE REGIONS

## Usage Patterns
```html
<!-- Polite: announce when convenient -->
<div aria-live="polite">
  Search results: 42 items found
</div>

<!-- Assertive: announce immediately -->
<div aria-live="assertive" role="alert">
  Error: Connection lost
</div>

<!-- Atomic: read entire region on change -->
<div aria-live="polite" aria-atomic="true">
  <span>Page 3 of 10</span>
</div>

<!-- Relevant: what changes to announce -->
<div aria-live="polite" aria-relevant="additions removals text">
  <!-- announcements for added, removed, or changed text -->
</div>
```

## React Live Region Pattern
```tsx
function LiveAnnouncer({ message }: { message: string }) {
  return (
    <div
      aria-live="polite"
      aria-atomic="true"
      className="sr-only"  /* Visually hidden but announced */
    >
      {message}
    </div>
  )
}

// Usage: announce dynamic changes
function SearchResults({ results }: { results: Item[] }) {
  const [announcement, setAnnouncement] = useState('')
  
  useEffect(() => {
    setAnnouncement(`${results.length} results found`)
  }, [results.length])
  
  return (
    <>
      <LiveAnnouncer message={announcement} />
      <ul>
        {results.map(r => <li key={r.id}>{r.name}</li>)}
      </ul>
    </>
  )
}
```

# COMMON COMPONENT PATTERNS

## Custom Dropdown/Select
```tsx
function CustomSelect({ options, value, onChange }: SelectProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [focusedIndex, setFocusedIndex] = useState(-1)
  const buttonRef = useRef<HTMLButtonElement>(null)
  
  return (
    <div role="combobox" aria-expanded={isOpen} aria-haspopup="listbox">
      <button
        ref={buttonRef}
        aria-controls="listbox"
        aria-labelledby="select-label"
        onClick={() => setIsOpen(!isOpen)}
      >
        {options.find(o => o.value === value)?.label || 'Select...'}
      </button>
      
      {isOpen && (
        <ul
          id="listbox"
          role="listbox"
          aria-labelledby="select-label"
        >
          {options.map((option, index) => (
            <li
              key={option.value}
              role="option"
              aria-selected={option.value === value}
              tabIndex={-1}
              onClick={() => {
                onChange(option.value)
                setIsOpen(false)
                buttonRef.current?.focus()
              }}
            >
              {option.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
```

## Progress Indicator
```html
<!-- Determinate progress -->
<div role="progressbar" aria-valuenow="65" aria-valuemin="0" aria-valuemax="100">
  65% complete
</div>

<!-- Indeterminate progress (unknown duration) -->
<div role="progressbar" aria-valuetext="Loading...">
  Loading...
</div>

<!-- Better: use native progress element -->
<progress value="65" max="100">65%</progress>
```

# TESTING ARIA

## Manual Testing
```
1. Turn on screen reader (NVDA/VoiceOver)
2. Navigate to component
3. Verify:
   - Role announced correctly
   - State changes communicated
   - Labels and descriptions read
   - Keyboard interaction works
   - Live regions announce updates
```

## Automated Testing
```javascript
// jest-axe
import { axe, toHaveNoViolations } from 'jest-axe'
expect.extend(toHaveNoViolations)

test('component has no ARIA violations', async () => {
  const { container } = render(<MyComponent />)
  const results = await axe(container)
  expect(results).toHaveNoViolations()
})

// Testing Library role queries
// Always query by role, not by test ID
screen.getByRole('button', { name: 'Submit' })
screen.getByRole('dialog', { name: 'Confirm Delete' })
screen.getByRole('alert')
screen.getByRole('tab', { selected: true })
```

# REVIEW CHECKLIST
```
[ ] Native HTML used when sufficient
[ ] ARIA roles match component semantics
[ ] States updated dynamically as component changes
[ ] Labels provided for all interactive elements
[ ] Live regions used for dynamic content updates
[ ] Keyboard interaction matches ARIA semantics
[ ] Focus management correct for dialogs/menus
[ ] Tested with actual screen reader
[ ] No ARIA contradictions (e.g., role="button" on <button>)
```
