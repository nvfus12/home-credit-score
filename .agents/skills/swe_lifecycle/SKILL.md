---
name: swe_lifecycle
description: Guidelines for task planning, progress tracking via ledger, Git branching strategy, and shipping code in the software engineering lifecycle.
---

# Software Engineering Lifecycle Guidelines

This skill guides the high-level workflow of the project, ensuring systematic progress, version control sanity, and clean releases.

## 1. Task Planning & Execution

- **Task Board (`task.md`)**:
  - Maintain a project-level `task.md` in the conversation artifacts.
  - Mark items as `[/]` (in progress) and `[x]` (completed) immediately when transitions happen.
- **Continuous Progress**:
  - Do not pause to ask the user "Should I proceed to Task N?" unless blocked by a major architectural design decision.
  - Work sequentially through tasks defined in the implementation plan.

## 2. Durable Progress Ledger

To prevent state/context loss due to context window compaction, maintain a progress ledger:
- **Ledger File**: Maintain a persistent file at `.agents/progress_ledger.md` in the project root.
- **Recording Progress**: After a task is completed, verified, and reviewed, append a single line:
  `Task N: complete (commits <base7>..<head7>, review clean)`
- **Recovery Protocol**: If the context window is compacted or reset, inspect this ledger first to verify completed commits and resume execution from the first incomplete task.

## 3. Git Workflow & Versioning

- **Branching Strategy**:
  - Always work in descriptive feature branches (e.g., `feat/langgraph-setup`, `fix/pdf-parser-tables`). Never work directly on `main`/`master` without confirmation.
  - Base the branch on the latest clean state of the main branch.
- **Commit Guidelines**:
  - Commit small, modular changes. Do not bundle multiple unrelated tasks into a single commit.
  - Use conventional commit prefixes:
    - `feat:` for new features or business logic.
    - `fix:` for bug fixes.
    - `test:` for writing unit/integration tests.
    - `docs:` for markdown guidelines or readme updates.
    - `refactor:` for codebase organization with no behavior changes.

## 4. Shipping & Release

Before finalizing a branch or completing the implementation plan:
- Clean up unused imports, dead variables, and debug print/log statements.
- Ensure the project builds cleanly.
- Verify that 100% of tests pass.
- Write a clear, structured `walkthrough.md` summarizing the changes, files modified, and test outputs.
