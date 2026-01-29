"""System dependency checker."""

from __future__ import annotations

from aux.util.subprocess import which, run_tool


REQUIRED_TOOLS = {
    "rg": {
        "name": "ripgrep",
        "install": "https://github.com/BurntSushi/ripgrep#installation",
        "commands": ["grep"],
    },
    "fd": {
        "name": "fd-find",
        "install": "https://github.com/sharkdp/fd#installation",
        "commands": ["find"],
        "alternatives": ["fdfind"],  # Debian/Ubuntu
    },
    "git": {
        "name": "git",
        "install": "https://git-scm.com/downloads",
        "commands": ["diff"],
    },
    "diff": {
        "name": "diff",
        "install": "Usually pre-installed on Unix systems",
        "commands": ["diff"],
    },
}


def check_tool(name: str) -> dict:
    """Check if a tool is available and get its version.

    Args:
        name: Tool name

    Returns:
        Dict with availability and version info
    """
    info = REQUIRED_TOOLS.get(name, {"name": name, "install": "Unknown"})

    # Check main name and alternatives
    names_to_check = [name] + info.get("alternatives", [])
    found_path = None
    found_name = None

    for check_name in names_to_check:
        path = which(check_name)
        if path:
            found_path = path
            found_name = check_name
            break

    if not found_path:
        return {
            "name": name,
            "available": False,
            "path": None,
            "version": None,
            "install": info["install"],
        }

    # Try to get version
    version = None
    try:
        result = run_tool([found_name, "--version"], timeout=5.0)
        if result.ok and result.stdout:
            version = result.stdout.strip().split("\n")[0]
    except Exception:
        pass

    return {
        "name": name,
        "available": True,
        "path": str(found_path),
        "version": version,
        "actual_name": found_name if found_name != name else None,
    }


def run_doctor() -> dict:
    """Run full system dependency check.

    Returns:
        Dict with check results and overall status
    """
    results = {}
    all_ok = True

    for tool_name in REQUIRED_TOOLS:
        check = check_tool(tool_name)
        results[tool_name] = check
        if not check["available"]:
            all_ok = False

    return {
        "ok": all_ok,
        "tools": results,
        "message": "All dependencies available" if all_ok else "Some dependencies missing",
    }
