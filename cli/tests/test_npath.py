"""Tests for aux npath — NPATH acyclic execution path complexity."""

from __future__ import annotations

from pathlib import Path

import pytest

from aux.kernels.npath import npath_kernel


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write(tmp_path: Path, source: str, name: str = "test.py") -> Path:
    f = tmp_path / name
    f.write_text(source)
    return tmp_path


def _by_name(result, name: str):
    for fn in result.functions:
        if fn.name == name:
            return fn
    raise AssertionError(f"Function {name!r} not found in {[f.name for f in result.functions]}")


# ---------------------------------------------------------------------------
# 1. Basic / empty
# ---------------------------------------------------------------------------


def test_empty_directory_returns_empty(tmp_path: Path):
    result = npath_kernel(tmp_path)
    assert result.functions == []
    assert result.functions_analyzed == 0


def test_unsupported_language_returns_error(tmp_path: Path):
    result = npath_kernel(tmp_path, languages=["cobol"])
    assert result.functions == []
    assert any("No supported" in e for e in result.errors)


# ---------------------------------------------------------------------------
# 2. Hand-calculated Python NPATH values
# ---------------------------------------------------------------------------


def test_straight_line_npath_1(tmp_path: Path):
    """No branches → NPATH = 1."""
    _write(tmp_path, """\
def straight(a, b):
    x = a + b
    y = x * 2
    return y
""")
    result = npath_kernel(tmp_path)
    fn = _by_name(result, "straight")
    assert fn.npath == 1


def test_single_if_no_else_npath_2(tmp_path: Path):
    """One if without else → NPATH = then(1) + 1 = 2."""
    _write(tmp_path, """\
def one_if(x):
    if x > 0:
        x = x + 1
    return x
""")
    result = npath_kernel(tmp_path)
    fn = _by_name(result, "one_if")
    assert fn.npath == 2


def test_single_if_else_npath_2(tmp_path: Path):
    """One if-else → NPATH = then(1) + else(1) = 2."""
    _write(tmp_path, """\
def if_else(x):
    if x > 0:
        x = x + 1
    else:
        x = x - 1
    return x
""")
    result = npath_kernel(tmp_path)
    fn = _by_name(result, "if_else")
    assert fn.npath == 2


def test_three_sequential_ifs_npath_8(tmp_path: Path):
    """Three sequential ifs (no else) → 2 * 2 * 2 = 8.

    This is the key difference from CCX: CCX = 4, NPATH = 8.
    """
    _write(tmp_path, """\
def three_ifs(x):
    if x > 0:
        x = x + 1
    if x > 10:
        x = x + 2
    if x > 100:
        x = x + 3
    return x
""")
    result = npath_kernel(tmp_path)
    fn = _by_name(result, "three_ifs")
    assert fn.npath == 8


def test_ten_sequential_ifs_npath_1024(tmp_path: Path):
    """The canonical CCX gap case: 10 sequential ifs → NPATH = 2^10 = 1024.

    CCX would report 11 here. NPATH catches the combinatorial explosion.
    """
    lines = ["def ten_ifs(x):"]
    for i in range(10):
        lines.append(f"    if x > {i}:")
        lines.append(f"        x = x + {i}")
    lines.append("    return x")
    _write(tmp_path, "\n".join(lines) + "\n")
    result = npath_kernel(tmp_path)
    fn = _by_name(result, "ten_ifs")
    assert fn.npath == 1024


def test_nested_if_npath(tmp_path: Path):
    """Nested if-else inside if → then_outer has npath 2, else_outer = 1.

    outer if: then = inner_if(2) → 2, else = 1 (implicit)
    total = (2 + 1) = 3
    """
    _write(tmp_path, """\
def nested(x):
    if x > 0:
        if x > 10:
            x = x + 1
        else:
            x = x + 2
    return x
""")
    result = npath_kernel(tmp_path)
    fn = _by_name(result, "nested")
    assert fn.npath == 3


def test_while_loop_npath(tmp_path: Path):
    """while loop → body(1) + 1 = 2."""
    _write(tmp_path, """\
def with_loop(x):
    while x > 0:
        x = x - 1
    return x
""")
    result = npath_kernel(tmp_path)
    fn = _by_name(result, "with_loop")
    assert fn.npath == 2


def test_for_loop_npath(tmp_path: Path):
    """for loop → body(1) + 1 = 2."""
    _write(tmp_path, """\
def with_for(items):
    total = 0
    for x in items:
        total = total + x
    return total
""")
    result = npath_kernel(tmp_path)
    fn = _by_name(result, "with_for")
    assert fn.npath == 2


def test_loop_with_if_npath(tmp_path: Path):
    """Loop body has an if → loop(if(2) + 1) = 3. Sequence: 3 * 1 = 3."""
    _write(tmp_path, """\
def loop_if(items):
    total = 0
    for x in items:
        if x > 0:
            total = total + x
    return total
""")
    result = npath_kernel(tmp_path)
    fn = _by_name(result, "loop_if")
    # for body contains if (npath=2), so loop = 2 + 1 = 3
    assert fn.npath == 3


def test_try_except_npath(tmp_path: Path):
    """try + 1 except → try_body(1) + handler(1) = 2."""
    _write(tmp_path, """\
def with_try(x):
    try:
        x = x + 1
    except Exception:
        x = 0
    return x
""")
    result = npath_kernel(tmp_path)
    fn = _by_name(result, "with_try")
    assert fn.npath == 2


