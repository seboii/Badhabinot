# Contributing to BADHABINOT

This document defines the Git workflow, commit conventions, and CI expectations
for the BADHABINOT graduation project.

---

## Branch Strategy

| Branch | Purpose |
|---|---|
| `main` | Stable, production-candidate. Protected. No direct commits. |
| `develop` | Integration branch. Features merge here first. |
| `feature/*` | New functionality. Branch from `develop`. |
| `fix/*` | Bug fixes. Branch from `develop`. |
| `chore/*` | Tooling, CI, configuration. Branch from `develop`. |
| `docs/*` | Documentation-only changes. Branch from `develop`. |

> **Note:** The repository currently uses `master` as the stable branch.
> The convention above targets the renamed `main`. Update locally with:
> `git branch -m master main`

### Branch naming examples

```
feature/grounded-chat-history
fix/vision-service-timeout
chore/ci-split-workflows
docs/api-endpoint-reference
```

---

## Commit Message Convention

```
type(scope): short description in lowercase
```

**Types**

| Type | When to use |
|---|---|
| `feat` | New feature or behaviour |
| `fix` | Bug fix |
| `refactor` | Code restructure without behaviour change |
| `test` | Tests added or updated |
| `build` | Build system or dependency changes |
| `chore` | Tooling, CI, config, repo hygiene |
| `docs` | Documentation only |

**Scopes**

`backend`, `frontend`, `python`, `docker`, `ci`, `repo`

**Examples**

```
feat(backend): add grounded chat endpoint with conversation history
fix(python): handle vision service timeout with correct error code
chore(ci): split monolithic workflow into four scoped files
docs(repo): add branch and commit convention guide
test(backend): add unit tests for AnalysisOrchestratorService
build(frontend): upgrade vite to v8 and align tsconfig
refactor(backend): move exceptions to common.exception package
```

**Rules**
- Keep the subject line under 72 characters
- Use the imperative mood: "add" not "added", "fix" not "fixes"
- No period at the end of the subject line
- Leave the body blank for small changes; use it to explain *why* for non-obvious ones

---

## Opening a Pull Request

1. Branch from `develop` (or `main` for hotfixes)
2. Commit with the convention above
3. Open a PR targeting `develop`
4. Fill in the PR template completely
5. Wait for all CI checks to go green before requesting review

---

## CI Checks

| Workflow | Trigger | What it validates |
|---|---|---|
| `ci-backend.yml` | push/PR → `main`, `develop` | `mvn verify`: compile, unit tests, JaCoCo ≥ 20% line coverage |
| `ci-python.yml` | push/PR → `main`, `develop` | `pytest` for both `ai-service` and `vision-service` with coverage |
| `ci-frontend.yml` | push/PR → `main`, `develop` | TypeScript type check + Vite production build |
| `ci-docker.yml` | push → `main`, `develop` | Compose config validation + image build for all services |

All checks must pass before a PR can be merged.
