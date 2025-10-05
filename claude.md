# Development Guidelines for Claude

## 🎯 Core Principles

### 1. Commit Discipline
**Rule:** Commit after every successful result or completed task.
- One feature = One commit
- Descriptive commit messages
- No batching multiple changes

### 2. Code Implementation Philosophy
**Rule:** Don't overthink. Ask when confused.
- If stuck on implementation → Ask for help
- User provides solutions → Follow them
- User's approach seems wrong → Politely suggest corrections
- **Never spend time guessing** → Just ask

### 3. Brainstorm-First Approach
**Rule:** Think before coding. Always.
```
✅ Discuss approach → Get approval → Code
❌ Code first → Show user → Refactor
```
- Verbalize your thinking
- Explain the plan
- Wait for confirmation
- Then implement

### 4. Zero Assumptions Policy
**Rule:** When in doubt, ask. Every. Single. Time.
- Missing requirements? → Ask
- Unclear specification? → Ask
- Design decision needed? → Ask
- Implementation detail? → Ask

**Assume nothing. Clarify everything.**

### 5. Strict Scope Control
**Rule:** Implement ONLY what was requested.

**Scenario:**
- User asks: "Implement feature A"
- You think: "B, C, D would be nice too!"
- **Your action:** Ask once (expect "no"), then focus on A

**Anti-pattern:**
```
❌ "I implemented A, and also added B, C, D for convenience"
✅ "I implemented A. Should I also add B, C, D?" → [Probably: "No, just A"]
```

## 🔄 Standard Workflow

```mermaid
Request → Brainstorm → Ask Clarifications → Get Approval → Implement → Test → Commit
```

## 💬 Communication Guidelines

| Do | Don't |
|---|---|
| ✅ Ask direct questions | ❌ Make educated guesses |
| ✅ State uncertainties clearly | ❌ Hide confusion |
| ✅ Suggest alternatives when asked | ❌ Assume alternatives are wanted |
| ✅ Focus on the task | ❌ Add "helpful" extras |
| ✅ Be concise | ❌ Over-explain |

## 📝 Quick Reference

**When confused:** Ask, don't assume
**Before coding:** Brainstorm and discuss
**After feature:** Commit immediately
**Scope creep:** Ask first (expect "no")
**User's solution:** Follow it (correct if wrong)

---

## 🔧 Project-Specific Rules

### File Naming Conventions
- **All files:** `snake_case` naming
- **Prompts:** Store in `prompts/` folder, use `.md` extension
- **Tests:** Store in `tests/` folder, prefix with `test_`

### Testing Requirements
- Create dedicated test files for features
- Use **actual API calls** (not mocks) for integration tests
- Test files should be standalone and runnable

### MCP Tool Preferences

**Use Exa MCP when:**
- ✅ Need quick code examples
- ✅ Looking for package versions
- ✅ Initial research/discovery
- ✅ No time for indexing

**Use Nia MCP when:**
- ✅ Deep documentation analysis needed
- ✅ Building persistent knowledge base
- ✅ Complex codebase understanding
- ✅ Will search same docs repeatedly

**Best workflow:** Exa (quick scan) → Nia (index if valuable) → Deep search with Nia

### Folder Structure
```
prompts/          # System prompts, configs (.md files)
tests/            # Test files (test_*.py)
├── test_*.py     # Actual API-based tests
```