def test_if_elif_else_npath(tmp_path: Path):
    """if/elif/else chain → 3 branches = 1 + 1 + 1 = 3."""
    _write(tmp_path, """\
def three_way(x):
    if x > 0:
        return 1
    elif x < 0:
        return -1
    else:
        return 0
""")
    result = npath_kernel(tmp_path)
    fn = _by_name(result, "three_way")
    assert fn.npath == 3


# ---------------------------------------------------------------------------
# 3. Sorting and filtering
# ---------------------------------------------------------------------------


def test_sorted_by_npath_descending(tmp_path: Path):
    _write(tmp_path, """\
def simple():
    return 1

def branchy(x):
    if x > 0:
        x = x + 1
    if x > 10:
        x = x + 2
    if x > 100:
        x = x + 3
    return x
""")
    result = npath_kernel(tmp_path)
    npaths = [fn.npath for fn in result.functions]
    assert npaths == sorted(npaths, reverse=True)


def test_min_npath_filter(tmp_path: Path):
    _write(tmp_path, """\
def simple():
    return 1

def branchy(x):
    if x > 0:
        x = x + 1
    if x > 10:
        x = x + 2
    return x
""")
    result = npath_kernel(tmp_path, min_npath=3)
    names = [fn.name for fn in result.functions]
    assert "simple" not in names
    assert "branchy" in names


def test_max_results_truncation(tmp_path: Path):
    lines = []
    for i in range(5):
        lines.append(f"def fn{i}(x):")
        lines.append(f"    if x > {i}:")
        lines.append(f"        x = x + {i}")
        lines.append(f"    return x")
        lines.append("")
    _write(tmp_path, "\n".join(lines))
    result = npath_kernel(tmp_path, max_results=2)
    assert len(result.functions) <= 2
    assert result.truncated is True


# ---------------------------------------------------------------------------
# 4. Multi-language
# ---------------------------------------------------------------------------


def test_javascript_npath(tmp_path: Path):
    _write(tmp_path, """\
function branchy(x) {
    if (x > 0) {
        x = x + 1;
    }
    if (x > 10) {
        x = x + 2;
    }
    return x;
}
""", name="test.js")
    result = npath_kernel(tmp_path, languages=["javascript"])
    fn = _by_name(result, "branchy")
    assert fn.language == "javascript"
    assert fn.npath == 4  # 2 * 2


def test_go_npath(tmp_path: Path):
    _write(tmp_path, """\
package main

func branchy(x int) int {
    if x > 0 {
        x = x + 1
    }
    if x > 10 {
        x = x + 2
    }
    return x
}
""", name="test.go")
    result = npath_kernel(tmp_path, languages=["go"])
    fn = _by_name(result, "branchy")
    assert fn.language == "go"
    assert fn.npath == 4


def test_rust_npath(tmp_path: Path):
    _write(tmp_path, """\
fn branchy(x: i32) -> i32 {
    let mut x = x;
    if x > 0 {
        x = x + 1;
    }
    if x > 10 {
        x = x + 2;
    }
    x
}
""", name="test.rs")
    result = npath_kernel(tmp_path, languages=["rust"])
    fn = _by_name(result, "branchy")
    assert fn.language == "rust"
    assert fn.npath == 4


def test_java_npath(tmp_path: Path):
    _write(tmp_path, """\
public class Test {
    public int branchy(int x) {
        if (x > 0) {
            x = x + 1;
        }
        if (x > 10) {
            x = x + 2;
        }
        return x;
    }
}
""", name="Test.java")
    result = npath_kernel(tmp_path, languages=["java"])
    fn = _by_name(result, "branchy")
    assert fn.language == "java"
    assert fn.npath == 4


def test_typescript_npath(tmp_path: Path):
    _write(tmp_path, """\
function branchy(x: number): number {
    if (x > 0) {
        x = x + 1;
    }
    if (x > 10) {
        x = x + 2;
    }
    return x;
}
""", name="test.ts")
    result = npath_kernel(tmp_path, languages=["typescript"])
    fn = _by_name(result, "branchy")
    assert fn.language == "typescript"
    assert fn.npath == 4


# ---------------------------------------------------------------------------
# 5. Nested functions
# ---------------------------------------------------------------------------


def test_nested_function_excluded_from_parent(tmp_path: Path):
    """Nested function's control flow doesn't inflate the parent's NPATH."""
    _write(tmp_path, """\
def outer(x):
    def inner(y):
        if y > 0:
            return y
        return 0
    if x > 0:
        return inner(x)
    return 0
""")
    result = npath_kernel(tmp_path)
    outer = _by_name(result, "outer")
    # outer has one if → NPATH = 2
    # inner's if should NOT be counted in outer's NPATH
    assert outer.npath == 2


# ---------------------------------------------------------------------------
# 6. CLI round-trip
# ---------------------------------------------------------------------------


def test_schema_exits_zero():
    import io
    import json
    from contextlib import redirect_stdout
    from aux.cli import create_parser

    parser = create_parser()
    args = parser.parse_args(["npath", "--schema"])
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = args.func(args)
    assert rc == 0
    schema = json.loads(buf.getvalue())
    assert "properties" in schema


def test_cli_simple_mode(tmp_path: Path):
    import io
    import json
    from contextlib import redirect_stdout
    from aux.cli import create_parser

    _write(tmp_path, """\
def branchy(x):
    if x > 0:
        x = x + 1
    if x > 10:
        x = x + 2
    return x
""")
    parser = create_parser()
    args = parser.parse_args(["npath", "--root", str(tmp_path)])
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = args.func(args)
    assert rc == 0
    data = json.loads(buf.getvalue())
    assert "functions" in data
    assert "summary" in data
