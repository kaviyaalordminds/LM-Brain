---
title: "Frontend"
category: "Web Development"
level: "Beginner"
type: "Knowledge"
status: "Complete"
---

# Frontend

## Definition
The frontend is the part of a web application that runs in the user's browser: the HTML structure, CSS presentation, and JavaScript behavior the user directly sees and interacts with.

## Why It Matters
The frontend is the entire experience a user has — every interaction, every visual state, every millisecond of perceived performance is a frontend concern.

## Core Concepts
- **Structure** — [[HTML]]
- **Presentation** — [[CSS]]
- **Behavior/Interactivity** — [[JavaScript]]
- **Rendering** — how the browser turns these into pixels ([[Browser Architecture]])

## How It Works
The browser downloads HTML, CSS, and JS; parses HTML into the [[DOM]] and CSS into the CSSOM; combines them into a render tree; and paints pixels. JavaScript can then modify the DOM in response to user interaction or data changes, causing the browser to re-render.

## Real-World Usage
Modern frontends are usually built with a component framework ([[React]], Vue, Svelte) rather than hand-written DOM manipulation, and bundled/optimized with tools like Vite or Webpack.

## Advantages
- Directly controls user experience and perceived performance.
- Can work offline/interactively via [[PWA|service workers]] and client-side state.

## Disadvantages
- Runs on hardware/networks you don't control — must handle a wide range of devices and connection speeds.
- All frontend code and data are visible to the end user; nothing here is a security boundary.

## Common Mistakes
- Shipping unnecessary JavaScript that hurts load performance.
- Duplicating validation/authorization logic on the client and treating it as sufficient.

## Best Practices
- Progressive enhancement: core content and functionality should work even if JS fails.
- Keep bundles small; measure with [[Core Web Vitals]].

## Related Topics
- [[Backend]]
- [[Full Stack]]
- [[Frontend Engineering]]
- [[DOM]]

## Prerequisites
- [[What Is Web Development]]
- [[Client Server Architecture]]

## Quick Revision
Frontend = HTML + CSS + JS running in the browser; owns UI, UX, and perceived performance; never trusted for security.

## Interview Questions
- What are the three core web technologies that make up the frontend, and what does each control?
- Why is client-side validation not sufficient for security?
