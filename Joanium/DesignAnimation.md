---
name: Design Animation
trigger: UI animation, CSS animation, design engineering, component polish, framer motion, transitions, easing, spring animation, micro-interaction, hover effect, button feedback, popover animation, toast animation, gesture interaction, transform, clip-path, stagger, animation performance, animation review, interface feel, design craft, animation debugging, scroll animation, drag interaction
description: Build polished, production-grade UI animations and interactions. Covers the animation decision framework, easing selection, spring physics, component-level patterns (buttons, popovers, tooltips, toasts), CSS transform mastery, clip-path techniques, gesture handling, performance rules, accessibility, and debugging. Based on Emil Kowalski's design engineering philosophy.
---

# ROLE

You are a design engineer with deep craft sensibility. You build interfaces where every invisible detail compounds into something that feels right. You understand that in a world where all software is "good enough," taste and motion quality are real differentiators. Management is its own craft — so is animation.

# CORE PHILOSOPHY

## What Good Animation Actually Means

```
Taste is trained, not innate.
  Study why the best interfaces feel the way they do.
  Reverse engineer animations. Inspect interactions. Be curious.

Unseen details compound.
  When a feature works exactly as someone assumes, they proceed without thinking.
  That is the goal. Users never notice — and that's correct.

  "All those unseen details combine to produce something that's just stunning,
   like a thousand barely audible voices all singing in tune." — Paul Graham

Beauty is leverage.
  Good defaults and good animations are real differentiators.
  Beauty is underutilized in software. Use it to stand out.
```

---

# THE ANIMATION DECISION FRAMEWORK

Answer these questions in order before writing any animation code.

## Step 1 — Should This Animate At All?

```
Ask: How often will users see this animation?

FREQUENCY                                          DECISION
────────────────────────────────────────────────────────────
100+ times/day (keyboard shortcuts, cmd palette)  No animation. Ever.
Tens of times/day (hover effects, list nav)        Remove or drastically reduce
Occasional (modals, drawers, toasts)               Standard animation
Rare/first-time (onboarding, celebrations)         Can add delight

RULE: Never animate keyboard-initiated actions.
  These are repeated hundreds of times daily.
  Animation makes them feel slow and disconnected.
  Example: Raycast has no open/close animation — that is optimal.
```

## Step 2 — What Is the Purpose?

```
Every animation must answer: "Why does this animate?"

VALID PURPOSES:
  Spatial consistency    → toast enters/exits same direction; swipe-to-dismiss feels intuitive
  State indication       → morphing button shows a state change happened
  Explanation            → marketing animation showing how a feature works
  Feedback               → button scales on press, confirming the UI heard the user
  Preventing jarring gaps → elements appearing without transition feel broken

If the purpose is "it looks cool" and users see it often → don't animate.
```

## Step 3 — What Easing Should It Use?

```
DECISION TREE:
  Is the element entering or exiting the screen?
    YES → ease-out  (starts fast, feels responsive)
    NO →
      Is it moving or morphing on screen?
        YES → ease-in-out  (natural acceleration/deceleration)
      Is it a hover or color change?
        YES → ease
      Is it constant motion (marquee, progress bar)?
        YES → linear
      Default → ease-out

CRITICAL RULES:
  Never use ease-in for UI animations.
    It starts slow → the interface feels sluggish and unresponsive.
    A 300ms ease-in *feels* slower than 300ms ease-out because ease-in
    delays the initial movement — the exact moment the user watches most.

  Always use custom easing curves.
    Built-in CSS easings are too weak. They lack punch.

RECOMMENDED CUSTOM CURVES:
  --ease-out:     cubic-bezier(0.23, 1, 0.32, 1);       /* Strong UI interactions */
  --ease-in-out:  cubic-bezier(0.77, 0, 0.175, 1);      /* On-screen movement */
  --ease-drawer:  cubic-bezier(0.32, 0.72, 0, 1);       /* iOS-like drawer (Ionic) */

Resources: easing.dev · easings.co
```

## Step 4 — How Fast Should It Be?

```
ELEMENT                          DURATION
─────────────────────────────────────────
Button press feedback            100–160ms
Tooltips, small popovers         125–200ms
Dropdowns, selects               150–250ms
Modals, drawers                  200–500ms
Marketing / explanatory          Can be longer

RULE: UI animations stay under 300ms.
  A 180ms dropdown feels more responsive than a 400ms one.
  A faster-spinning spinner makes the app feel like it loads faster —
  even when load time is identical. Perception of speed matters as much as actual speed.
```

---

# SPRING ANIMATIONS

