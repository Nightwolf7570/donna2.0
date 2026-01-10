---
description: Sync skill expertise with current codebase changes
argument-hint: [skill-name or "all"]
---

# Command: Sync Skills

Update skill expertise with recent codebase changes. This validates existing patterns and discovers new conventions.

## Usage

```bash
/sync-skills convex          # Sync convex skill only
/sync-skills nextjs          # Sync nextjs skill only
/sync-skills shadcn          # Sync shadcn skill only
/sync-skills tech-stack      # Sync all 4 infrastructure expertise files
/sync-skills all             # Sync all skills
```

## What is Sync Skills?

**Self-Improvement = Learning from the Codebase**

Each skill has expertise file(s) that evolve over time. Sync skills:

1. **Reads current expertise** (mental model from `resources/*.yaml`)
2. **Explores codebase** (source of truth)
3. **Validates patterns** (checks what's still true, counts occurrences)
4. **Discovers new patterns** (finds new conventions, requires 3+ occurrences)
5. **Updates expertise file** (writes learnings, increments version)

**Result:** Skill knowledge synchronized with reality

## When to Run

**Recommended triggers:**

✅ **After significant error fixes** (agents will remind you)
- Fixed 3+ occurrences of same error
- Discovered new architectural pattern
- Implemented workaround that should be documented
- Changed core conventions

✅ **After major features** (5+ files changed)
- New patterns likely introduced
- Manual: `/sync-skills [affected-skill]`

✅ **After refactoring**
- Patterns may have changed
- Manual: `/sync-skills all`

✅ **Monthly maintenance**
- Keep expertise fresh
- Manual: `/sync-skills all`

✅ **When answers seem outdated**
- Skill gave wrong/outdated answer
- Manual: `/sync-skills [that-skill]`

**Don't run:**
❌ After every commit (too frequent)
❌ During active development (wait for stable state)
❌ When build is broken (fix first)

## How It Works

### For Individual Skills (convex, nextjs, shadcn)

```bash
/sync-skills convex
```

**Process:**
1. Load `.claude/skills/convex/resources/expertise.yaml`
2. Explore relevant codebase directories (convex/, lib/, etc.)
3. Validate existing patterns (count occurrences)
4. Discover new patterns (3+ occurrences required)
5. Update `resources/expertise.yaml`:
   - Add new patterns (if 3+ occurrences)
   - Update confidence levels (based on validation count)
   - Remove obsolete patterns (not found in 2+ runs)
   - Update file locations
   - Increment version
   - Add evolution log entry

**Output:** Summary of what changed

### For Unified Skill (tech-stack)

```bash
/sync-skills tech-stack
```

**Process:**
1. Syncs ALL 4 infrastructure expertise files:
   - `vercel-expertise.yaml` - Vercel deployment patterns
   - `inngest-expertise.yaml` - Inngest workflow patterns
   - `e2b-expertise.yaml` - E2B sandbox patterns
   - `clerk-expertise.yaml` - Clerk auth patterns
2. Each file validated independently
3. Aggregated summary at end

**Note:** This syncs ALL infrastructure expertise, not just one.

### For All Skills

```bash
/sync-skills all
```

**Process:**
1. Run self-improvement for each skill:
   - convex → `convex/resources/expertise.yaml`
   - nextjs → `nextjs/resources/expertise.yaml`
   - shadcn → `shadcn/resources/expertise.yaml`
   - tech-stack → All 4 expertise files
2. Aggregate results
3. Show summary for all skills

**Note:** Takes longer (4+ expertise files)

## Skill Mapping

| Command Arg | Skill Path | Expertise Files |
|-------------|------------|-----------------|
| `convex` | `.claude/skills/convex/` | `resources/expertise.yaml` |
| `nextjs` | `.claude/skills/nextjs/` | `resources/expertise.yaml` |
| `shadcn` | `.claude/skills/shadcn/` | `resources/expertise.yaml` |
| `tech-stack` | `.claude/skills/tech-stack/` | `resources/vercel-expertise.yaml`<br>`resources/inngest-expertise.yaml`<br>`resources/e2b-expertise.yaml`<br>`resources/clerk-expertise.yaml` |

## Self-Improvement Workflow

For each expertise file, follow this workflow:

### 1. Read Current Expertise

```typescript
const expertisePath = skillPath + "/resources/expertise.yaml";
const currentExpertise = await readYAML(expertisePath);

console.log(`Current version: ${currentExpertise.version}`);
console.log(`Current confidence: ${currentExpertise.confidence}`);
console.log(`Current patterns: ${currentExpertise.patterns.length}`);
```

### 2. Explore Relevant Codebase

**For convex skill:**
- Explore: `convex/` directory
- Look for: queries, mutations, actions, schema, validators

**For nextjs skill:**
- Explore: `app/`, `components/`
- Look for: Server/Client Components, routing, layouts

**For shadcn skill:**
- Explore: `components/ui/`, `app/globals.css`
- Look for: UI components, Tailwind patterns, design tokens

**For tech-stack (each domain):**
- **Vercel:** `vercel.json`, `.env.example`, deployment config
- **Inngest:** `inngest/` directory, workflows, event handlers
- **E2B:** `lib/e2b/`, sandbox utilities
- **Clerk:** `middleware.ts`, `app/layout.tsx`, Clerk providers

### 3. Validate Existing Patterns

For each pattern in current expertise:

```typescript
for (const pattern of currentExpertise.patterns) {
  // Search codebase for pattern occurrences
  const occurrences = await searchPattern(pattern.pattern);

  if (occurrences.length >= 5) {
    pattern.confidence = "high";
  } else if (occurrences.length >= 3) {
    pattern.confidence = "medium";
  } else if (occurrences.length >= 1) {
    pattern.confidence = "low";
  } else {
    // Pattern not found - mark for removal
    pattern.obsolete = true;
  }

  // Update evidence with current file locations
  pattern.evidence = occurrences.map(o => `${o.file}:${o.line}`).join(", ");
}
```

### 4. Discover New Patterns

```typescript
// Look for repeated patterns (3+ occurrences)
const candidatePatterns = await findRepeatedPatterns();

for (const candidate of candidatePatterns) {
  if (candidate.occurrences >= 3 && !existsInExpertise(candidate)) {
    // Add new pattern
    newPatterns.push({
      pattern: candidate.description,
      confidence: candidate.occurrences >= 5 ? "high" : "medium",
      evidence: candidate.files.join(", "),
      learned_from: "self-improve",
      importance: assessImportance(candidate),
    });
  }
}
```

### 5. Update Expertise File

```typescript
// Remove obsolete patterns
updatedPatterns = currentExpertise.patterns.filter(p => !p.obsolete);

// Add new patterns
updatedPatterns.push(...newPatterns);

// Increment version
const newVersion = incrementVersion(
  currentExpertise.version,
  newPatterns.length > 0 ? "MINOR" : "PATCH"
);

// Add evolution log
const evolutionEntry = {
  date: new Date().toISOString().split('T')[0],
  change: `Validated ${validatedCount} patterns, added ${newPatterns.length} new patterns`,
  confidence_before: currentExpertise.confidence,
  confidence_after: calculateConfidence(updatedPatterns),
  trigger: "manual sync",
};

// Write updated expertise
await writeYAML(expertisePath, {
  ...currentExpertise,
  version: newVersion,
  confidence: evolutionEntry.confidence_after,
  patterns: updatedPatterns,
  evolution_log: [...currentExpertise.evolution_log, evolutionEntry],
  last_updated: new Date().toISOString(),
});
```

### 6. Report Summary

```markdown
## Syncing {skill-name}...

### Exploration
- Found: {N} relevant files
- New files: {N} (file1.ts, file2.ts)
- Modified: {N} files since last sync

### Pattern Validation
- ✅ "Pattern name" - VALIDATED (5 occurrences → high confidence)
- ✅ "Pattern name" - VALIDATED (3 occurrences → medium confidence)
- ⚠️  "Pattern name" - REMOVED (not found in 2+ runs)

### New Discoveries
- 🆕 "New pattern 1" (5 occurrences → high confidence)
- 🆕 "New pattern 2" (3 occurrences → medium confidence)

### Updates
- **Patterns added:** {N}
- **Patterns updated:** {N}
- **Patterns removed:** {N}
- **Confidence increased:** {N} patterns
- **Version:** {old} → {new}

### Evolution
- **Before:** {confidence} confidence
- **After:** {confidence} confidence
- **Reasoning:** {explanation}

✅ {skill-name} synchronized
```

## Example Output

### Single Skill Sync

```markdown
## Syncing convex skill...

### Exploration
- Found: 18 Convex files (queries, mutations, actions)
- New files: 1 (convex/webhooks.ts)
- Modified: 2 files since last sync

### Pattern Validation
- ✅ "userId filtering in all queries" - VALIDATED (18 occurrences → high confidence)
- ✅ "Date.now() for timestamps" - VALIDATED (12 occurrences → high confidence)
- ✅ "Admin role checks" - VALIDATED (5 occurrences → high confidence)
- ⚠️  "Use ctx.storage.getUrl()" - CONFIDENCE LOWERED (1 occurrence → low confidence)

### New Discoveries
- 🆕 "Webhook validation pattern" (3 occurrences → medium confidence)
- 🆕 "Error message format: 'Failed to...'" (8 occurrences → high confidence)

### Updates
- **Patterns added:** 2
- **Patterns updated:** 4
- **Patterns removed:** 0
- **Confidence increased:** 2 patterns
- **Version:** 0.6.0 → 0.7.0

### Evolution
- **Before:** high confidence (37 conventions validated)
- **After:** high confidence (39 conventions validated)
- **Reasoning:** New patterns discovered from webhook integration

✅ convex skill synchronized
```

### Tech-Stack Sync (All 4 Domains)

```markdown
## Syncing tech-stack skill (4 domains)...

### Vercel (vercel-expertise.yaml)
- Patterns validated: 16
- Patterns added: 1 (new security header)
- Version: 0.5.0 → 0.5.1
- Confidence: high → high

### Inngest (inngest-expertise.yaml)
- Patterns validated: 8
- Patterns added: 0
- Version: 0.2.0 → 0.2.0 (no changes)
- Confidence: high → high

### E2B (e2b-expertise.yaml)
- Patterns validated: 5
- Patterns added: 2 (new timeout patterns)
- Version: 0.2.0 → 0.3.0
- Confidence: medium → high

### Clerk (clerk-expertise.yaml)
- Patterns validated: 6
- Patterns added: 1 (middleware pattern)
- Version: 0.2.0 → 0.3.0
- Confidence: high → high

---

**Summary:**
- Total patterns validated: 35
- Total patterns added: 4
- Domains improved: 3/4
- Average confidence: high

✅ tech-stack synchronized (all 4 domains)
```

## Agent Reminder Integration

After fixing errors, agents will remind you to sync:

```markdown
✅ Error fixed: Missing userId filter in buildLogs query

💡 **Consider running:** `/sync-skills convex`

This fix introduces a pattern that should be documented in convex expertise:
- Pattern: "Always filter queries by userId for security"
- Evidence: convex/buildLogs.ts:23-26
- Importance: Critical (security)

Running sync will:
1. Validate this pattern against all Convex files
2. Increase confidence if found 3+ times
3. Add to common_issues if recurring
4. Update expertise for future answers
```

## When Agents Should Remind

Agents suggest sync when:

✅ Fixed 3+ occurrences of same error
✅ Discovered new architectural pattern
✅ Implemented workaround worth documenting
✅ Changed core conventions

Agents DON'T suggest sync for:
❌ Single-line fixes
❌ Trivial changes
❌ Experimental code
❌ Temporary workarounds

## Validation Rules

**Validation Rules:**

**Add Pattern:**
- 3+ occurrences in codebase
- Consistent across files
- Significant (not trivial)

**Update Pattern:**
- More evidence found (increase confidence)
- Exceptions discovered (add context)
- Evidence refined (better file paths)

**Remove Pattern:**
- Not found in 2+ self-improve runs
- Contradicted by current code
- Obsolete (no longer relevant)

**Confidence Levels:**
- **High:** 5+ validated occurrences
- **Medium:** 3-4 validated occurrences
- **Low:** 1-2 validated occurrences

**Version Bumps:**
- **PATCH (0.1.0 → 0.1.1):** Minor updates, confidence adjustments
- **MINOR (0.1.0 → 0.2.0):** New patterns added, significant updates
- **MAJOR (0.9.0 → 1.0.0):** Expertise mature, high confidence across all patterns

## Time Estimates

**Single skill:** 30-60 seconds
- File exploration
- Pattern validation
- Expertise update

**Tech-stack:** 1-2 minutes
- 4 expertise files × 30 seconds each
- Sequential validation

**All skills:** 2-4 minutes
- 3 individual + 4 tech-stack files
- Sequential execution

## Verification

After sync, verify changes:

```bash
# View updated expertise
Read: .claude/skills/convex/resources/expertise.yaml

# Check version increment
# Should see: version incremented, timestamp updated

# Check evolution log
# Should have new entry with date and changes

# Test with question
/convex "How do I filter queries by userId?"
# Should give answer with updated confidence
```

## Troubleshooting

### Issue: Skill not found

```
Skill 'database' not found.
Available: convex, nextjs, shadcn, tech-stack, all
```

**Solution:** Use correct skill name from available list

### Issue: No changes after sync

```
⚠️ No significant changes detected
- All patterns still valid
- No new patterns found (threshold: 3+ occurrences)
- Confidence levels unchanged
```

**Reason:** Codebase hasn't changed significantly since last sync
**Action:** This is normal! Not every sync needs changes.

### Issue: YAML syntax error

```
❌ Error updating expertise: Invalid YAML syntax
```

**Solution:**
1. Read expertise file to see issue
2. Fix syntax manually or restore from git
3. Re-run sync

## Best Practices

**DO:**
✅ Run after significant changes (agent will remind)
✅ Run before asking questions (for freshest answers)
✅ Review changes in expertise files
✅ Commit updated expertise files
✅ Use "all" after major refactoring

**DON'T:**
❌ Run after every commit (too frequent)
❌ Run during active development (wait for stable)
❌ Ignore sync reminders from agents
❌ Skip committing updated expertise
❌ Run when build is broken

## Related Commands

- `/convex [question]` - Ask Convex questions (uses current expertise)
- `/nextjs [question]` - Ask Next.js questions (uses current expertise)
- `/shadcn [question]` - Ask shadcn questions (uses current expertise)
- `/tech-stack [question]` - Ask infrastructure questions (uses current expertise)

Run sync before asking if you suspect expertise is stale!

## Success Metrics

A successful sync should:
- [ ] Complete without errors
- [ ] Increment version (or keep same if no changes)
- [ ] Update timestamp
- [ ] Add evolution log entry
- [ ] Validate existing patterns
- [ ] Discover insights if codebase changed
- [ ] Maintain or increase confidence
- [ ] Take < 2 minutes

## Notes

- Skills are the evolution of the expert system
- Regular syncing keeps expertise accurate
- Expertise evolves with your codebase
- Patterns validated 5+ times reach high confidence
- Obsolete patterns are automatically removed
- Each sync makes future answers better
- Agent reminders help you know when to sync
