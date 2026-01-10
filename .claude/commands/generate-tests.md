---
description: Generate comprehensive test suite for the entire application
---

# Command: Generate Tests

Generate a comprehensive test suite that validates the entire application works flawlessly. If all tests pass, the app should be production-ready.

## Test Coverage Layers

### Layer 1: Backend Unit Tests (Convex)
Test all Convex mutations and queries in `convex/`:
- `sessions.ts` — session CRUD, phase transitions, auth
- `users.ts` — user management, role checks
- `buildLogs.ts` — logging, retrieval
- `modelConfig.ts` — AI model configuration
- `adminLogs.ts` — admin operations

**Pattern:** Use `convex-test` + Vitest (see `convex/sessions.test.ts`)
**Run:** `npm run test:convex`

### Layer 2: Integration Tests
Test service integrations:
- Inngest workflow triggers and event handling
- Convex ↔ API route communication
- External API interactions (mocked)

**Run:** `npm run test:integration`

### Layer 3: E2E Tests (Playwright)
Test complete user journeys:
- **Auth flow:** Sign in, sign up, sign out, protected routes
- **Discovery flow:** Form validation, submission, session creation
- **Build dashboard:** Session display, phase progression, logs
- **Admin panel:** Model config, user management, logs viewing
- **Error handling:** Network failures, invalid inputs, edge cases

**Pattern:** See `tests/e2e/` for existing specs
**Run:** `npm run test:e2e`

## Execution Steps

1. **Audit** existing test coverage across all layers
2. **Identify gaps** — modules without tests, untested edge cases
3. **Prioritize** by criticality (auth > data mutations > UI)
4. **Generate** missing tests following project patterns
5. **Verify** all tests pass:
   ```bash
   npm run test:convex && npm run test && npm run test:e2e
   ```

## Critical Paths That MUST Be Tested

| Path | Tests Must Verify |
|------|-------------------|
| User signs up → creates project → sees build | Full flow works end-to-end |
| Unauthenticated access to `/dashboard` | Redirects to sign-in |
| User A cannot see User B's sessions | Data isolation enforced |
| Invalid form submission | Shows validation errors, doesn't save |
| Build fails mid-process | Session marked failed, user notified |
| Admin changes AI model | New model used for next build |

## Success Criteria

✅ All Convex mutations/queries have unit tests  
✅ All E2E specs cover critical user journeys  
✅ Auth and authorization enforced at every layer  
✅ `npm run test:convex && npm run test && npm run test:e2e` passes  

## Output

After generating tests, provide a coverage report (don't create a new file, just provide the report in the terminal):
```
Backend:     X/Y mutations tested
E2E:         X critical paths covered
Integration: X services validated
Status:      ✓ All tests passing
```