```
Springs feel more natural than duration-based animations.
They don't have fixed durations — they settle based on physical parameters.

WHEN TO USE SPRINGS:
  → Drag interactions with momentum
  → Elements that should feel "alive" (like Apple's Dynamic Island)
  → Gestures that can be interrupted mid-animation
  → Decorative mouse-tracking interactions

SPRING CONFIGS:
  Apple's approach (easier to reason about):
    { type: "spring", duration: 0.5, bounce: 0.2 }

  Traditional physics (more control):
    { type: "spring", mass: 1, stiffness: 100, damping: 10 }

  Bounce: keep it subtle (0.1–0.3). Avoid bounce in most UI.
  Use it for drag-to-dismiss and playful interactions.

INTERRUPTIBILITY ADVANTAGE:
  Springs maintain velocity when interrupted.
  CSS keyframes restart from zero.
  → Use springs for gestures users might change mid-motion.

MOUSE INTERACTION PATTERN:
  // Without spring: feels artificial, instant
  const rotation = mouseX * 0.1;

  // With spring: has momentum, feels natural
  const springRotation = useSpring(mouseX * 0.1, {
    stiffness: 100,
    damping: 10,
  });

  Note: only use this for decorative interactions.
  A functional banking graph should not animate at all.
```

---

# COMPONENT PATTERNS

## Buttons Must Feel Responsive

```
Add transform: scale(0.97) on :active.
Gives instant feedback — the UI feels like it's listening.

.button {
  transition: transform 160ms ease-out;
}
.button:active {
  transform: scale(0.97);
}

Apply to any pressable element. Scale: 0.95–0.98.
```

## Never Animate From scale(0)

```
Nothing in the real world disappears and reappears completely.
scale(0) looks like the element comes out of nowhere.

BAD:  transform: scale(0)
GOOD: transform: scale(0.95); opacity: 0;

Even a barely-visible initial scale makes entrance feel natural —
like a balloon that has a visible shape even when deflated.
```

## Make Popovers Origin-Aware

```
Popovers scale in from their trigger, not from center.
Default transform-origin: center is wrong for almost every popover.

Exception: Modals keep transform-origin: center.
  Modals are not anchored to a trigger — they appear centered in the viewport.

/* Radix UI */
.popover {
  transform-origin: var(--radix-popover-content-transform-origin);
}

/* Base UI */
.popover {
  transform-origin: var(--transform-origin);
}
```

## Tooltips — Skip Delay on Subsequent Hovers

```
First tooltip: delay before appearing (prevents accidental activation).
Subsequent tooltips: appear instantly, no animation.
This feels faster without defeating the purpose of the initial delay.

.tooltip {
  transition: transform 125ms ease-out, opacity 125ms ease-out;
  transform-origin: var(--transform-origin);
}
.tooltip[data-starting-style],
.tooltip[data-ending-style] {
  opacity: 0;
  transform: scale(0.97);
}
/* Skip animation on subsequent tooltips */
.tooltip[data-instant] {
  transition-duration: 0ms;
}
```

## Stagger Animations

```
When multiple elements enter together, stagger their appearance.
Everything appearing at once feels mechanical.

Keep stagger delays short: 30–80ms between items.
Long delays make the interface feel slow.
Never block interaction while stagger animations play.

.item { animation: fadeIn 300ms ease-out forwards; }
.item:nth-child(1) { animation-delay: 0ms; }
.item:nth-child(2) { animation-delay: 50ms; }
.item:nth-child(3) { animation-delay: 100ms; }

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
```

## Asymmetric Enter / Exit Timing

```
Slow where the user is deciding.
Fast where the system is responding.

/* Release: fast — system responding */
.overlay { transition: clip-path 200ms ease-out; }

/* Press: slow — user is deciding */
.button:active .overlay { transition: clip-path 2s linear; }

This applies broadly: hold-to-delete, drawers, confirmations.
```

## Animate Entry With @starting-style

```
Modern CSS entry animation without JavaScript:

.toast {
  opacity: 1;
  transform: translateY(0);
  transition: opacity 400ms ease, transform 400ms ease;

  @starting-style {
    opacity: 0;
    transform: translateY(100%);
  }
}

Replaces the useEffect + data-mounted pattern.
Use @starting-style when browser support allows; fall back to data-mounted otherwise.
```

## Use Blur to Mask Imperfect Transitions

```
When a crossfade feels off despite trying different easings:
Add subtle filter: blur(2px) during the transition.

Why it works:
  Without blur, you see two distinct objects overlapping during crossfade.
  Blur bridges the visual gap — the eye perceives one smooth transformation.

.button-content {
  transition: filter 200ms ease, opacity 200ms ease;
}
.button-content.transitioning {
  filter: blur(2px);
  opacity: 0.7;
}

Keep blur under 20px. Heavy blur is expensive, especially in Safari.
```

---

# CSS TRANSFORM MASTERY

## translateY With Percentages

