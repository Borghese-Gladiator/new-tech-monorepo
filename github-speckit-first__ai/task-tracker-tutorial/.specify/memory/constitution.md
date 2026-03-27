<!--
  Sync Impact Report
  ==================
  Version change: 0.0.0 → 1.0.0 (initial ratification)
  Modified principles: N/A (first version)
  Added sections:
    - Core Principles (6 principles)
    - Technology Constraints
    - Development Workflow
    - Governance
  Removed sections: None
  Templates requiring updates:
    - .specify/templates/plan-template.md ✅ no changes needed (Constitution Check section is generic)
    - .specify/templates/spec-template.md ✅ no changes needed (already requires user scenarios + testing)
    - .specify/templates/tasks-template.md ✅ no changes needed (test tasks align with testing principle)
  Follow-up TODOs: None
-->

# Task Tracker Tutorial Constitution

## Core Principles

### I. Simplicity

Every architectural decision MUST favor the simplest viable approach.

- The application MUST use a flat, readable project structure
- No abstractions unless the same logic appears in three or more places
- New patterns or layers MUST be justified against a simpler alternative
- YAGNI: features not yet needed MUST NOT be built speculatively

**Rationale**: This is a tutorial app — clarity for readers is the
primary design goal.

### II. Minimal Dependencies

The project MUST minimize external dependencies.

- Every new dependency MUST be justified with a concrete need that
  cannot be met with built-in language/platform APIs
- Prefer standard library solutions over third-party packages
- No dependency MAY be added solely for convenience if the equivalent
  code is under ~30 lines

**Rationale**: Fewer dependencies reduce bundle size, security
surface, and cognitive overhead for tutorial readers.

### III. Testing Discipline

All features MUST include both happy-path and failure-path tests.

- Every user-facing feature MUST have at least one happy-path test
  demonstrating correct behavior
- Every user-facing feature MUST have at least one failure-path test
  demonstrating graceful error handling
- Tests MUST be co-located or clearly mapped to the code they cover
- Test names MUST describe the scenario, not the implementation

**Rationale**: Tutorial code that ships without tests teaches bad
habits. Covering both paths ensures real-world resilience.

### IV. Accessibility

Core user flows MUST be accessible.

- All interactive elements MUST be keyboard-navigable
- Form inputs MUST have associated labels
- Color MUST NOT be the sole means of conveying information
- Core flows MUST pass WCAG 2.1 Level A criteria
- Semantic HTML elements MUST be used over generic divs/spans
  where an appropriate element exists

**Rationale**: Accessibility is a baseline quality bar, not an
afterthought. Tutorial apps MUST model inclusive design.

### V. Performance

The app MUST feel fast on first load and work well on mobile.

- Initial page load MUST NOT include unused JavaScript bundles
- Images and heavy assets MUST be lazy-loaded or deferred
- Layout MUST be responsive and usable on screens ≥ 320px wide
- No layout shift MAY occur during initial render of above-the-fold
  content
- Interactive elements MUST have touch targets ≥ 44×44px on mobile

**Rationale**: Tutorial users often test on low-end devices or
throttled connections. Performance is a feature.

### VI. Code Clarity

All code MUST use clear naming and small functions.

- Function and variable names MUST describe intent, not
  implementation (e.g., `getOverdueTasks` not `filterArr`)
- Functions MUST do one thing; if a function requires an "and" to
  describe, it MUST be split
- No function body SHOULD exceed ~20 lines; longer functions MUST
  be reviewed for extraction opportunities
- Boolean variables and functions MUST read as yes/no questions
  (e.g., `isComplete`, `hasPermission`)

**Rationale**: Readers learn patterns from tutorial code. Clear,
small functions are easier to understand and reuse.

## Technology Constraints

- The app is a small, self-contained tutorial web application
- Prefer vanilla or near-vanilla solutions; heavy frameworks MUST
  be justified
- Build tooling MUST be minimal and standard (no custom plugins
  unless absolutely required)
- The project MUST remain runnable with a single install + start
  command sequence

## Development Workflow

- All changes MUST be scoped and incremental — one concern per
  commit
- Code review MUST verify compliance with this constitution
- Every PR MUST include evidence that both happy-path and
  failure-path tests pass
- Accessibility checks MUST be part of the PR review checklist for
  UI changes
- Performance regressions MUST be flagged before merge

## Governance

This constitution is the authoritative source of project standards.
All code, reviews, and architectural decisions MUST comply.

- **Amendments**: Any principle change MUST be documented with
  rationale, approved by the project owner, and reflected in a
  version bump
- **Versioning**: MAJOR for principle removals/redefinitions, MINOR
  for new principles or expanded guidance, PATCH for wording fixes
- **Compliance**: Every PR review MUST include a constitution
  compliance check. Violations MUST be resolved before merge.

**Version**: 1.0.0 | **Ratified**: 2026-03-27 | **Last Amended**: 2026-03-27
