Protocol for adding a new agent to the Crucible framework.

This is a human-executed checklist, not an agent dispatch.
Adding an agent changes what the system can do autonomously — that is an Article II decision.
No agent can add another agent. You do this. Work through the steps in order.

Usage: /gen-new-agent <agent name>

---

## Why human, not agent

An agent that adds agents is self-modifying governance. The system would be
able to expand its own autonomous authority without a human decision.
Article II is explicit: "An agent executes. A human decides."
Agent creation is a decision, not an execution.

---

## Step 1 — Constitutional grounding

Before writing a line of the agent file, answer these questions. If you cannot
answer them, the agent is not ready to be written.

**Q1 — Which branch does this agent belong to?**
  Bureaucracy   — executes established procedures autonomously (Bureaucracy Standing Order)
  Judiciary     — argues positions, rules, or records decisions (Judicial Branch)
  Legislature   — proposes changes, drafts Bills (Legislative Process)

  Most new agents are Bureaucracy. If you are adding a Judiciary or Legislature
  agent, you need a /hear to ratify its constitutional role.

**Q2 — What is its Standing Order class?**
  Name the class from CONSTITUTION.md Bureaucracy section, or propose a new one.
  If new: add the class to CONSTITUTION.md before writing the agent.
  A Bureaucracy agent without a named Standing Order class has no constitutional authority.

**Q3 — Which Articles and Amendments govern it?**
  List them. At minimum: Article I or Article II (usually both).
  List any Amendment that constrains what it can do autonomously.
  List any Amendment that mandates it be invoked (e.g. Amendment 6 mandates signal plots).

**Q4 — What does it do that no existing agent does?**
  Check the current agent roster in `.claude/agents/`. If an existing agent can be
  extended, extend it — don't create a new one. Duplicating scope creates constitutional
  ambiguity about which agent governs a Standing Order.

**Q5 — What does it explicitly NOT do?**
  Write this before the "What you do" section. Constraints are as important as capabilities.
  The "What you do NOT do" section is what prevents scope creep at runtime.

---

## Step 2 — Write the agent file

Create `.claude/agents/<agent-name>.md` using this exact structure:

```markdown
---
name: <agent-name>
description: "<one sentence — triggers for USE THIS AGENT WHEN, and what it does>"
tools: <comma-separated: Bash, Read, Write, Edit, Glob, Grep, Agent — only what it needs>
model: <haiku for read-only/reporting | sonnet for reasoning/proposing | opus for adversarial>
color: <pick one not already used by a similar-scope agent>
---

You are a [Bureaucracy civil servant / Judicial Branch member] under the Crucible
Constitutional Governance system (CONSTITUTION.md) operating under the
**[Standing Order class name] Standing Order**.

[One sentence on what you do. One sentence on what you do NOT do.]

---

## Constitutional Basis

| Rule | How it governs your work |
|---|---|
| Article I / II | [how] |
| Amendment N   | [how] |

---

## When you are called

You are invoked by:
- [command or agent that calls you] — [why]

---

## What you read

[ordered list of RAG sources, most important first]

---

## [Your core procedure section]

[checklist or step sequence]

---

## What you do NOT do

- [constraint 1]
- [constraint 2]

## Escalation Triggers

Stop and report to the human if:
- [condition]
```

Model selection guide:
  haiku  — read-only agents, reporting agents, sub-agents called many times per session
  sonnet — reasoning agents, advisory agents, orchestrators
  opus   — adversarial agents (attorneys), agents that must argue against themselves

Tool selection guide — only grant what is needed:
  Read, Glob, Grep — for any agent that reads files
  Bash            — only if it runs shell commands (simulation, git, serial port)
  Write, Edit     — only if it writes files (most agents should NOT have these)
  Agent           — only if it orchestrates sub-agents

---

## Step 3 — Define the skill (command or embedded)

Decide: does this agent need its own `/command`, or does it live inside an existing flow?

**Needs its own command if:**
- A human engineer would invoke it directly and on-demand
- It has optional focus arguments (like /code-review, /sw-advisor)
- It produces output the human reviews before deciding next steps

**Lives inside an existing flow if:**
- It is always invoked by another agent (like uart-reader, called by simulator-operator)
- It runs automatically at a defined trigger point (like police at session start)
- It has no optional arguments — it always does the same thing

**If it needs its own command**, create `.claude/commands/<agent-name>.md`:

```markdown
Invoke the <agent-name> agent to [what it does].

Usage: /<command-name> [focus]

Focus (optional):
  [focus options if any]

Constitutional grounding:
  [Amendment N] — [why relevant]

Reads before acting:
  [list of RAG sources]

Now invoke the <agent-name> agent with "$ARGUMENTS".
[Guard clause for missing Amendment 1 or empty evidence base if applicable]
```

**If it lives inside an existing flow**, skip to Step 4 and wire it there.

---

## Step 4 — Update related agents

For every agent that invokes or is invoked by the new agent, add a reciprocal
reference. Check these specifically:

**judicial-clerk.md**
Add the new agent to the roster check list (both the read list and the COURTROOM READY
confirmation message).

**Orchestrators that call this agent** (if any)
Add the new agent to the orchestrator's "Agent Orchestration" section.

**Agents this agent calls** (if any)
Add "You are invoked by: <new-agent>" to each sub-agent's "When you are called" section.

**session.md commands block**
If the agent has its own command, add it to the appropriate section
(core workflow or housekeeping) in the session header.

**hear.md Step 1**
If the agent is a hearing participant (not just a Bureaucracy agent), add it to
the judicial-clerk roster check that Step 1 triggers.

---

## Step 5 — Update associated documents

**docs/governance/amendments.md**
If you added a new Standing Order class: add it to the Bureaucracy section
of CONSTITUTION.md and note the new agent in amendments.md under a new amendment
if the scope warrants governance documentation.

**If a new Standing Order class was added to CONSTITUTION.md:**
Run `agent-updater` with "new standing order class [name] added" to check
whether existing agents need to acknowledge the new class.

**If the new agent enforces any Amendment:**
Add that enforcement relationship to the amendment's text:
  "Enforced by: <agent-name> agent"

---

## Step 6 — Verify with gov-audit

After completing Steps 1–5, run `/gov-audit` to confirm:
- No orphaned amendment references in the new agent
- No index gaps in amendments.md
- Judicial-clerk roster is consistent

If gov-audit reports any CONFLICT or MALFORMED finding related to your new agent,
fix it before considering the agent active.

---

## Checklist

```
[ ] Q1–Q5 answered (constitutional grounding complete)
[ ] Agent file created at .claude/agents/<name>.md
[ ] Standing Order class confirmed or added to CONSTITUTION.md
[ ] Constitutional Basis table filled with real amendment numbers
[ ] RAG read order specified
[ ] "What you do NOT do" section written
[ ] Escalation triggers written
[ ] Command file created at .claude/commands/<name>.md (if direct invocation needed)
[ ] judicial-clerk.md updated (roster + COURTROOM READY message)
[ ] Orchestrators updated (if applicable)
[ ] Sub-agents updated (if applicable)
[ ] session.md commands block updated
[ ] amendments.md updated (if new Standing Order class)
[ ] /gov-audit run and clean
```
