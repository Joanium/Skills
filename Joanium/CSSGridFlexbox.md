---
name: CSS Grid and Flexbox Mastery
trigger: css grid, flexbox, css layout, grid template, flex container, align items, justify content, grid area, responsive layout, css columns, flex wrap, grid gap, auto-fill, auto-fit, subgrid, css layout patterns
description: Master CSS Grid and Flexbox — covering when to use each, all key properties, common layout patterns, responsive techniques, and real-world component layouts.
---

# ROLE
You are a senior front-end engineer who knows exactly when to reach for Grid vs Flexbox, writes clean CSS layouts without hacks, and builds responsive designs that degrade gracefully.

# WHEN TO USE WHICH

```
FLEXBOX — one-dimensional layout (a row OR a column)
  ✓ Navigation bars, toolbars
  ✓ Card rows, button groups
  ✓ Centering a single element
  ✓ Distributing space in a row/column
  ✓ Dynamic item sizes that should grow/shrink

GRID — two-dimensional layout (rows AND columns)
  ✓ Page layouts (header, sidebar, main, footer)
  ✓ Card grids where items must align across rows
  ✓ Dashboard widgets
  ✓ Complex form layouts
  ✓ Overlapping elements

RULE OF THUMB:
  Content drives layout → Flexbox
  Layout drives content → Grid
```

# FLEXBOX — COMPLETE REFERENCE

## Container Properties
```css
.flex-container {
  display: flex;              /* or inline-flex */

  /* Main axis direction */
  flex-direction: row;            /* → left to right (default) */
  flex-direction: row-reverse;    /* ← right to left */
  flex-direction: column;         /* ↓ top to bottom */
  flex-direction: column-reverse; /* ↑ bottom to top */

  /* Wrapping */
  flex-wrap: nowrap;    /* single line, items may overflow (default) */
  flex-wrap: wrap;      /* wraps to next line */
  flex-wrap: wrap-reverse;

  /* Shorthand: flex-flow: <direction> <wrap> */
  flex-flow: row wrap;

  /* Alignment on main axis */
  justify-content: flex-start;    /* pack to start */
  justify-content: flex-end;      /* pack to end */
  justify-content: center;        /* center */
  justify-content: space-between; /* equal gaps, no edge gaps */
  justify-content: space-around;  /* equal gaps, half gap at edges */
  justify-content: space-evenly;  /* equal gaps including edges */

  /* Alignment on cross axis (single line) */
  align-items: stretch;      /* fill cross-axis height (default) */
  align-items: flex-start;   /* align to start of cross axis */
  align-items: flex-end;     /* align to end */
  align-items: center;       /* center vertically */
  align-items: baseline;     /* align text baselines */

  /* Alignment on cross axis (multi-line — only with wrap) */
  align-content: flex-start;
  align-content: center;
  align-content: space-between;
  align-content: stretch;

  gap: 16px;             /* gap between items (row & column) */
  gap: 16px 24px;        /* row-gap column-gap */
}
```

## Item Properties
```css
.flex-item {
  /* How item grows to fill extra space */
  flex-grow: 0;     /* don't grow (default) */
  flex-grow: 1;     /* grow proportionally */

  /* How item shrinks when space is tight */
  flex-shrink: 1;   /* can shrink (default) */
  flex-shrink: 0;   /* never shrink */

  /* Base size before grow/shrink */
  flex-basis: auto;   /* use item's content size (default) */
  flex-basis: 200px;  /* start at 200px */
  flex-basis: 0;      /* ignore content size, distribute purely by ratio */

  /* Shorthand: flex: <grow> <shrink> <basis> */
  flex: 1;          /* flex: 1 1 0 — grow + shrink + zero basis (equal distribution) */
  flex: 1 0 auto;   /* grow but never shrink */
  flex: 0 0 200px;  /* fixed 200px — don't grow or shrink */
  flex: none;       /* flex: 0 0 auto — rigid, use content size */

  /* Self-alignment (overrides align-items) */
  align-self: center;
  align-self: flex-end;

  /* Order (default 0, lower = earlier) */
  order: -1;   /* move before others */
  order: 1;    /* move after others */
}
```

# CSS GRID — COMPLETE REFERENCE

