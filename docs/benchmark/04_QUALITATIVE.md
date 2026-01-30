# Qualitative Observations

## Medium Reasoning Output Characteristics

With AUx skills, medium reasoning produced:

- **Comprehensive architecture maps**: Full edge-to-backend auth flow (ingress → oauth2-proxy → backend middleware → routers → frontend/CLI)
- **Detailed security analysis**: 6+ actionable findings (hardcoded secrets, JWKS host header trust, missing iss/aud validation, cookie flags, impersonation header risks)
- **Explicit producer/consumer mapping**: Clear delineation of "who issues identity" vs "who enforces authorization" with file pointers
- **Strategy articulation**: 5-step procedure explicitly aligned with skill documentation
- **Deep file coverage**: Read 43 files across deploy templates, backend auth/middleware/routers, client CLI, and frontend hooks

**Observation**: Medium reasoning leverages skills to go *deeper*, not just faster. The structured approach frees cognitive resources for analysis rather than navigation.

## Low Reasoning Output Characteristics

With AUx skills, low reasoning produced:

- **Solid architecture maps**: Identified all major auth components (Dex, oauth2-proxy, JWT middleware, role guards)
- **Targeted security findings**: JWKS validation, issuer/audience gaps, cookie flags, host header influence
- **Focused file selection**: Read only 11 high-signal files (vs 22 without skills)
- **Efficient search strategy**: 7 bounded grep passes (vs 12+ without skills)
- **Comparable coverage**: Matched medium reasoning's component identification with less detail

**Observation**: Low reasoning uses skills to stay *focused*. Without skills, it over-reads and wanders; with skills, it targets enforcement points efficiently.

## Key Qualitative Difference

| Aspect                  | Medium Reasoning              | Low Reasoning                |
|-------------------------|-------------------------------|------------------------------|
| **Analysis depth**      | Deep (6+ security items)      | Moderate (4 items)           |
| **File coverage**       | Broad (43 files)              | Targeted (11 files)          |
| **Output verbosity**    | Detailed prose                | Concise bullets              |
| **Strategy visibility** | Explicit 5-step               | Implicit but aligned         |
| **Best for**            | Security audits, arch reviews | Bounded discovery, inventory |

**Recommendation**: Match model tier to task complexity. Use medium reasoning for deep analysis; use low reasoning for bounded discovery tasks where cost matters more than exhaustive detail.
