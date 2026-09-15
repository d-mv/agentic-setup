# Global Agent Instructions

## MANDATORY STARTUP ROUTINE
1. **Check for Project Identity**: Immediately upon start, check the current directory for any Markdown files in root and `/docs`.
2. **Fetch Project Context**: README.md, and docs. Can ask user Confluence and/or Jira link.
3. **User Briefing**: Present a concise summary of the **pending tasks** to the user as the very first action. Do not wait for a user prompt to show this.
4. **New Projects**: Add/edit README.mv and keep it up to date.
5. Check project memory in `~/.agents/projects/:name`

## SECRETS & CREDENTIAL HANDLING
- **Never interpolate secrets into remote command strings.** Piping a password/token via `PASS='$SECRET'; echo "$PASS" | sudo -S ...` (or any inline shell variable built from a secret) puts the plaintext value into that process's argv, which `ps`/`pgrep` on the remote host will show to any other local user for the life of the process — and to you, the next time you inspect processes.
- **Prefer scoped `NOPASSWD` sudo** for known automation commands (e.g. `docker compose`, `caddy reload`, `rsync`/`tee` under a specific app directory) over passing a sudo password at all. If a password truly must be sent, use `sudo -S` fed via a piped file/stdin redirect that never appears as a literal in the command string, not a `VAR='<secret>'` prefix.
- **Never run `ps`, `pgrep -f`, `history`, or similar full-command-line listings** on a host/process where a secret may be embedded in argv, unless you first filter it out (e.g. `ps -o pid,etime,comm=` instead of `-o cmd`/`-o args`, or pipe through a redaction filter). Assume any such output you capture becomes part of the durable conversation transcript.
- **If a secret is ever captured into tool output or a transcript, treat it as compromised** — tell the user immediately and recommend rotating it. Don't try to scrub it after the fact; flag and move on.

## DEVELOPMENT LOOP
For handling tasks follow development loop, described in `~/.agents/development_loop.md`.

## PROJECT MEMORY
After any session where you touch code in a project, create or update a project memory file at `~/.agents/projects/<slug>/memory/project_structure.md` covering:
- Key component/file paths and what each owns (state, routing, API calls, etc.)
- State management patterns (stores, local refs, composables)
- Any libraries or conventions that are non-obvious from the file names alone

This lets future sessions skip the codebase exploration step entirely. Update the entry whenever you discover something new or something has changed.

Template is in `~/.agents/templates/project_structure.md`

## SESSION HYGIENE
- **Terse / Concise Mode Early**: At the start of any session involving debugging across multiple files, architecture decisions, or expected long duration — switch to concise/terse output immediately. Do not wait until the session is already large and token pressure has built up.
- **Proactive Compaction**: Summarize or compact context mid-session before context limits are reached (target after ~30 exchanges, or when switching from one major task to another). Do not wait for forced context compression — by then rate-limit risk is already elevated.
- **Deferred Debt Must Become Tasks**: Whenever a known limitation, workaround, or intentional tech debt is mentioned or discovered in a session — create Markdown file with tasks (or update existing) for it before the session ends. Memory notes and code comments are not substitutes; undocumented debt has no owner and no priority.

## AI COLLABORATION & DISCOVERY WORKFLOWS
- **Blindspot Pass**: Before starting unfamiliar tasks or complex features, perform a blindspot pass to surface "unknown unknowns" and guide prompt & architectural alignment.
- **Brainstorming & Prototyping**: Uncover "unknown knowns" early by creating lightweight, isolated prototypes (e.g. standalone HTML mocks or dry runs) before altering production code or backend logic.
- **Interactive Interviews**: When scope is ambiguous, interview the user one question at a time, prioritizing questions whose answers alter architecture.
- **Reference-Driven Code**: Point to exact source code, schemas, or reference implementations as authoritative guides for new code.
- **Decision-Focused Plans**: Structure implementation plans by leading with decisions most likely to change (data models, type interfaces, UX). Keep mechanical refactoring at the bottom.
- **Deviations Log (`implementation-notes.md`)**: Maintain an `implementation-notes.md` (or `.html`) file to log conservative choices made when encountering unpredicted edge cases during execution.
- **Pitches, Explainers & Quizzes**: Package major feature completions into pitch/explainer docs for review, and generate post-implementation context reports with a quiz to verify full comprehension before merging.

## LOCAL SKILLS & AGENT ROUTING
Always leverage specialized local skills when performing domain-specific tasks. Key local skills include:
- `analysis-auditor`: analyze project, audit current state & etc

### Agent Routing Table
Apply the appropriate specialist agent skill(s) automatically for every task. Use multiple agents in parallel when a task spans domains.

| Task type | Agent skill / Skill to apply |
|-----------|------------------------------|
| React/Vue/Next.js, state management, browser perf, CSS, build tooling, a11y | **frontend-agent** |
| API design, DB queries/schema, server-side logic, microservices, caching, background jobs | **backend-agent** |
| CI/CD, Docker, Kubernetes, cloud infra, Terraform/Pulumi, monitoring, secrets | **devops-agent** |
| Test strategy, coverage gaps, test pyramid, quality gates, flaky tests | **qa-agent** |
| Auth flows, user input, SQL/NoSQL queries, file uploads, secrets, OWASP, prod deploy review | **security-agent** |
| Feature scoping, user stories, acceptance criteria, PRD writing, prioritization, MVP | **product-agent** |
| User flows, navigation design, form patterns, empty/error/loading states, a11y UX, onboarding | **ux-agent** |

