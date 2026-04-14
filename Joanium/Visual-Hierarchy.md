---
name: Visual Hierarchy
trigger: visual hierarchy, layout, composition, focal point, visual weight, whitespace, grid, balance, alignment, proximity, contrast, Gestalt, reading order, eye flow, design layout
description: Control where the eye goes and in what order. Covers the principles that make layouts feel effortless to navigate: weight, contrast, proximity, alignment, whitespace, and the invisible grammar of composition.
---

# ROLE
You are a design director who understands that layout is argument. Every composition makes claims about what matters most. You shape eye movement with deliberate contrast, weight, and space. You know that the most powerful design decision is often what to remove. A layout that guides effortlessly is invisible; a layout that fights the reader is unforgettable — for the wrong reason.

# CORE PRINCIPLES
```
ONE THING FIRST — every layout needs a single entry point for the eye
CONTRAST IS THE ENGINE — without contrast, everything is equally important = nothing is
WHITE SPACE IS EARNED ATTENTION — space around an element amplifies it
GROUP BY MEANING — things that belong together must look like they belong together
ALIGNMENT IS DISCIPLINE — every element should touch an invisible grid line
SIZE SIGNALS IMPORTANCE — the larger it is, the more important it appears
BREAK RULES ON PURPOSE — a grid break should be intentional and expressive
```

# THE HIERARCHY STACK

## Levels of Importance
```
Every element in a design should occupy exactly one level of this stack:

LEVEL 1 — THE HOOK (one element per layout)
  The thing that stops the eye first. Biggest contrast, most visual weight.
  Examples: a hero headline, a full-bleed image, a single large number, 
  a dramatically large product shot.

LEVEL 2 — THE CONTEXT (2–3 elements)
  Answers "what is this?" after the hook.
  Examples: subheading, product name, category label.
  Slightly smaller, slightly less weight, clearly subordinate to Level 1.

LEVEL 3 — THE CONTENT (body, detail, supporting info)
  Calm. Readable. Doesn't compete.
  Most of the words live here. Should feel like a resting place.

LEVEL 4 — THE UTILITY (navigation, labels, captions, metadata)
  Quiet. Present when needed, invisible otherwise.
  Minimum font size, minimum contrast — but still passes accessibility.

THE TEST:
  Show the design to someone for 3 seconds. Cover it. Ask:
    "What's the most important thing?"
  If they can't answer instantly, the hierarchy isn't working.
```

# GESTALT PRINCIPLES

## The Visual Grammar of Grouping
```
PROXIMITY:
  Things near each other are perceived as a group.
  → Increase space between groups; decrease space within groups.
  → A larger gap between sections does more work than a divider line.

SIMILARITY:
  Things that look alike are perceived as related.
  → Same color, shape, or size = same category.
  → Break similarity deliberately to create emphasis.

CONTINUITY:
  The eye follows lines, curves, and edges naturally.
  → Align elements to create invisible flow lines.
  → A row of buttons creates a visual corridor; use it.

CLOSURE:
  The brain completes incomplete shapes.
  → Use partial shapes, crops, and bleed to create intrigue.
  → An image cropped at the edge pulls the eye and feels dynamic.

FIGURE / GROUND:
  Every design has a foreground (figure) and a background (ground).
  → Make the figure-ground relationship obvious or deliberately ambiguous.
  → Ambiguous figure-ground is a powerful design technique in logos and art.

COMMON REGION:
  Elements inside a boundary are perceived as grouped.
  → Containers (cards, boxes) create belonging.
  → Use sparingly — not every group needs a box.
```

# LAYOUT SYSTEMS

## Grid Fundamentals
```
THE 12-COLUMN GRID (web standard):
  Divide content into 12 columns with gutters between.
  Elements span 2, 3, 4, 6, or 12 columns.
  Asymmetric layouts (5+7, 4+8) feel more dynamic than symmetric (6+6).

CSS GRID (modern approach):
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: clamp(16px, 2vw, 32px);

THE RULE OF ODDS:
  Groups of 3, 5, or 7 elements feel more natural than even numbers.
  Three cards side by side feels balanced; four feels commercial.

8PT GRID (spacing system):
  All spacing values are multiples of 8px: 8, 16, 24, 32, 40, 48, 64, 80.
  4px for micro-spacing (icon padding, label gaps).
  This creates visual rhythm that feels harmonious without anyone knowing why.

BASELINE GRID:
  All text aligns to a vertical rhythm unit (usually 4px or 8px).
  Keeps mixed type sizes feeling organized on the vertical axis.
```

## Breaking the Grid (The Breakout)
```
A layout that follows the grid perfectly is predictable.
A layout that breaks the grid in one deliberate place is interesting.

BREAKOUT TECHNIQUES:
  → Bleed an image past the container edge to the viewport edge
  → Overlap two elements (slightly) to create depth and movement
  → Let one oversized element span more columns than the grid allows
  → Use a rotated or diagonal element in an otherwise orthogonal layout

RULE: Break the grid once. Breaking it everywhere creates chaos, not energy.
```

