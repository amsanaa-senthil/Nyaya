# DevOps and Security Checklist

This document maps the project to grading criteria for deployment, CI/CD, and secure practices.

## 1) Cloud Deployment (Minimum Requirement)

Current deployment path:
- Containerized service via [Dockerfile](Dockerfile)
- Render blueprint via [render.yaml](render.yaml)
- Production deployment automation via [.github/workflows/deploy.yml](.github/workflows/deploy.yml)

How deployment works:
1. Push to `main`
2. GitHub Actions builds and pushes image to GHCR (`ghcr.io/<owner>/nyaya`)
3. Workflow triggers Render deploy hook when `RENDER_DEPLOY_HOOK_URL` secret is set

Required GitHub secrets:
- `RENDER_DEPLOY_HOOK_URL`

## 2) Functional CI/CD Pipeline (Build, Test, Deploy)

### CI (Build + Test)
- Workflow: [.github/workflows/ci.yml](.github/workflows/ci.yml)
- Test stage:
  - Python install
  - flake8 checks
  - pytest suite
- Build stage:
  - Docker build validation (`docker/build-push-action` with `push: false`)

### Quality/Security Checks
- Workflow: [.github/workflows/quality.yml](.github/workflows/quality.yml)
- Includes:
  - Bandit scan
  - safety dependency checks
  - pylint report

### CD (Deploy)
- Workflow: [.github/workflows/deploy.yml](.github/workflows/deploy.yml)
- Deploy strategy:
  - Build and push production image to GHCR
  - Trigger cloud deploy via Render webhook

## 3) Branch Strategy and Automation Practices

Recommended branch strategy:
- `main`: production-ready only
- `development`: integration branch
- `feature/*`: short-lived feature branches
- `hotfix/*`: emergency fixes for production

Recommended pull request policy:
1. PR into `development` or `main`
2. Require CI success (ci + quality)
3. Minimum one reviewer
4. Squash merge with descriptive commit title

## 4) Authentication, Authorization, and Validation

### Authentication
- API key protection on protected endpoints in [app.py](app.py)
- Header: `X-API-Key` (`NYAYA_API_KEY` env)
- Admin key for sensitive governance endpoints:
  - Header: `X-Admin-Key` (`NYAYA_ADMIN_API_KEY` env)

### Authorization controls
- Conversation ownership checks and permission gates in [collaboration_store.py](collaboration_store.py)
- Sensitive endpoints enforce both API and admin keys:
  - `/collaboration/audit`
  - `/governance/purge`

### Validation and abuse controls
- Query validation and sanitization in [app.py](app.py)
- Request rate limiting in [app.py](app.py)
- Safety/guardrail checks in [agent/guardrails.py](agent/guardrails.py)

## 5) Risk Identification and Mitigation Summary

Identified risks and mitigations:
1. Unauthorized API access
- Mitigation: `X-API-Key`, optional strict enforcement in production

2. Privileged governance misuse
- Mitigation: separate `X-Admin-Key` control for audit/purge operations

3. Prompt abuse / harmful requests
- Mitigation: safety filter + refusal behavior in guardrails

4. Data leakage from permissive browser origins
- Mitigation: configurable CORS origins via `CORS_ORIGINS`

5. CI instability from external model/network dependencies
- Mitigation: deterministic tests, lazy model loading, and workflow diagnostics

6. Transport/browser security hardening gaps
- Mitigation: security headers (`X-Frame-Options`, `X-Content-Type-Options`, `HSTS`, etc.)

## 6) Production Environment Baseline

Set these in cloud environment variables:
- `NYAYA_API_KEY`
- `NYAYA_ADMIN_API_KEY`
- `CORS_ORIGINS`
- `QDRANT_HOST`, `QDRANT_API_KEY`, `QDRANT_COLLECTION`
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
- LLM credentials (Azure or Gemini)

Do not commit `.env` to git.