**Rules:**
1. Identify the domain(s) of every task before starting.
2. Load and follow the skill(s) for those domain(s) — mandatory for all matching tasks. Local skills are located under `~/.agents/skills/`.
3. Full-stack features: apply frontend-agent + backend-agent + security-agent at minimum.
4. New features: apply product-agent first to define scope, then domain agents.
5. Deployment: apply devops-agent + security-agent together alongside deployment skills.
6. Bug fixes: apply systematic-debugging first to identify the root cause, write a failing test that reproduces the bug, then fix, then qa-agent for regression coverage.
7. When multiple agents apply, synthesize their guidance — they are complementary, not competing.

## ENGINEERING STANDARDS
- **Strict Scope & Ask First**: Do NOT do things you were not explicitly asked to do. Do NOT introduce unrequested architectural changes, global catch-all solutions, or speculative workarounds without user consent. Always ask first before adding changes or introducing new patterns.
- **Strict & Explicit Component Contracts**: Explicitly declare all supported props, event interfaces, and types. Do NOT use unsafe, loose, or unvalidated catch-all solutions (such as blind `$attrs` splatting or uncontrolled fallthrough overrides). Looks at `~/.agents/contracts/component_standards.md`
- **Test-Driven Development (TDD)**: Follow a strict Red-Green-Refactor cycle for all code changes — write the failing test first, then implement.
- **Plan Deviations**: During the implementation of a plan, track and log any deviations from the original plan (e.g., architectural adjustments, edge cases discovered, scope shifts, or alternate implementations) and present a summary of these deviations to the user upon completion.
- **Bug Fix Protocol**: Once a bug is identified, write a failing test that reproduces it *before* touching any production code. Only then fix the bug and confirm the test goes green.
- **Multi-Agentic Work**: Use specialist sub-agents for complex tasks to preserve context and maximize efficiency. Apply the routing table above automatically.
- **Semantic Commits**: Use `feat:`, `fix:`, `refactor:`, `docs:`, `chore:` for all commits.
- **Version Bump On Every Change**: Every change to a package/service MUST bump its version (`package.json`, `mix.exs`, `Cargo.toml`, `deploy.toml`, or whatever the project uses as the canonical version), following SemVer `MAJOR.MINOR.PATCH`:
  - **Bug fixes / internal changes** (no API change) → bump `PATCH` (`x.x.PATCH+1`).
  - **New backward-compatible features** → bump `MINOR` (`x.MINOR+1.0`), reset `PATCH` to `0`.
  - **Breaking / incompatible changes** → bump `MAJOR` (`MAJOR+1.0.0`), reset `MINOR` and `PATCH` to `0`.
  - Once change done, version bumped - commit the change + version; never ship code changes with an unchanged version. Record it in the changelog / release notes where the project keeps one.
- **Project Lifecycle**: For every significant feature or project, follow this 15-step process tracked in local Markdown file: Purpose → Audience → Scope → Requirements → Deliverables → Metrics → Execution → Review → Devil's Advocate → Document → Ownership → Track → Iterate → Finalize → Post-launch.
- **Typecheck Before Deploy**: A passing test run is NOT sufficient proof a build will succeed. Test runners like `vitest` strip types without checking them, but the production build typechecks test files too (e.g. `vue-tsc -b`, `tsc --noEmit`). Always run the project's full typecheck locally before deploying, so type errors fail fast on your machine instead of mid-deploy in build pipelines.
- **`.env` Must Never Enter the Docker Build Context**: The repo `.dockerignore` MUST exclude `.env` and `.env.*` (keep `!.env.example`). A stale `.env` copied into the image build context can silently shadow or diverge from `build_args`. Build args are the only supported source for build-time vars in a deployed image. The `deploy` skill's rsync steps must also `--exclude=.env` so local env never lands in staging or the app context.
- **Verify the Built Artifact, Not Just the Deploy Exit Code**: A green `docker compose build` / `up -d` does not prove the right config shipped. After deploy, fetch the actual served bundle (e.g. `curl .../assets/index-*.js | grep` for the expected key/URL) and hit a live endpoint that exercises the credential (e.g. Supabase `/auth/v1/health` or `/auth/v1/otp` — anything but `Unregistered API key` / `Invalid API key`). Only then is the deploy done.
- **Supabase CLI (EXPLICIT)**: Always target the project explicitly.
  - Use `bunx supabase ... --project-ref ...`.
  - For direct queries: `bunx supabase db query --linked "SQL"`.
  - NEVER run bare supabase commands that might target a local or default environment.

## TECH STACK & ARCHITECTURE PREFERENCES
- **Heavy-Duty Backend & Parallel Tasks**: Prefer Elixir w/ Phoenix.
- **Light / Moderate Backend**: Prefer TypeScript + Elysia.
- **CLI Development**: Prefer TypeScript.
- **JS/TS Tooling & Runtime**:
  - Prefer TypeScript over JavaScript across all projects.
  - Prefer `bun` with `oxlint` / `oxfmt`.
- **Latest Versions**: Always stick to the latest versions across all programming languages, runtimes, frameworks, and libraries.
- **Web UI**: Prefer Vue.
- **Styling & CSS**: Prefer use of Tailwind v4+.
- **Desktop Apps**: Prefer Electron + Vue (or Tauri + Vue for resource-heavy / high-performance requirements).
- **Architecture**: Prefer stateless, serverless apps whenever applicable.
