---
name: swe_coding_style
description: Behavioral guidelines to enforce simplicity, surgical code edits, and the library-first principle (don't reinvent the wheel).
---

# Software Engineering Coding Style Guidelines

This skill enforces clean, minimal, and modular code, incorporating Andrej Karpathy's coding discipline and token-conservation strategies.

## 1. Think Before Coding
- **State Assumptions**: Before modifying or adding code, write down your implementation assumptions. If a requirement is ambiguous, clarify it first.
- **No Speculative Design**: Do not write abstractions for code that is only used once. Do not add "flexibility" or "configurability" parameters that were not requested.

## 2. Library-First Principle (Don't Reinvent the Wheel)
- **Search First**: Before implementing any complex algorithm, utility function, or parsing logic (e.g., custom retry loops, custom logging setups, custom date parsers), check if a standard, robust Python library exists in the ecosystem.
- **Prefer Packages**: Prefer installing and configuring established packages over custom-written solutions. Examples:
  - Use `tenacity` for robust retry logic on API connections.
  - Use `pydantic` or `dataclasses` for data validation and schema definitions.
  - Use `loguru` or standard `logging` for structured application logs.
- **Document Decisions**: When choosing to write custom logic instead of importing a library, document the technical rationale in the code comments.

## 3. Simplicity & Surgical Changes
- **Minimum Code**: Write the absolute minimum lines of code to solve the problem. If a 10-line function solves the task, do not write a 40-line general-purpose class.
- **Surgical Edits**: Touch *only* the lines and files required by the task.
  - Do not clean up adjacent formatting or unrelated style mismatches.
  - Match the style of the surrounding file exactly.
- **Clean Up Orphans**: When your code changes make variables, functions, or imports unused, delete them immediately.

## 4. Token Conservation
- **Targeted Reading**: When using `view_file`, specify `StartLine` and `EndLine` to read only the lines you need. Do not read the entire file if it is larger than 100 lines.
- **Targeted Writing**: Use `replace_file_content` with a precise `TargetContent` search block to edit files surgically. Do not overwrite or rewrite whole files unless necessary.
