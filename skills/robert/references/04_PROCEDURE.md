---
description: Step-by-step execution flow, metric reference, and output interpretation.
index:
  - Invocation modes
  - Execution pipeline
  - Metrics reference
  - Zone reference
  - Output interpretation
  - Agent usage patterns
---

# Procedure

## Invocation modes

**Simple mode:**
```bash
aux robert --root /path/to/src --language python
aux robert --root /path/to/src --language go
aux robert --root /path/to/src --language go --include-main
```

**Plan mode:**
```bash
aux robert --plan '{"root":"/path","language":"python"}'
aux robert --plan '{"root":"/path","language":"go","include_main":true}'
```

**Schema:**
```bash
aux robert --schema
```

**Skill script:**
```bash
./skills/robert/scripts/skill.sh run --root ./src --language python
./skills/robert/scripts/skill.sh schema
echo '{"root":"./src","language":"go"}' | ./skills/robert/scripts/skill.sh run --stdin
```

## Execution pipeline

1. `find_kernel(root, globs)` — enumerate candidate files for the language
2. `deps_kernel(root, ...)` — extract file-level import edges (AST or text-tier)
3. `_resolve_packages(files, language)` — group files into packages:
   - Go: every directory → one package
   - Python: directory → package only if `__init__.py` present
4. For Go: filter out `package main` packages unless `include_main: true`
5. Build `file_to_pkg` reverse map
6. Aggregate file-level `imported_by` edges to package-level Ca/Ce:
   - For each file `f` in `pkg_f`, for each importer `g` in `f.imported_by`:
     - `Ca[pkg_f].add(pkg_g)` — `pkg_g` contributes to `pkg_f`'s afferent
     - `Ce[pkg_g].add(pkg_f)` — `pkg_f` contributes to `pkg_g`'s efferent
7. For each package: count Na/Nc via tree-sitter (if available) or regex fallback
8. Compute I, A, D', zone, interpretation per package
9. Sort by D' descending, apply max_results cap
10. Build guidance list for non-clean packages

## Metrics reference

| Metric | Formula | Range | Meaning |
|--------|---------|-------|---------|
| Ca (Afferent Coupling) | packages that import this | ≥ 0 | Incoming dependencies |
| Ce (Efferent Coupling) | packages this imports | ≥ 0 | Outgoing dependencies |
| I (Instability) | Ce / (Ca + Ce) | [0, 1] | 0 = stable, 1 = unstable |
| Na | abstract types in package | ≥ 0 | Interfaces / ABCs / Protocols |
| Nc | concrete types in package | ≥ 0 | Structs / classes |
| A (Abstractness) | Na / (Na + Nc) | [0, 1] | 0 = fully concrete, 1 = fully abstract |
| D' (Normalized Distance) | \|A + I − 1\| | [0, 1] | 0 = on main sequence (ideal) |

Abstract type detection:
- **Go**: `type X interface { ... }` → Na; `type X struct { ... }` → Nc
- **Python**: `class X(ABC):` / `class X(Protocol):` / `class X(ABCMeta):` → Na;
  all other `class X:` → Nc

## Zone reference

| Zone | Condition | Meaning | Action |
|------|-----------|---------|--------|
| `pain` | I < 0.3 AND A < 0.3 | Zone of Pain: stable but concrete. Rigid under change. | Extract interfaces or accept stability contract. |
| `uselessness` | I > 0.7 AND A > 0.7 | Zone of Uselessness: abstract but unstable. Wasted abstraction. | Collapse abstractions or invert dependencies. |
| `warning` | D' ≥ 0.5 | Drifting from main sequence. | Rebalance I and A. |
| `clean` | D' < 0.2 | On or near main sequence. Ideal. | No action needed. |
| `ok` | everything else | Minor drift. | Monitor. |
| `unknown` | I or A is None | Insufficient data (no imports or no types). | Add type declarations or check package resolution. |

## Output interpretation

- `summary.zone_counts` — count of packages per zone; scan for `pain`/`uselessness` first
- `summary.guidance` — prioritized action list; one line per non-clean package
- `summary.mean_distance` — overall health indicator; < 0.2 = healthy codebase
- `packages[]` — sorted by D' descending; first entry = worst-designed package
  - `zone` — machine-filterable zone label
  - `interpretation` — human-readable verdict with specific I, A, D' values
  - `instability` — null when Ca + Ce == 0 (isolated package, no edges)
  - `abstractness` — null when Na + Nc == 0 (no type declarations found)
  - `distance` — null when either instability or abstractness is null

## Agent usage patterns

**Pre-refactor check:**
```
1. Run robert on current codebase
2. Note packages in "pain" zone (high Ca, low A) as primary refactor targets
3. Report D' scores to user as baseline
4. After proposing changes, re-run robert to verify D' improved
```

**Self-evaluation before proposing structural changes:**
```
1. Run robert to establish D' baseline
2. Propose changes
3. Run robert again (or reason about expected I/A changes)
4. Report: "This change improves pkg_x from Zone of Pain (D'=0.85) to clean (D'=0.12)"
```

**Design review:**
```
1. Identify packages with D' > 0.5 (warning or pain/uselessness)
2. For each: read interpretation field for specific action
3. Cross-reference with deps --target for import details
4. Summarize findings: N packages on main sequence, M in pain zone, guidance attached
```
