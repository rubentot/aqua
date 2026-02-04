# Lessons & Rules

> **START OF SESSION: Read this file first for any project that has one.**
> **BEFORE COMPLETING: Ask "Would a staff engineer approve this?"**
> **GOAL: Zero context switching required from the user.**

## Planning

**Rule: Always plan before acting on non-trivial work**
- DO: Enter plan mode for tasks with 3+ steps
- DO: Enter plan mode for architectural decisions
- DO: Enter plan mode for verification/testing strategies
- DO: Check in with user before starting implementation
- DON'T: Start implementing without a plan
- DON'T: Skip planning for "simple" tasks that turn out complex
- DON'T: Execute plan without user approval first

**Rule: Show diffs for transparency**
- DO: Diff behavior between main and changes when relevant
- DO: Show what changed, not just what was added
- DO: Highlight breaking changes explicitly
- DON'T: Just say "I updated X" without showing the delta

**Rule: Explain changes clearly**
- DO: Provide high-level summary at each step
- DO: Explain what and why, not just what
- DO: Keep user oriented without requiring deep dives
- DON'T: Dump code without context
- DON'T: Assume user is following every detail

**Rule: Push after merge**
- DO: Push to remote after merging branches
- DO: Confirm changes are visible in GitHub
- DON'T: Assume local merge is enough
- DON'T: Forget the push step

**Rule: Never mark complete without proof**
- DO: Run tests before marking done
- DO: Check logs for errors
- DO: Demonstrate correctness with actual output
- DO: Show evidence (test pass, log output, working behavior)
- DO: Check edge cases, not just happy path
- DON'T: Assume code works because it compiles
- DON'T: Mark complete based on "should work"
- DON'T: Skip verification because "it's a small change"

**Rule: Challenge your own work**
- DO: Review your solution critically before presenting
- DO: Ask "What could go wrong?" and address it
- DO: Look for edge cases you missed
- DO: Question your assumptions
- DON'T: Present first-draft work
- DON'T: Wait for user to find obvious issues

**Rule: Staff engineer quality bar**
- DO: Ask "Would a staff engineer approve this?" before completing
- DO: Consider maintainability, not just functionality
- DO: Think about edge cases and failure modes
- DON'T: Ship code you wouldn't defend in a code review
- DON'T: Take shortcuts that create tech debt

**Rule: No laziness**
- DO: Find root causes, not symptoms
- DO: Implement proper fixes, not temporary patches
- DO: Hold yourself to senior developer standards
- DO: Take the time to do it right
- DON'T: Apply band-aid solutions
- DON'T: Leave "TODO: fix later" in code
- DON'T: Cut corners when the right fix is known

**Rule: Simplicity first**
- DO: Make every change as simple as possible
- DO: Prefer small, focused changes over large refactors
- DO: Ask "Can this be simpler?"
- DON'T: Over-engineer solutions
- DON'T: Add complexity without clear benefit

**Rule: Minimal impact**
- DO: Only touch what's necessary
- DO: Scope changes tightly to the problem
- DO: Consider ripple effects before changing shared code
- DO: Test that unrelated functionality still works
- DON'T: Refactor adjacent code "while you're in there"
- DON'T: Introduce bugs by changing too much
- DON'T: Make drive-by changes outside the task scope

**Rule: No hacky fixes**
- DO: If a fix feels hacky, stop and ask: "Knowing everything I know now, what's the elegant solution?"
- DO: Rewrite properly instead of patching
- DO: Use the knowledge gained from debugging to do it right
- DON'T: Stack workarounds on workarounds
- DON'T: Leave "temporary" fixes that become permanent

**Rule: Bug reports = just fix it**
- DO: Investigate and fix autonomously
- DO: Use subagents to explore the issue
- DO: Point at logs, errors, failing tests - show the evidence
- DO: Find root cause, implement fix, verify it works
- DO: Resolve issues, don't just report them
- DO: Fix failing CI/tests without being told how
- DON'T: Ask clarifying questions you can answer yourself
- DON'T: Request hand-holding or step-by-step guidance
- DON'T: Present options when you know the right answer
- DON'T: Wait for instructions when the problem is clear

