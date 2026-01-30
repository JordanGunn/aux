# Task

Analyze authentication and authorization implementation across the entire codebase.

## Rationale

This is a worst-case scenario for agents: auth touches backend middleware, deployment configs, Helm charts, and IaC. Architectural roots are scattered across 6+ directories, each with dozens of sub-directories, and hundreds of files.

**No single directory tells the whole story.**
