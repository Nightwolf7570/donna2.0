---
description: Execute an engineer prompt from docs/engineer-prompts/
argument-hint: <prompt-number> (e.g., 13, 14, 15)
---

# Command: /engineer

Execute an engineer prompt from `/docs/engineer-prompts/`. These prompts contain detailed implementation guides for specific features.

## Usage

`/engineer <number>` - Execute the prompt with the given number (e.g., `/engineer 13` runs `13-parallel-build-execution.md`)

## Available Prompts

Check `/docs/engineer-prompts/` for available prompts. Format: `<number>-<feature-name>.md`

## Instructions

1. **Read the full prompt** from `/docs/engineer-prompts/$ARGUMENTS.md` (match by number prefix)
2. **Create a todo list** from the phases/tasks outlined in the prompt
3. **Execute each phase** systematically, following the implementation details
4. **Test thoroughly** - run `npm run test`, `npm run test:convex`, and `npm run build`
5. **Update progress** - mark `/docs/plan/progress.md` with completed items
6. **Commit changes** - use `/commit` after significant progress
7. **Update CHANGELOG** - document what was implemented

## Critical Rules

- Follow the prompt's structure exactly (phases, file paths, code patterns)
- Run `npm run build` before committing to catch type errors
- Test new functionality manually if E2E tests aren't covering it
- If blocked, document the issue and ask for clarification
- Never skip validation checklists at the end of prompts

## Example

```
/engineer 13
```

This will:
1. Read `docs/engineer-prompts/13-parallel-build-execution.md`
2. Implement parallel build execution as specified
3. Create the new files and modify existing ones per the prompt
4. Run tests and verify the build passes
5. Commit and update changelog
