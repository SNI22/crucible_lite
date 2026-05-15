---
name: framework-restructure-2026-05-15
description: "Crucible was split into a framework (~/crucible/core) and per-project workspaces on 2026-05-15. cloth-grasp lives at ~/crucible/cloth-grasp and is on the cloth_grasp branch of crucible_lite. Next step is /session 0."
metadata:
  type: project
---

On 2026-05-15 the old monolithic `crucible-lite` repo was split into a reusable
framework (`~/crucible/core/`, installed via `pipx install -e`) and per-project
workspaces. This cloth-grasp project was renamed from `~/Documents/crucible-lite/`
to `~/crucible/cloth-grasp/`. Its GitHub remote is `SNI22/crucible_lite` and
its active branch is `cloth_grasp` (NOT `main` — `main` is the upstream
template state).

**Why:** The mono-repo couldn't host multiple projects without each one
hand-customising or stripping the framework. The framework/instance split lets
`crucible init` bootstrap new project workspaces from shared templates.

**How to apply:** When working on cloth-grasp, `cd ~/crucible/cloth-grasp` and
work on the `cloth_grasp` branch. Project state is at end of Spec Gate; **next
step is `/session 0`** (HIL Toolchain Lock). Detailed session digest:
`docs/session_logs/2026-05-15.md`. Two outstanding pre-Stage-0 items: DAQ
per-channel curve fit form (Bill required) and DAQ capacity for 5 incoming
A301-25 sensors. Related: [[project-comparison-framing]], [[daq-capacity-pending]].
