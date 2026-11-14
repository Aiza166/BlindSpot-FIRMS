# ECC attribution

Parts of this `.claude/` folder are adapted from **ECC** by Affaan Mustafa:
https://github.com/affaan-m/ECC, MIT License, Copyright (c) 2026 Affaan Mustafa.

The MIT License requires that the copyright and permission notice be kept with copies:

> Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions: The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software. THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.

Files were copied as text only. No ECC scripts, installer, hooks or npm packages were run or copied.
Each copied file now ends with a one-line attribution footer.

## Files copied

| File here | ECC source | Changes |
|---|---|---|
| `agents/planner.md` | `agents/planner.md` | Stripe example success criterion "80%+ coverage" changed to "billing logic covered by tests" |
| `agents/architect.md` | `agents/architect.md` | None |
| `agents/python-reviewer.md` | `agents/python-reviewer.md` | None |
| `agents/typescript-reviewer.md` | `agents/typescript-reviewer.md` | Removed reference to the `/react-review` command (not installed) |
| `agents/react-reviewer.md` | `agents/react-reviewer.md` | Description "MUST BE USED for React projects" changed to "use before merging web changes"; "Related" list cut to what is installed here |
| `agents/fastapi-reviewer.md` | `agents/fastapi-reviewer.md` | None |
| `agents/build-error-resolver.md` | `agents/build-error-resolver.md` | "Quick Recovery": scoped to `web/`, must ask before running; removed `rm -rf package-lock.json` (now `npm ci` from the existing lockfile); "add missing dependencies" now needs asking first |
| `agents/tdd-guide.md` | `agents/tdd-guide.md` | 80% coverage target replaced with "test the harmonization, calibration and validation logic; no global % target"; test commands set to `pytest` / `npm test`; pointer from the uninstalled `tdd-workflow` skill to `python-testing` |
| `commands/plan.md` | `commands/plan.md` | Removed references to commands and skills that are not installed (`/multi-plan`, `/plan-canvas`, `/prp-*`, `/plan-prd`, `/pr`, `/build-fix`); "after planning" list points at the agents and skills here |
| `commands/save-session.md` | `commands/save-session.md` | Writes to project-local `.claude/session-data/*.md` instead of global `~/.claude/session-data/*.tmp`; removed reference to ECC's `session-manager.js`; added "never write secrets into a session file" |
| `commands/resume-session.md` | `commands/resume-session.md` | Reads project-local `.claude/session-data/*.md` instead of `~/.claude/session-data/` and the legacy `~/.claude/sessions/` |
| `skills/verification-loop/SKILL.md` | `skills/verification-loop/SKILL.md` (whole dir: one file) | Build and test phases point at `web/` and `pytest`; 80% coverage gate replaced with the project coverage goal; added MAP_KEY and tracked-`.env` checks to the security phase; removed reference to the uninstalled `/verify` command |
| `skills/python-testing/SKILL.md` | `skills/python-testing/SKILL.md` (whole dir: one file) | 80%/100% coverage targets replaced with the project coverage goal and named critical paths |

## Safety review

Every file was read in full and scanned for invisible or bidirectional Unicode, HTML comments, encoded payloads, network calls, `curl | sh`, publish/push steps, and instructions to edit global settings or disable safety. None were found. The only global-state behaviour was the session commands writing to `~/.claude/`, which was changed to a project-local folder.
