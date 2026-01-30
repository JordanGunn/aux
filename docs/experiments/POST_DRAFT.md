# Experiment Draft (for Reddit Post)

## The Test Repository

To validate the value proposition, I ran a controlled experiment on a **production SaaS platform monorepo**:

| Metric | Value |
|--------|-------|
| **Source files** | ~900 files |
| **Lines of code** | ~110,000 |
| **Languages** | Go, TypeScript, Python, YAML, Bicep, Shell |
| **Disk size** | 1.6 GB |

### Architectural Components

| Layer | Description |
|-------|-------------|
| **Backend** | Go microservices (API server, migrations, backup, client SDK) |
| **Frontend** | TypeScript/React UI |
| **Infrastructure** | Helm charts, Bicep IaC, Kubernetes manifests |
| **Containers** | 18 container definitions (compute workloads, identity providers, proxies) |
| **CI/CD** | GitLab CI, GitHub Actions |

The codebase spans **multiple architectural boundaries**:

- Authentication touches backend, middleware, deployment configs, and IaC
- A single feature like OAuth2 has files in 6+ directories
- Cross-cutting concerns are scattered across layers

This is exactly the environment where agents struggle: too many files to read naively, too much context to hold, too easy to tunnel-vision on one directory.

---

## The Experiment

**Task:** Analyze the authentication and authorization implementation across the codebase.

**Setup:**

- **Session A:** AUx skills disabled — agent uses native tools only
- **Session B:** AUx skills enabled — agent has access to grep, find, diff, ls skills

Same prompt, same model, same codebase.

---

## Results

_To be filled after running the experiment._

| Metric | Without Skills | With Skills |
|--------|----------------|-------------|
| Tokens consumed | | |
| Tool calls | | |
| Files read | | |
| Time to completion | | |
| Cross-cutting coverage | | |

---

## Why This Matters

In a 110k-line polyglot monorepo:

- **Without skills:** Agent reads files one by one, greps manually, potentially misses auth code in deployment configs or IaC
- **With skills:** Agent establishes the reasoning surface first (what exists?), then reads only what's relevant

The difference isn't subtle. Surface discovery before deep reading is fundamentally better architecture for agentic code understanding.