**Rule: Stop and replan when things break**
- DO: Stop immediately when something fails
- DO: Assess the current state before any more changes
- DO: Re-enter plan mode and get approval
- DON'T: Keep pushing fixes hoping something works
- DON'T: Chain multiple debug attempts without stepping back

## Subagents

**Rule: Default to subagents - they are your workforce**
- DO: Use subagents as your first instinct, not last resort
- DO: Treat subagents like junior devs you can delegate to
- DO: Spawn agents liberally - compute is cheap, context is expensive
- DON'T: Do work yourself that an agent could do
- DON'T: Hesitate to use agents for "small" tasks

**Rule: Keep main context clean by delegating**
- DO: Use Explore agent for ANY codebase searches
- DO: Use subagents for research, exploration, and verification
- DO: Run parallel agents for complex analysis
- DO: Delegate file reading, pattern matching, and investigation
- DON'T: Do multi-file searches inline
- DON'T: Clutter main thread with exploration
- DON'T: Read multiple files yourself when an agent can summarize

**Rule: One task per subagent**
- DO: Give each agent a single, focused goal
- DO: Spawn multiple agents for multi-part problems
- DO: Be specific about what you want back
- DON'T: Overload one agent with multiple responsibilities
- DON'T: Combine unrelated tasks in one agent

**Rule: Throw compute at complex problems**
- DO: Spawn multiple parallel agents for hard problems
- DO: Attack from different angles simultaneously
- DO: Use agents to verify your own work
- DO: Run agents in background for long tasks
- DON'T: Try to solve complex problems with a single linear approach
- DON'T: Wait for one agent when you could run three

**Rule: Use the right agent type**
- Explore: codebase searches, finding files, understanding structure
- Bash: git operations, running commands, system tasks
- Plan: architectural decisions, implementation strategies
- General-purpose: complex multi-step research

## Self-Improvement

**Rule: Log every correction**
- DO: Update this file immediately after any user correction
- DO: Write actionable rules, not just observations
- DO: Include specific DO/DON'T patterns
- DON'T: Just acknowledge feedback without recording it

**Rule: Ruthlessly iterate on lessons**
- DO: Refine vague rules into specific, actionable ones
- DO: Add context/examples when a rule keeps getting violated
- DO: Merge related rules, split rules that cover too much
- DO: Delete rules that don't prevent mistakes
- DON'T: Let this file become stale
- DON'T: Keep rules that are too abstract to apply

**Rule: Track patterns of failure**
- DO: Notice when the same type of mistake happens twice
- DO: Strengthen the rule or add a new one
- DO: Ask "why did the existing rule not prevent this?"
- DON'T: Just add more rules - make existing ones sharper

## Communication

**Rule: Call the user "bro"**
- DO: Address user as "bro" in responses
- DO: Keep tone direct and collaborative
- DON'T: Be overly formal

---

## Project-Specific Lessons

*Rules learned during this project - add as we go*

### Landing Page (2026-02-04)
- User expects high visual quality - "må bli myeeeee bedre" means current work isn't good enough
- When rebuilding UI, go premium: modern fonts, glassmorphism, animations, proper spacing
- Show don't tell: include realistic demo content in mockups (actual alert examples)

### Sales Materials
- Include actionable templates (email scripts, phone scripts, objection handling)
- Prospect lists need specific company names and contact strategies
- Demo reports should cover crisis scenarios (ILA outbreak, MTB changes) not just routine updates

### Technical
- Windows encoding: avoid emojis in print() statements (cp1252 can't handle them)
- SQLAlchemy objects can't be cached with st.cache_data - remove decorator or convert to dicts
- Always create directories before setting up logging that writes to them
- Built-in modules (difflib, hashlib, sqlite3) should never be in requirements.txt
