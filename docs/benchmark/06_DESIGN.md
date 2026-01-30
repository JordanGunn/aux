# Experiment Design

## Methodology

Each experiment runs the **same prompt** in two sessions:

| Session | Configuration                                                             |
|---------|---------------------------------------------------------------------------|
| **A**   | Native IDE tools only: built-in grep, file reading                        |
| **B**   | AUx skills enabled: structured grep/find/diff/ls with explicit parameters |

All other factors held constant. Metrics captured:

- tokens used
- tool calls
- files read
- coverage quality

## Test Codebase

The subject is a **production SaaS monorepo** hosting a distributed cloud-computing platform:

| Metric         | Value                                                  |
|----------------|--------------------------------------------------------|
| Source files   | ~900                                                   |
| Lines of code  | ~110,000                                               |
| Disk size      | 1.6 GB                                                 |
| Languages      | Go, TypeScript, Python, YAML, Bicep, Shell, Dockerfile |
| Frameworks     | Kubernetes, Helm, ArgoCD, React, Gin, GraphQL          |
| Cloud          | Azure (Bicep IaC)                                      |

This represents a **high-complexity, polyglot environment** typical of enterprise platform teams.

## Task: Cross-Cutting Analysis

The prompt asks the agent to inventory authentication and authorization code across the entire codebase.

This is a **worst-case scenario** for agents:

- Auth touches backend middleware, deployment configs, Helm charts, IaC, Clients, etc
- Architectural roots scattered across 6+ directories
- Each directory contains dozens of subdirectories and hundreds of files
- **No single directory tells the whole story**

An agent without structured discovery tools tends to:

- Tunnel-vision on one directory
- Miss cross-cutting concerns (ignore related architectural components)
- Consume excessive context reading irrelevant files

AUx skills seek to address this by enabling bounded, repo-wide surface scans before deep file reads.