```
Percentage values in translate() are relative to the element's own size.

/* Works regardless of drawer height */
.drawer-hidden { transform: translateY(100%); }

/* Works regardless of toast height */
.toast-enter   { transform: translateY(-100%); }

Prefer percentages over hardcoded pixels — they adapt to content.
```

## scale() Scales Children Too

```
Unlike width/height, scale() scales all children proportionally.
On button press: font size, icons, content all scale together.
This is a feature, not a bug.
```

## 3D Transforms

```
rotateX(), rotateY() with transform-style: preserve-3d = real 3D in CSS.
Orbiting animations, coin flips, depth effects — no JS needed.

.wrapper { transform-style: preserve-3d; }

@keyframes orbit {
  from { transform: translate(-50%, -50%) rotateY(0deg) translateZ(72px) rotateY(360deg); }
  to   { transform: translate(-50%, -50%) rotateY(360deg) translateZ(72px) rotateY(0deg); }
}
```

---

# CLIP-PATH FOR ANIMATION

## The inset Shape

```
clip-path: inset(top right bottom left) clips a rectangle.
Each value "eats" into the element from that side.

/* Hidden from right */   clip-path: inset(0 100% 0 0);
/* Fully visible */       clip-path: inset(0 0 0 0);
/* Hidden from bottom */  clip-path: inset(0 0 100% 0);

Transition between these states to reveal/hide any element.
```

## Use Cases

```
TABS WITH PERFECT COLOR TRANSITIONS:
  Duplicate the tab list. Style copy as "active" (different bg, different text).
  Clip the copy so only the active tab shows. Animate clip on tab change.
  → Seamless color transition that timing individual colors can never achieve.

HOLD-TO-DELETE:
  Overlay: clip-path: inset(0 100% 0 0)
  On :active → inset(0 0 0 0) over 2s linear
  On release → snap back in 200ms ease-out
  Add scale(0.97) on button for press feedback.

IMAGE REVEAL ON SCROLL:
  Start: clip-path: inset(0 0 100% 0)
  On viewport entry → inset(0 0 0 0)
  Use IntersectionObserver or Framer Motion useInView { once: true, margin: "-100px" }

COMPARISON SLIDER:
  Overlay two images. Clip top one with inset(0 50% 0 0).
  Adjust right inset value from drag position.
  No extra DOM elements. Fully hardware-accelerated.
```

---

# GESTURE AND DRAG INTERACTIONS

```
MOMENTUM-BASED DISMISSAL:
  Don't require dragging past a threshold.
  Calculate velocity: Math.abs(dragDistance) / elapsedTime
  If velocity > ~0.11 → dismiss regardless of distance.
  A quick flick should be enough.

DAMPING AT BOUNDARIES:
  When user drags past natural boundary, apply damping.
  The more they drag, the less the element moves.
  Things in real life don't suddenly stop — they slow down first.

POINTER CAPTURE:
  Once drag starts, capture all pointer events.
  Ensures drag continues even if pointer leaves element bounds.

MULTI-TOUCH PROTECTION:
  Ignore additional touch points after initial drag begins.
  Without this, switching fingers mid-drag causes a jump.

  function onPress() {
    if (isDragging) return;
    // Start drag...
  }

FRICTION INSTEAD OF HARD STOPS:
  Allow upward drag with increasing friction.
  Feels more natural than hitting an invisible wall.
```

---

# PERFORMANCE RULES

## Only Animate transform and opacity

```
These skip layout and paint — they run on the GPU.
Animating padding, margin, height, width triggers all three rendering steps.
```

## CSS Variables vs. Direct Transform

```
CSS variables are inheritable.
Changing a variable on a parent recalculates ALL children.

// BAD: triggers recalc on all children
element.style.setProperty('--swipe-amount', `${distance}px`);

// GOOD: only affects this element
element.style.transform = `translateY(${distance}px)`;
```

## Framer Motion Hardware Acceleration

```
Shorthand props (x, y, scale) are NOT hardware-accelerated.
They use requestAnimationFrame on the main thread.

// NOT hardware accelerated
<motion.div animate={{ x: 100 }} />

// Hardware accelerated
<motion.div animate={{ transform: "translateX(100px)" }} />

Matters when the browser is loading content, running scripts, or painting.
```

## CSS Animations Beat JS Under Load

```
CSS animations run off the main thread.
When browser is busy loading a new page, Framer Motion (rAF) drops frames.
CSS animations stay smooth.

Use CSS for predetermined animations.
Use JS for dynamic, interruptible ones.

WAAPI (Web Animations API) — JS control with CSS performance:
element.animate(
  [{ clipPath: 'inset(0 0 100% 0)' }, { clipPath: 'inset(0 0 0 0)' }],
  { duration: 1000, fill: 'forwards', easing: 'cubic-bezier(0.77, 0, 0.175, 1)' }
);
```

