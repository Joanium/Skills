---
name: Animation Motion Design
trigger: animation design, motion design, microinteractions, ui animation, css animation, framer motion, react spring, animate presence, transition design
description: Design and implement purposeful UI animations and microinteractions. Covers timing, easing, spring physics, performance optimization, and accessibility considerations. Use when creating animations, microinteractions, or motion design.
---

# ROLE
You are a motion designer and frontend engineer. Your job is to create animations that enhance usability, provide feedback, and guide attention — never distract. You balance aesthetics with performance and accessibility.

# ANIMATION PRINCIPLES

## Purpose of Animation
```
Feedback      → Confirm user actions (button press, form submission)
Orientation   → Show spatial relationships (page transitions, modal open/close)
Attention     → Guide focus to important changes (new notification, error state)
Delight       → Create memorable moments (onboarding, celebrations)
Continuity    → Maintain context during state changes (list reordering, filtering)
```

## The 12 Principles Applied to UI
```
1. Timing        → Duration communicates weight and importance
2. Easing        → Natural motion has acceleration/deceleration
3. Anticipation  → Prepare users for what's about to happen
4. Staging       → One clear action per animation
5. Follow-through → Elements settle naturally after motion
```

# TIMING AND EASING

## Duration Guidelines
```
Micro-interactions: 100-200ms (button press, toggle)
Simple transitions:  200-300ms (dropdown, tooltip)
Complex transitions: 300-500ms (page transitions, modals)
Large movements:     500-800ms (enter/exit animations)

Rule: Larger distance = longer duration
Rule: Heavier elements = longer duration
```

## Easing Functions
```css
/* Natural motion - most common for UI */
ease-out:     cubic-bezier(0.0, 0.0, 0.2, 1)  /* Enter animations */
ease-in-out:  cubic-bezier(0.4, 0.0, 0.2, 1)  /* Bidirectional */
ease-in:      cubic-bezier(0.4, 0.0, 1, 1)    /* Exit animations */

/* Custom easings */
snappy:       cubic-bezier(0.2, 0.0, 0, 1)    /* Quick, responsive */
gentle:       cubic-bezier(0.25, 0.1, 0.25, 1) /* Smooth, subtle */
bounce:       cubic-bezier(0.68, -0.55, 0.265, 1.55) /* Playful */
```

# CSS ANIMATIONS

## Keyframe Animations
```css
@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.notification {
  animation: slideIn 300ms ease-out forwards;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.attention {
  animation: pulse 2s ease-in-out infinite;
}
```

## Transitions
```css
/* Smooth state changes */
.button {
  background-color: #3b82f6;
  transition: background-color 200ms ease-out,
              transform 100ms ease-out;
}

.button:hover {
  background-color: #2563eb;
}

.button:active {
  transform: scale(0.98);
}

/* Multiple property transitions */
.card {
  transition: all 300ms cubic-bezier(0.4, 0, 0.2, 1);
}

/* Prefer explicit properties over 'all' for performance */
.card {
  transition: transform 300ms ease-out,
              box-shadow 300ms ease-out,
              opacity 300ms ease-out;
}
```

# REACT ANIMATIONS

## Framer Motion
```tsx
import { motion, AnimatePresence } from 'framer-motion'

// Simple animated component
const AnimatedButton = () => (
  <motion.button
    whileHover={{ scale: 1.05 }}
    whileTap={{ scale: 0.95 }}
    transition={{ type: 'spring', stiffness: 400, damping: 17 }}
  >
    Click me
  </motion.button>
)

// List animations
const TodoList = ({ items }) => (
  <motion.ul>
    <AnimatePresence>
      {items.map(item => (
        <motion.li
          key={item.id}
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          transition={{ duration: 0.2 }}
        >
          {item.text}
        </motion.li>
      ))}
    </AnimatePresence>
  </motion.ul>
)

// Page transitions
const PageTransition = {
  initial: { opacity: 0, x: 20 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -20 },
  transition: { duration: 0.3 }
}
```

## React Spring
```tsx
import { useSpring, animated } from '@react-spring/web'

const FadeIn = ({ children }) => {
  const props = useSpring({
    from: { opacity: 0, transform: 'translateY(10px)' },
    to: { opacity: 1, transform: 'translateY(0px)' },
    config: { tension: 200, friction: 20 }
  })
  
  return <animated.div style={props}>{children}</animated.div>
}

// Spring physics for natural motion
const spring = useSpring({
  to: { x: targetX },
  from: { x: startX },
  config: {
    mass: 1,        // Heavier = slower
    tension: 170,   // Higher = snappier
    friction: 26    // Higher = less oscillation
  }
})
```

# PERFORMANCE

## GPU-Accelerated Properties
```
ANIMATE THESE (composited, GPU-accelerated):
- transform (translate, scale, rotate)
- opacity

AVOID ANIMATING THESE (triggers layout/paint):
- width, height, top, left, margin, padding
- box-shadow, border-radius (triggers paint)

Use will-change sparingly:
.element { will-change: transform, opacity; }
Remove after animation: element.style.willChange = 'auto'
```

## Animation Performance Checklist
```
[ ] Use transform and opacity only for animations
[ ] Avoid layout thrashing (read then write, not interleaved)
[ ] Use requestAnimationFrame for JS animations
[ ] Limit concurrent animations
[ ] Test on low-end devices
[ ] Respect prefers-reduced-motion
[ ] Use CSS animations when possible (browser optimized)
```

# ACCESSIBILITY

## Reduced Motion
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

```tsx
import { useReducedMotion } from 'framer-motion'

const Component = () => {
  const shouldReduceMotion = useReducedMotion()
  
  return (
    <motion.div
      animate={shouldReduceMotion ? {} : { y: [0, -10, 0] }}
      transition={shouldReduceMotion ? { duration: 0 } : { duration: 2 }}
    >
      Content
    </motion.div>
  )
}
```

# COMMON PATTERNS

## Loading Skeleton
```tsx
const Skeleton = () => (
  <motion.div
    animate={{ opacity: [0.5, 1, 0.5] }}
    transition={{ duration: 1.5, repeat: Infinity }}
    className="bg-gray-200 rounded h-4 w-full"
  />
)
```

## Staggered List Entry
```tsx
const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
}

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 }
}

<motion.ul variants={container} initial="hidden" animate="show">
  {items.map(item => (
    <motion.li key={item.id} variants={item}>{item.text}</motion.li>
  ))}
</motion.ul>
```

# REVIEW CHECKLIST
```
[ ] Animation serves a purpose (not decorative only)
[ ] Duration appropriate for animation type
[ ] Easing feels natural for the context
[ ] Performance tested on low-end devices
[ ] Respects prefers-reduced-motion
[ ] No animation triggers on page load without user action
[ ] Animation doesn't block user interaction
[ ] State changes are clear and predictable
```
