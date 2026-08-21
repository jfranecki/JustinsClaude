---
name: tui-design-defer-to-exemplars
description: Anchor every terminal-UI component decision to established TUI exemplars (btop, lazygit, yazi, Bagels) instead of generic web idiom
metadata:
  type: feedback
---

## Context / Trigger

You are building or extending a terminal UI (TUI) — or a terminal-*styled* web UI — in [YOUR_APP_NAME], and you are about to design a new component: its appearance, interactability, animation, responsiveness, or the purpose it serves. This applies equally to true terminal apps (curses, [TUI_FRAMEWORK] such as Textual/Bubble Tea/ratatui) and to web apps deliberately imitating the terminal aesthetic.

## Core Rule / Insight

Defer to the established TUI exemplar family rather than inventing a treatment or borrowing generic web idiom:

- **Gallery:** https://terminal-apps.dev/ — a curated collection of beautiful terminal UIs; the four exemplars below are its standouts.
- **btop** (https://github.com/aristocratos/btop), a C++ system monitor, shows how far pure text graphics can go: braille-dot history graphs streaming in real time at sub-cell resolution, gradient-tinted meters (per-core CPU bars that shift color with load), box titles notched into their borders, panels toggled by number key with the layout reflowing to fill the freed space, a full options and help screen rendered as an in-app overlay rather than a man page, and theme files that define whole gradients — not single colors — so every meter and graph reskins together.
- **lazygit** (https://github.com/jesseduffield/lazygit), a Go git client, is the reference for multi-panel focus and discoverability: a fixed panel grid where focus is shown by a bright border, per-panel tabs, a context-sensitive keybind footer plus a `?` cheatsheet menu, modal popups for menus, confirmations, and inputs that overlay the layout instead of navigating away from it, a live preview pane that tracks the selection as it moves, line- and hunk-level staging with range select, and spinner glyphs for async work — everything mouse-clickable, but keyboard-first.
- **yazi** (https://github.com/sxyazi/yazi), an async Rust file manager, is the reference for speed-as-design and progressive disclosure: a Miller-column layout (parent / current / preview), scrolling that stays instant with explicit loading states while slow previews resolve, in-terminal rendering of images, video thumbnails, and syntax-highlighted code in the preview pane, a segmented vim-style status bar (mode, file info, position), visual-mode multi-select, tabs, and a which-key-style popup that lists the valid continuations the moment you start a key chord.
- **Bagels** (https://github.com/EnhancedJax/Bagels), a Textual-based expense tracker, is a particularly rich source of widget patterns: animated glyph effects on welcome panels, dotted line charts with period paging (`<<< Last Month >>>`) and mode tabs, segmented budget bars with bracket labels, diagonal-hatch (`/////`) progress bars and empty states, week-band calendar/period selectors, a focus system (bright border on the focused section plus a per-section keybind footer and a jump mode), and date-grouped tables with tree-connector sub-rows.

Before building any new UI element, consult the exemplar whose specialty matches it — btop for charts, graphs, and meters; lazygit for panel layout, focus, and keybind discoverability; yazi for previews, navigation, and perceived speed; Bagels for individual widget treatments — then hold the design to the family-wide idiom:

- **Text-first controls** aligned to the monospace grid — no proportional-font widgets.
- **Keyboard parity**: every mouse action has a key, and keybinds are surfaced in the UI (footers, key chips).
- **Terminal-step animation** — `steps()`, blink, spinner glyphs — never smooth web easing.
- **Theme variables only** — no hardcoded colors, so the whole UI reskins together.

A coherent TUI design language is built from elements like notched borders (`┤ ├`), key chips, selection bands, meters, step-blink cursors, and breathing tints. Every new component must speak the language the app already has — extending the family's vocabulary, not importing web-app vocabulary alongside it.

## Expected Outcome

New components feel native to the terminal design family on first render, and the UI stays coherent as it grows. Without this rule, terminal-styled apps drift one component at a time into web idiom — smooth easing, proportional fonts, mouse-only affordances, one-off colors — until the aesthetic reads as a costume instead of a language.
