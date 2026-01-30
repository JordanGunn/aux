# Troubleshooting

Common issues and their solutions.

---

## Skill fails with "ModuleNotFoundError" or missing venv

**Symptom:**

```
ModuleNotFoundError: No module named 'cli'
```

or

```
error: .venv not found
```

**Cause:** The `aux` CLI is not installed or not on your `PATH`.

**Solution:** Run the install script:

```bash
# Install the aux CLI and verify dependencies
./scripts/install.sh
```

---

## Skill fails with "command not found: rg" or "command not found: fd"

**Symptom:**

```
error: rg not found. Install ripgrep.
```

or

```
error: fd not found. Install fd-find (binary may be 'fdfind' on Debian/Ubuntu).
```

**Cause:** Required system dependencies are not installed.

**Solution:** Install the missing dependencies. See [QUICKSTART.md](QUICKSTART.md) for installation instructions:

- **ripgrep** (`rg`): Required for grep skill
- **fd** (`fd` or `fdfind`): Required for find skill
- **git**: Required for diff and ls git-status features
- **python** (3.10+): Required for all skills
- **uv**: Required for installation

---

## Skill fails with "uv: command not found"

**Symptom:**

```
error: uv not found. Install from https://docs.astral.sh/uv/
```

**Cause:** The `uv` package manager is not installed.

**Solution:** Install uv:

```bash
# Using curl (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using pip
pip install uv
```

See [https://docs.astral.sh/uv/](https://docs.astral.sh/uv/) for more options.

---

## Skill fails with "Unable to determine which files to ship inside the wheel"

**Symptom:**

```
ValueError: Unable to determine which files to ship inside the wheel
```

**Cause:** The skill's `pyproject.toml` is missing hatch build configuration.

**Solution:** This error typically indicates a packaging misconfiguration during local development. Re-run the installer after correcting the packaging configuration.

```toml
[tool.hatch.build.targets.wheel]
packages = ["."]
```

Then re-run install.

---

## On Debian/Ubuntu: "fd: command not found" but fd-find is installed

**Symptom:** You installed `fd-find` but the find skill can't locate it.

**Cause:** On Debian/Ubuntu, the `fd-find` package installs the binary as `fdfind` (not `fd`) to avoid a naming conflict with another package.

**Solution:** The find skill automatically checks for both `fd` and `fdfind`. If you're still seeing this error:

1. Verify `fdfind` is installed: `which fdfind`
2. Ensure it's in your PATH
3. Re-run the skill

---

## Skill produces no output or empty results

**Symptom:** The skill runs but returns no matches.

**Possible causes:**

1. **Pattern too restrictive** — Try broadening your search pattern
2. **Wrong directory** — Verify the `--root` path is correct
3. **Gitignored files** — By default, skills respect `.gitignore`. Use `--no-ignore` if needed
4. **Hidden files excluded** — Use `--hidden` to include hidden files

---

## Skill output is truncated

**Symptom:** Results end with `truncated: true` or you're missing expected matches.

**Cause:** Skills have bounded output to prevent overwhelming the agent context.

**Solution:** Narrow your search to reduce result count, or increase `--max-results` if your agent can handle more context.

---

## Permission denied when running scripts

**Symptom:**

```
bash: ./scripts/install.sh: Permission denied
```

**Cause:** The script doesn't have execute permissions.

**Solution:**

```bash
chmod +x ./scripts/install.sh
# Or run via bash directly
bash ./scripts/install.sh
```

---

## PowerShell script execution is disabled

**Symptom:**

```
File cannot be loaded because running scripts is disabled on this system.
```

**Cause:** PowerShell execution policy blocks script execution.

**Solution:**

```powershell
# For current session only
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Or run with bypass
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1
```

---

## Git-related features don't work

**Symptom:** The `--git-status` flag or diff skill doesn't work.

**Possible causes:**

1. **Not in a git repository** — These features require a git working tree
2. **Git not installed** — Install git
3. **Corrupted git state** — Try `git status` directly to diagnose

---

## Still stuck?

1. Check the skill's `SKILL.md` for skill-specific documentation
2. Run the skill with `validate` to check dependencies
3. Check [FAQ.md](FAQ.md) for common questions
4. Open an issue with:
   - The exact command or plan you ran
   - The full error output
   - Your OS and shell version
   - Output of `which rg fd git python uv`