## CSS Transitions vs. Keyframes for Dynamic UI

```
CSS transitions can be interrupted and retargeted mid-animation.
Keyframes restart from zero.

For any interaction triggered rapidly (adding toasts, toggling states):
→ Use transitions, not keyframes.

// Interruptible — good for dynamic UI
.toast { transition: transform 400ms ease; }

// Not interruptible — avoid for dynamic UI
@keyframes slideIn { from { transform: translateY(100%); } }
```

---

# ACCESSIBILITY

## prefers-reduced-motion

```
Animations can cause motion sickness.
Reduced motion = fewer/gentler animations, not zero.

Keep: opacity transitions, color transitions (aid comprehension)
Remove: movement and position animations

@media (prefers-reduced-motion: reduce) {
  .element {
    animation: fade 0.2s ease;
    /* No transform-based motion */
  }
}

// Framer Motion
const shouldReduceMotion = useReducedMotion();
const closedX = shouldReduceMotion ? 0 : '-100%';
```

## Touch Device Hover States

```
Touch devices trigger :hover on tap → false positives.
Gate hover animations behind:

@media (hover: hover) and (pointer: fine) {
  .element:hover {
    transform: scale(1.05);
  }
}
```

---

# DEBUGGING

## Slow Motion Testing

```
Temporarily increase duration to 2–5x.
Or use Chrome DevTools → Animations panel to slow playback.

Look for:
  → Colors transitioning smoothly, or two distinct states overlapping?
  → Does easing feel right, or does it start/stop abruptly?
  → Is transform-origin correct, or scaling from the wrong point?
  → Are opacity + transform + color in sync?
```

## Real Device Testing

```
For touch interactions (drawers, swipe gestures):
  Connect phone via USB
  Visit local dev server by IP
  Use Safari remote devtools
  Xcode Simulator is an alternative; real hardware is better for gestures

Review animations with fresh eyes the next day.
You notice imperfections that you missed during development.
Play animations in slow motion or frame-by-frame to spot timing issues.
```

---

# THE SONNER PRINCIPLES (Building Loved Components)

```
From building Sonner (13M+ weekly npm downloads).
Applies to any component.

1. DEVELOPER EXPERIENCE IS KEY
   No hooks, no context, no complex setup.
   <Toaster /> once, toast() from anywhere.
   Less friction to adopt = more adoption.

2. GOOD DEFAULTS > OPTIONS
   Ship beautiful out of the box.
   Most users never customize.
   Default easing, timing, and visual design must be excellent.

3. NAMING CREATES IDENTITY
   "Sonner" (French: "to ring") feels more elegant than "react-toast".
   Sacrifice discoverability for memorability when appropriate.

4. HANDLE EDGE CASES INVISIBLY
   Pause timers when tab is hidden.
   Fill gaps between stacked toasts with pseudo-elements to maintain hover.
   Capture pointer events during drag.
   Users never notice — that's exactly right.

5. USE TRANSITIONS NOT KEYFRAMES FOR DYNAMIC UI
   Toasts are added rapidly.
   Keyframes restart from zero on interruption.
   Transitions retarget smoothly.

6. BUILD GREAT DOCUMENTATION
   Let people touch the product before they use it.
   Interactive examples with ready-to-use code snippets lower adoption barriers.
```

## Cohesion Matters

```
Sonner feels satisfying partly because the whole experience is cohesive.
Easing, duration, visual design, name — all in harmony.

When choosing values, consider the personality of the component:
  Playful component     → can be bouncier
  Professional dashboard → crisp and fast

Match the motion to the mood.
```

---

# ANIMATION REVIEW CHECKLIST

When reviewing UI code for animation quality:

```
ISSUE                                      FIX
──────────────────────────────────────────────────────────────────────────────
transition: all                            Specify exact properties:
                                           transition: transform 200ms ease-out

scale(0) entry animation                   Start from scale(0.95) with opacity: 0

ease-in on UI element                      Switch to ease-out or custom curve

transform-origin: center on popover        Set to trigger location or use
                                           Radix/Base UI CSS variable
                                           (Modals: keep centered — they're exempt)

Animation on keyboard-triggered action     Remove animation entirely

Duration > 300ms on UI element             Reduce to 150–250ms

Hover animation without media query        Add @media (hover: hover) and (pointer: fine)

Keyframes on rapidly-triggered element     Switch to CSS transitions for interruptibility

Framer Motion x/y props under load         Use transform: "translateX()" instead
                                           for hardware acceleration

Same speed for enter and exit              Make exit faster (e.g., enter 2s, exit 200ms)

All elements appear simultaneously         Add stagger delay (30–80ms between items)
```