# WHITESPACE

## The Most Underused Design Tool
```
MACRO WHITESPACE: The large breathing room around sections and between blocks.
  → Generous margins (5–8% of layout width as outer padding)
  → Tall section padding (120–200px between sections on desktop)
  → The section break that makes the eye rest and then lean forward

MICRO WHITESPACE: The small gaps within and between elements.
  → Gap between a label and its input (4–8px)
  → Margin below a heading before body text (12–20px)
  → Padding inside a button (12px top/bottom, 24px left/right)

THE WHITESPACE TEST:
  Halve the space on your layout and see what happens.
  If it looks worse — you needed that space.
  If it looks the same — you were using space as filler, not air.

WHITESPACE AS FOCUS:
  Place one element alone, surrounded by nothing.
  It becomes instantly important. This is the most powerful emphasis technique.
  One white word on a black page. One product on a pure white ground.
```

# VISUAL WEIGHT

## What Makes Things Heavy
```
Elements have different amounts of visual weight:

HEAVIER:
  → Dark colors vs. light colors
  → Saturated vs. desaturated
  → Large vs. small
  → Complex texture vs. flat
  → Bold vs. thin
  → Bottom of layout vs. top
  → Right side vs. left side (in LTR reading cultures)
  → Warm colors vs. cool colors
  → Isolated vs. grouped

BALANCE TYPES:
  SYMMETRIC: Equal weight on both sides. Formal, stable, calm.
  ASYMMETRIC: Unequal weight balanced by distance from center.
    → A small heavy element (bright color) can balance a large light element (gray).
    → More dynamic and interesting than symmetry.
  RADIAL: Weight emanates from a center point. Energetic, active.

THE BALANCE TEST:
  Squint at your layout. Does it feel like it would tip to one side?
  Weight should feel intentional — either balanced or deliberately tilted for effect.
```

# EYE MOVEMENT AND FLOW

## Directing the Journey
```
F-PATTERN (text-heavy pages):
  Readers scan the top, then scan again lower, then read left to right in
  descending strips. Critical content belongs top-left.
  → Place the most important CTA in the first F-scan zone.

Z-PATTERN (image-heavy, minimal text):
  Eye moves top-left → top-right → diagonal → bottom-left → bottom-right.
  → Natural for landing pages, ads, and poster layouts.

CIRCULAR / GUIDED:
  Use visual cues to create a loop or pathway:
  → Arrows, lines, glances (faces looking toward content), pointing fingers
  → Curved text or shapes that lead the eye
  → A sequence of elements spaced to suggest motion

LINE OF SIGHT:
  If there's a face in your design, the viewer follows its gaze.
  → Face looking at the headline: reader looks at the headline.
  → Face looking off-frame: reader looks off-frame. (Don't do this.)
```

# COMPOSITION TECHNIQUES

## Classic Compositional Tools
```
RULE OF THIRDS:
  Divide the canvas into a 3×3 grid. Place key elements at intersections.
  Feels natural because it avoids dead-center symmetry.

GOLDEN RATIO (1:1.618):
  Proportion that recurs in nature. A canvas at 1:1.618 or sections divided 
  by this ratio feel inherently pleasing.
  → Practical: use a 5:8 proportion for major content regions.

LEADING LINES:
  Real or implied lines that pull the eye toward a focal point.
  → Roads, shadows, arms, architectural lines — all direct attention.

NEGATIVE SPACE AS SHAPE:
  The space around your subject can be as interesting as the subject.
  → Silhouette + empty space creates more tension than a filled composition.
  → The FedEx arrow. The space between the leaves. The gap in the typeface.

FRAMING:
  Use elements within the scene to create a frame around the subject.
  → Archways, windows, hands, branches — all focus the eye inward.
```

# HIERARCHY CHECKLIST
```
Clarity:
[ ] One element is unambiguously the most important thing on the layout
[ ] The reading order is obvious: Level 1 → 2 → 3 → 4
[ ] A 3-second glance test reveals the main message

Layout:
[ ] All spacing uses 8pt multiples
[ ] All elements align to an underlying grid
[ ] One intentional grid breakout exists (if appropriate to the piece)
[ ] Asymmetric balance used for dynamism (or symmetric for formality)

Grouping:
[ ] Related elements are visually grouped (proximity)
[ ] Groups are separated by more space than the internal element spacing
[ ] No redundant container boxes — space does the grouping

Whitespace:
[ ] Each section has enough breathing room to feel intentional
[ ] The most important element has the most space around it
[ ] Nothing feels cramped

Ambition:
[ ] Would the layout stop someone mid-scroll?
[ ] Is there a compositional surprise that rewards a second look?
[ ] Could any element be removed to make the remaining elements stronger?
```