## Container Properties
```css
.grid-container {
  display: grid;    /* or inline-grid */

  /* Define columns */
  grid-template-columns: 200px 1fr 1fr;      /* fixed + 2 equal */
  grid-template-columns: repeat(3, 1fr);     /* 3 equal columns */
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));  /* responsive */
  grid-template-columns: [sidebar] 250px [main] 1fr [end];       /* named lines */

  /* Define rows */
  grid-template-rows: auto 1fr auto;     /* header, content, footer */
  grid-template-rows: repeat(3, 100px);

  /* Named areas */
  grid-template-areas:
    "header  header"
    "sidebar main"
    "footer  footer";

  /* Shorthand — areas + rows / columns */
  grid-template:
    "header  header"  60px
    "sidebar main"    1fr
    "footer  footer"  40px
    / 200px 1fr;

  /* Auto-created row height */
  grid-auto-rows: 200px;           /* implicit rows = 200px */
  grid-auto-rows: minmax(100px, auto);

  /* Auto-created column width */
  grid-auto-columns: 1fr;

  /* Flow direction for auto-placed items */
  grid-auto-flow: row;     /* fill rows first (default) */
  grid-auto-flow: column;
  grid-auto-flow: row dense;  /* fill holes in grid */

  gap: 16px;
  gap: 16px 24px;  /* row-gap column-gap */

  /* Alignment of entire grid within container */
  justify-content: center;   /* horizontal */
  align-content: center;     /* vertical */

  /* Alignment of items within their cells */
  justify-items: stretch;    /* default */
  align-items: stretch;      /* default */
}
```

## Item Properties
```css
.grid-item {
  /* Placement by line number */
  grid-column: 1 / 3;        /* span columns 1 to 3 */
  grid-column: 1 / -1;       /* from column 1 to last (-1) */
  grid-column: span 2;       /* span 2 columns from auto position */

  grid-row: 1 / 3;
  grid-row: span 2;

  /* Placement by area name */
  grid-area: header;          /* place in named area */
  grid-area: 1 / 1 / 3 / 3;  /* row-start / col-start / row-end / col-end */

  /* Self-alignment */
  justify-self: center;   /* horizontal in cell */
  align-self: center;     /* vertical in cell */
  place-self: center;     /* both */
}
```

# COMMON LAYOUT PATTERNS

## Perfect Center
```css
/* Flexbox */
.center {
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Grid (shortest) */
.center {
  display: grid;
  place-items: center;
}
```

## Holy Grail Layout
```css
.page {
  display: grid;
  grid-template:
    "header  header"  60px
    "sidebar main"    1fr
    "footer  footer"  40px
    / 240px  1fr;
  min-height: 100vh;
}

.header  { grid-area: header; }
.sidebar { grid-area: sidebar; }
.main    { grid-area: main; }
.footer  { grid-area: footer; }
```

## Responsive Card Grid
```css
/* Auto-fill: creates as many columns as fit */
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
}
/* No media queries needed — wraps automatically */

/* auto-fill vs auto-fit:
   auto-fill: keeps empty columns (grid stays wide)
   auto-fit:  collapses empty columns (last row stretches) */
```

## Sidebar Layout
```css
.layout {
  display: grid;
  grid-template-columns: min(280px, 30%) 1fr;
  gap: 32px;
}

/* Responsive: stack on small screens */
@media (max-width: 768px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
```

## Masonry-ish: Multi-Column
```css
.masonry {
  columns: 3 280px;  /* 3 columns, each min 280px */
  column-gap: 20px;
}
.masonry > * {
  break-inside: avoid;  /* don't split items across columns */
  margin-bottom: 20px;
}
```

## Sticky Sidebar
```css
.layout {
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 32px;
  align-items: start;   /* CRITICAL — without this sidebar stretches full height */
}

.sidebar {
  position: sticky;
  top: 24px;
}
```

## Full-Bleed Section in Constrained Layout
```css
/* Content constrained to max-width, but some elements span full width */
.content {
  display: grid;
  grid-template-columns:
    [full-start] minmax(16px, 1fr)
    [content-start] min(100% - 32px, 72ch) [content-end]
    minmax(16px, 1fr) [full-end];
}
.content > * {
  grid-column: content;
}
.content > .full-bleed {
  grid-column: full;
}
```

# RESPONSIVE WITHOUT MEDIA QUERIES
```css
/* Clamp: min, preferred, max */
font-size: clamp(1rem, 2.5vw, 1.5rem);
padding: clamp(16px, 4vw, 48px);
width: clamp(200px, 50%, 600px);

/* Fluid columns */
grid-template-columns: repeat(auto-fit, minmax(min(100%, 300px), 1fr));

/* Stack or row based on container width */
.card {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}
.card > * {
  flex: 1 1 200px;  /* grow, shrink, base 200px — wraps when needed */
}
```

# COMMON MISTAKES TO AVOID
```
✗ Using Flexbox for 2D layouts — use Grid
✗ Using negative margins for gaps — use gap
✗ align-content on single-line flex container — has no effect (need flex-wrap: wrap)
✗ Forgetting align-items: start on grid with sticky sidebar — sidebar grows full height
✗ Using px for flex-basis in flex: 1 0 200px — can't go below 200px even when space is tight
✗ Not using minmax(0, 1fr) — 1fr can't shrink below its content size without minmax(0, 1fr)
✗ Overcomplicating — most layouts need < 10 lines of CSS if you choose the right tool
✗ Using order to reorder — breaks keyboard navigation and screen readers
```
