"""Tests for aux ccx command — Cyclomatic and Cognitive Complexity metrics."""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import pytest
from pydantic import ValidationError

from aux.cli import create_parser
from aux.kernels.ccx import (
    _compute_zone,
    _interpret,
    _walk_file,
    ccx_kernel,
)
from aux.plans.schemas import CcxPlan


def _run(argv: list[str]) -> tuple[int, str]:
    """Run the CLI with captured stdout, return (exit_code, output)."""
    parser = create_parser()
    args = parser.parse_args(argv)

    buf = io.StringIO()
    with redirect_stdout(buf):
        assert hasattr(args, "func"), f"No func for {argv}"
        rc = args.func(args)

    return rc, buf.getvalue()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _walk_python(tmp_path: Path, source: str, filename: str = "sample.py"):
    """Write a Python source string to a temp file and walk it.

    Returns list[FunctionMetrics] for that single file.
    """
    file_path = tmp_path / filename
    file_path.write_text(source)
    functions, errors = _walk_file(file_path, "python", tmp_path, (10, 20, 50))
    assert not errors, f"Walker errors: {errors}"
    return functions


def _by_name(functions, name: str):
    """Look up a function by name from a list of FunctionMetrics."""
    for fn in functions:
        if fn.name == name:
            return fn
    raise AssertionError(f"Function {name!r} not found in {[f.name for f in functions]}")


# ---------------------------------------------------------------------------
# 1. Schema / plan validation tests
# ---------------------------------------------------------------------------

def test_ccx_plan_requires_root():
    with pytest.raises(ValidationError):
        CcxPlan()  # type: ignore[call-arg]


def test_ccx_plan_defaults():
    plan = CcxPlan(root="/tmp")
    assert plan.root == "/tmp"
    assert plan.languages == []
    assert plan.globs == []
    assert plan.excludes == []
    assert plan.hidden is False
    assert plan.no_ignore is False
    assert plan.max_results is None
    assert plan.min_ccx == 1


def test_ccx_plan_accepts_single_language():
    plan = CcxPlan(root="/tmp", languages=["python"])
    assert plan.languages == ["python"]


def test_ccx_plan_accepts_multiple_languages():
    plan = CcxPlan(root="/tmp", languages=["python", "go", "rust"])
    assert plan.languages == ["python", "go", "rust"]


def test_ccx_plan_max_results_ge_1():
    with pytest.raises(ValidationError):
        CcxPlan(root="/tmp", max_results=0)


def test_ccx_plan_max_results_valid():
    plan = CcxPlan(root="/tmp", max_results=5)
    assert plan.max_results == 5


def test_ccx_plan_min_ccx_default_is_1():
    plan = CcxPlan(root="/tmp")
    assert plan.min_ccx == 1


def test_ccx_plan_min_ccx_rejects_zero():
    with pytest.raises(ValidationError):
        CcxPlan(root="/tmp", min_ccx=0)


def test_ccx_plan_min_ccx_accepts_higher():
    plan = CcxPlan(root="/tmp", min_ccx=11)
    assert plan.min_ccx == 11


# ---------------------------------------------------------------------------
# 2. Zone logic unit tests
# ---------------------------------------------------------------------------

def test_zone_simple_lower_bound():
    assert _compute_zone(1, (10, 20, 50)) == "simple"


def test_zone_simple_upper_bound():
    assert _compute_zone(10, (10, 20, 50)) == "simple"


def test_zone_moderate_lower_bound():
    assert _compute_zone(11, (10, 20, 50)) == "moderate"


def test_zone_moderate_upper_bound():
    assert _compute_zone(20, (10, 20, 50)) == "moderate"


def test_zone_complex_lower_bound():
    assert _compute_zone(21, (10, 20, 50)) == "complex"


def test_zone_complex_upper_bound():
    assert _compute_zone(50, (10, 20, 50)) == "complex"


def test_zone_untestable_lower_bound():
    assert _compute_zone(51, (10, 20, 50)) == "untestable"


def test_zone_untestable_high():
    assert _compute_zone(100, (10, 20, 50)) == "untestable"


def test_zone_custom_thresholds():
    # Stricter thresholds
    assert _compute_zone(5, (3, 6, 10)) == "moderate"
    assert _compute_zone(7, (3, 6, 10)) == "complex"
    assert _compute_zone(11, (3, 6, 10)) == "untestable"


def test_interpret_contains_ccx_value():
    text = _interpret(ccx=15, cog=15, zone="moderate")
    assert "CCX=15" in text


def test_interpret_flags_heavy_nesting():
    # CogC much higher than CCX should produce "heavy nesting" note
    text = _interpret(ccx=4, cog=8, zone="simple")
    assert "heavy nesting" in text or "CogC=8" in text


# ---------------------------------------------------------------------------
# 3. Python walker unit tests
# ---------------------------------------------------------------------------

def test_python_ccx_straight_line(tmp_path: Path):
    funcs = _walk_python(tmp_path, "def f():\n    return 1\n")
    assert len(funcs) == 1
    assert funcs[0].name == "f"
    assert funcs[0].ccx == 1
    assert funcs[0].cog == 0
    assert funcs[0].zone == "simple"


def test_python_ccx_single_if(tmp_path: Path):
    src = (
        "def f(x):\n"
        "    if x:\n"
        "        return 1\n"
        "    return 2\n"
    )
    fn = _by_name(_walk_python(tmp_path, src), "f")
    assert fn.ccx == 2  # base + 1 (if)
    assert fn.cog == 1  # if at depth 0


def test_python_ccx_if_elif_else(tmp_path: Path):
    src = (
        "def f(x):\n"
        "    if x == 1:\n"
        "        return 'one'\n"
        "    elif x == 2:\n"
        "        return 'two'\n"
        "    else:\n"
        "        return 'other'\n"
    )
    fn = _by_name(_walk_python(tmp_path, src), "f")
    # base + if + elif (else is not counted)
    assert fn.ccx == 3
    # CogC: if at depth 0 = 1, elif at depth 0 = 1
    assert fn.cog == 2


def test_python_ccx_nested_if(tmp_path: Path):
    src = (
        "def f(x, y):\n"
        "    if x:\n"
        "        if y:\n"
        "            return 1\n"
        "    return 0\n"
    )
    fn = _by_name(_walk_python(tmp_path, src), "f")
    assert fn.ccx == 3  # base + outer if + inner if
    # CogC: outer if at depth 0 = 1, inner if at depth 1 = 2
    assert fn.cog == 3


def test_python_ccx_for_loop(tmp_path: Path):
    src = (
        "def f(items):\n"
        "    for item in items:\n"
        "        process(item)\n"
    )
    fn = _by_name(_walk_python(tmp_path, src), "f")
    assert fn.ccx == 2
    assert fn.cog == 1


def test_python_ccx_while_loop(tmp_path: Path):
    src = (
        "def f(x):\n"
        "    while x > 0:\n"
        "        x -= 1\n"
    )
    fn = _by_name(_walk_python(tmp_path, src), "f")
    assert fn.ccx == 2
    assert fn.cog == 1


def test_python_ccx_try_single_except(tmp_path: Path):
    src = (
        "def f():\n"
        "    try:\n"
        "        do_thing()\n"
        "    except ValueError:\n"
        "        handle()\n"
    )
    fn = _by_name(_walk_python(tmp_path, src), "f")
    assert fn.ccx == 2  # base + 1 except
    assert fn.cog == 1


def test_python_ccx_try_multiple_except(tmp_path: Path):
    src = (
        "def f():\n"
        "    try:\n"
        "        do_thing()\n"
        "    except ValueError:\n"
        "        v_handle()\n"
        "    except TypeError:\n"
        "        t_handle()\n"
        "    except KeyError:\n"
        "        k_handle()\n"
    )
    fn = _by_name(_walk_python(tmp_path, src), "f")
    assert fn.ccx == 4  # base + 3 except clauses
    assert fn.cog == 3


def test_python_ccx_boolean_and_chain(tmp_path: Path):
    src = (
        "def f(a, b, c):\n"
        "    return a and b and c\n"
    )
    fn = _by_name(_walk_python(tmp_path, src), "f")
    # base + 2 'and' operators (one boolean_operator per binary op)
    assert fn.ccx == 3
    # CogC: one homogeneous sequence = 1
    assert fn.cog == 1


def test_python_ccx_boolean_or_chain(tmp_path: Path):
    src = (
        "def f(a, b, c):\n"
        "    return a or b or c\n"
    )
    fn = _by_name(_walk_python(tmp_path, src), "f")
    assert fn.ccx == 3
    assert fn.cog == 1


def test_python_ccx_mixed_boolean_operators(tmp_path: Path):
    # (a and b) or c — switching operator counts as +1 for CogC
    src = (
        "def f(a, b, c):\n"
        "    return (a and b) or c\n"
    )
    fn = _by_name(_walk_python(tmp_path, src), "f")
    # 2 boolean_operators total (one and, one or)
    assert fn.ccx == 3
    # CogC: outer or = 1, inner and (different op from parent) = 1
    assert fn.cog == 2


def test_python_ccx_ternary(tmp_path: Path):
    src = (
        "def f(x):\n"
        "    return 'yes' if x else 'no'\n"
    )
    fn = _by_name(_walk_python(tmp_path, src), "f")
    assert fn.ccx == 2  # base + ternary
    assert fn.cog == 1


def test_python_ccx_match_case(tmp_path: Path):
    src = (
        "def f(x):\n"
        "    match x:\n"
        "        case 1:\n"
        "            return 'one'\n"
        "        case 2:\n"
        "            return 'two'\n"
        "        case _:\n"
        "            return 'other'\n"
    )
    fn = _by_name(_walk_python(tmp_path, src), "f")
    # base + 3 case clauses
    assert fn.ccx == 4


def test_python_ccx_lambda_is_separate(tmp_path: Path):
    src = (
        "def outer(items):\n"
        "    return list(map(lambda x: x + 1 if x > 0 else 0, items))\n"
    )
    funcs = _walk_python(tmp_path, src)
    names = {f.name for f in funcs}
    assert "outer" in names
    assert "<lambda>" in names

    outer = _by_name(funcs, "outer")
    lam = _by_name(funcs, "<lambda>")

    # outer's body has no decision points of its own (the ternary lives in the lambda)
    assert outer.ccx == 1
    # lambda has the ternary
    assert lam.ccx == 2


def test_python_ccx_nested_function(tmp_path: Path):
    src = (
        "def outer(x):\n"
        "    def inner(y):\n"
        "        if y > 0:\n"
        "            return 1\n"
        "        return 0\n"
        "    return inner(x)\n"
    )
    funcs = _walk_python(tmp_path, src)
    outer = _by_name(funcs, "outer")
    inner = _by_name(funcs, "inner")
    # outer has no decision points; inner's branches don't propagate
    assert outer.ccx == 1
    # inner has one if
    assert inner.ccx == 2


def test_python_ccx_method_in_class(tmp_path: Path):
    src = (
        "class C:\n"
        "    def method(self, x):\n"
        "        if x:\n"
        "            return 1\n"
        "        return 0\n"
        "    def other(self):\n"
        "        return 42\n"
    )
    funcs = _walk_python(tmp_path, src)
    names = {f.name for f in funcs}
    assert "method" in names
    assert "other" in names
    assert _by_name(funcs, "method").ccx == 2
    assert _by_name(funcs, "other").ccx == 1


def test_python_ccx_two_top_level_functions(tmp_path: Path):
    src = (
        "def a():\n"
        "    return 1\n"
        "\n"
        "def b(x):\n"
        "    if x:\n"
        "        return 2\n"
        "    return 3\n"
    )
    funcs = _walk_python(tmp_path, src)
    assert len(funcs) == 2
    assert _by_name(funcs, "a").ccx == 1
    assert _by_name(funcs, "b").ccx == 2


def test_python_walker_emits_line_numbers(tmp_path: Path):
    src = (
        "# header comment\n"
        "\n"
        "def f():\n"
        "    return 1\n"
    )
    fn = _by_name(_walk_python(tmp_path, src), "f")
    assert fn.line == 3  # 1-based
    assert fn.end_line >= fn.line


def test_python_walker_ccx_minimum_one(tmp_path: Path):
    """The CCX of even an empty function body should be at least 1."""
    src = (
        "def f():\n"
        "    pass\n"
    )
    fn = _by_name(_walk_python(tmp_path, src), "f")
    assert fn.ccx >= 1
    assert fn.cog == 0


def test_python_kernel_aggregates_across_files(tmp_path: Path):
    """Smoke test for the full kernel: two files, two functions."""
    (tmp_path / "a.py").write_text("def f():\n    if x:\n        return 1\n    return 0\n")
    (tmp_path / "b.py").write_text("def g():\n    return 1\n")

    result = ccx_kernel(root=tmp_path, languages=["python"])
    assert result.functions_analyzed == 2
    assert result.languages.get("python") == 2
    # Sorted by ccx desc: f (ccx=2) before g (ccx=1)
    assert result.functions[0].name == "f"
    assert result.functions[1].name == "g"


# ---------------------------------------------------------------------------
# 4. Per-language walker tests
# ---------------------------------------------------------------------------

def _walk_one(tmp_path: Path, source: str, filename: str, language: str):
    """Generic helper: write source to a temp file and walk it."""
    file_path = tmp_path / filename
    file_path.write_text(source)
    functions, errors = _walk_file(file_path, language, tmp_path, (10, 20, 50))
    assert not errors, f"Walker errors for {language}: {errors}"
    return functions


# --- JavaScript ---

def test_js_ccx_arrow_function_with_ternary(tmp_path: Path):
    src = "const f = (x) => x > 0 ? 'pos' : 'neg';\n"
    funcs = _walk_one(tmp_path, src, "f.js", "javascript")
    assert len(funcs) == 1
    assert funcs[0].ccx == 2  # base + ternary


def test_js_ccx_if_else_chain(tmp_path: Path):
    src = (
        "function classify(x) {\n"
        "  if (x > 0) return 'pos';\n"
        "  else if (x < 0) return 'neg';\n"
        "  else return 'zero';\n"
        "}\n"
    )
    funcs = _walk_one(tmp_path, src, "f.js", "javascript")
    fn = _by_name(funcs, "classify")
    # base + outer if + nested if (else if parses as else { if })
    assert fn.ccx == 3


def test_js_ccx_switch_with_cases(tmp_path: Path):
    src = (
        "function f(x) {\n"
        "  switch (x) {\n"
        "    case 1: return 'a';\n"
        "    case 2: return 'b';\n"
        "    case 3: return 'c';\n"
        "    default: return 'z';\n"
        "  }\n"
        "}\n"
    )
    funcs = _walk_one(tmp_path, src, "f.js", "javascript")
    fn = _by_name(funcs, "f")
    # base + 3 cases (default not counted)
    assert fn.ccx == 4


def test_js_ccx_try_catch(tmp_path: Path):
    src = (
        "function f() {\n"
        "  try {\n"
        "    doThing();\n"
        "  } catch (e) {\n"
        "    handle(e);\n"
        "  }\n"
        "}\n"
    )
    funcs = _walk_one(tmp_path, src, "f.js", "javascript")
    fn = _by_name(funcs, "f")
    assert fn.ccx == 2  # base + catch


def test_js_ccx_boolean_and_chain(tmp_path: Path):
    src = (
        "function f(a, b, c) {\n"
        "  return a && b && c;\n"
        "}\n"
    )
    funcs = _walk_one(tmp_path, src, "f.js", "javascript")
    fn = _by_name(funcs, "f")
    # Two && operators
    assert fn.ccx == 3
    # CogC: one homogeneous sequence
    assert fn.cog == 1


def test_js_ccx_mixed_boolean(tmp_path: Path):
    src = (
        "function f(a, b, c) {\n"
        "  return (a && b) || c;\n"
        "}\n"
    )
    funcs = _walk_one(tmp_path, src, "f.js", "javascript")
    fn = _by_name(funcs, "f")
    assert fn.ccx == 3
    # Switching from && to || → +1 each
    assert fn.cog == 2


# --- TypeScript ---

def test_ts_ccx_function_with_for_and_if(tmp_path: Path):
    src = (
        "function process(items: number[]): number {\n"
        "  let count = 0;\n"
        "  for (const x of items) {\n"
        "    if (x > 0) count++;\n"
        "  }\n"
        "  return count;\n"
        "}\n"
    )
    funcs = _walk_one(tmp_path, src, "f.ts", "typescript")
    fn = _by_name(funcs, "process")
    # base + for + if
    assert fn.ccx == 3


# --- Go ---

def test_go_ccx_for_with_if(tmp_path: Path):
    src = (
        "package p\n"
        "\n"
        "func Process(xs []int) int {\n"
        "    sum := 0\n"
        "    for _, x := range xs {\n"
        "        if x > 0 {\n"
        "            sum += x\n"
        "        }\n"
        "    }\n"
        "    return sum\n"
        "}\n"
    )
    funcs = _walk_one(tmp_path, src, "f.go", "go")
    fn = _by_name(funcs, "Process")
    # base + for + if
    assert fn.ccx == 3


def test_go_ccx_switch_cases(tmp_path: Path):
    src = (
        "package p\n"
        "\n"
        "func Classify(x int) string {\n"
        "    switch x {\n"
        "    case 1:\n"
        "        return \"one\"\n"
        "    case 2:\n"
        "        return \"two\"\n"
        "    default:\n"
        "        return \"other\"\n"
        "    }\n"
        "}\n"
    )
    funcs = _walk_one(tmp_path, src, "f.go", "go")
    fn = _by_name(funcs, "Classify")
    # base + 2 expression_cases (default not counted)
    assert fn.ccx == 3


def test_go_ccx_select_communication_cases(tmp_path: Path):
    src = (
        "package p\n"
        "\n"
        "func Wait(c1, c2 chan int) int {\n"
        "    select {\n"
        "    case x := <-c1:\n"
        "        return x\n"
        "    case y := <-c2:\n"
        "        return y\n"
        "    }\n"
        "}\n"
    )
    funcs = _walk_one(tmp_path, src, "f.go", "go")
    fn = _by_name(funcs, "Wait")
    # base + 2 communication_cases
    assert fn.ccx == 3


# --- Rust ---

def test_rust_ccx_match_arms(tmp_path: Path):
    src = (
        "fn classify(x: i32) -> &'static str {\n"
        "    match x {\n"
        "        1 => \"one\",\n"
        "        2 => \"two\",\n"
        "        _ => \"other\",\n"
        "    }\n"
        "}\n"
    )
    funcs = _walk_one(tmp_path, src, "f.rs", "rust")
    fn = _by_name(funcs, "classify")
    # base + 3 match_arms (we count all arms including wildcard)
    assert fn.ccx == 4


def test_rust_ccx_if_let(tmp_path: Path):
    src = (
        "fn parse(s: Option<&str>) -> bool {\n"
        "    if let Some(x) = s {\n"
        "        if x.is_empty() {\n"
        "            return false;\n"
        "        }\n"
        "        return true;\n"
        "    }\n"
        "    false\n"
        "}\n"
    )
    funcs = _walk_one(tmp_path, src, "f.rs", "rust")
    fn = _by_name(funcs, "parse")
    # base + outer if (if_let) + nested if
    assert fn.ccx == 3


# --- Java ---

def test_java_ccx_enhanced_for_with_if(tmp_path: Path):
    src = (
        "class C {\n"
        "    int count(int[] xs) {\n"
        "        int n = 0;\n"
        "        for (int x : xs) {\n"
        "            if (x > 0) n++;\n"
        "        }\n"
        "        return n;\n"
        "    }\n"
        "}\n"
    )
    funcs = _walk_one(tmp_path, src, "C.java", "java")
    fn = _by_name(funcs, "count")
    # base + enhanced_for + if
    assert fn.ccx == 3


def test_java_ccx_try_catch_finally(tmp_path: Path):
    src = (
        "class C {\n"
        "    void f() {\n"
        "        try {\n"
        "            doThing();\n"
        "        } catch (Exception e) {\n"
        "            handle(e);\n"
        "        } finally {\n"
        "            cleanup();\n"
        "        }\n"
        "    }\n"
        "}\n"
    )
    funcs = _walk_one(tmp_path, src, "C.java", "java")
    fn = _by_name(funcs, "f")
    # base + 1 catch (try and finally not counted)
    assert fn.ccx == 2


# --- Kernel-level multi-language tests ---

def test_kernel_mixed_language_detection(tmp_path: Path):
    """The kernel should auto-detect Python and Go in the same tree."""
    (tmp_path / "a.py").write_text("def f():\n    if x:\n        return 1\n    return 0\n")
    (tmp_path / "b.go").write_text(
        "package p\n"
        "\n"
        "func G(x int) int {\n"
        "    if x > 0 {\n"
        "        return 1\n"
        "    }\n"
        "    return 0\n"
        "}\n"
    )
    result = ccx_kernel(root=tmp_path)  # languages=None → auto
    assert result.languages.get("python") == 1
    assert result.languages.get("go") == 1
    assert result.functions_analyzed == 2


def test_kernel_languages_filter(tmp_path: Path):
    """Explicit languages list restricts analysis."""
    (tmp_path / "a.py").write_text("def f():\n    return 1\n")
    (tmp_path / "b.go").write_text(
        "package p\n\nfunc G() int {\n    return 1\n}\n"
    )
    result = ccx_kernel(root=tmp_path, languages=["python"])
    assert result.languages.get("python") == 1
    assert "go" not in result.languages


def test_kernel_unsupported_language_errors(tmp_path: Path):
    """Unsupported language in the languages list returns an error."""
    result = ccx_kernel(root=tmp_path, languages=["cobol"])
    assert any("cobol" in e or "Unsupported" in e for e in result.errors)
    assert result.functions_analyzed == 0


# ---------------------------------------------------------------------------
# 7. CLI round-trip tests
# ---------------------------------------------------------------------------

def test_cli_ccx_schema():
    rc, output = _run(["ccx", "--schema"])
    assert rc == 0
    schema = json.loads(output)
    assert "properties" in schema
    props = schema["properties"]
    assert "root" in props
    assert "languages" in props
    assert "min_ccx" in props
    assert "max_results" in props


def test_cli_ccx_missing_root():
    rc, output = _run(["ccx"])
    assert rc == 1
    data = json.loads(output)
    assert "error" in data


def test_cli_ccx_root_not_exists():
    rc, output = _run(["ccx", "--root", "/nonexistent/path/that/does/not/exist"])
    assert rc == 1
    data = json.loads(output)
    assert "error" in data


def test_cli_ccx_valid_json_output(tmp_path: Path):
    """Full round-trip: produces valid JSON with all required top-level keys."""
    (tmp_path / "a.py").write_text("def f():\n    return 1\n")

    _, output = _run(["ccx", "--root", str(tmp_path)])
    data = json.loads(output)
    assert "summary" in data
    assert "functions" in data
    assert "files" in data
    assert "errors" in data


def test_cli_ccx_summary_keys(tmp_path: Path):
    """Summary must have all expected keys."""
    (tmp_path / "a.py").write_text("def f():\n    if x:\n        return 1\n    return 0\n")

    _, output = _run(["ccx", "--root", str(tmp_path)])
    data = json.loads(output)
    summary = data["summary"]

    assert "languages" in summary
    assert "files_searched" in summary
    assert "functions_analyzed" in summary
    assert "zone_counts" in summary
    assert "guidance" in summary


def test_cli_ccx_function_fields(tmp_path: Path):
    """Every function entry must carry the documented fields."""
    (tmp_path / "a.py").write_text(
        "def f(x):\n"
        "    if x > 0:\n"
        "        return 1\n"
        "    return 0\n"
    )

    _, output = _run(["ccx", "--root", str(tmp_path)])
    data = json.loads(output)
    assert len(data["functions"]) == 1
    fn = data["functions"][0]
    for field in ("name", "file", "path", "line", "end_line", "language",
                  "ccx", "cog", "zone", "interpretation"):
        assert field in fn, f"Missing field {field!r} in {fn}"


def test_cli_ccx_plan_mode(tmp_path: Path):
    """Plan mode round-trip."""
    (tmp_path / "a.py").write_text("def f():\n    return 1\n")

    plan_json = json.dumps({"root": str(tmp_path), "languages": ["python"]})
    _, output = _run(["ccx", "--plan", plan_json])
    data = json.loads(output)
    assert "summary" in data
    assert data["summary"]["languages"].get("python") == 1


def test_cli_ccx_sorted_by_ccx_desc(tmp_path: Path):
    """Functions must be sorted by ccx descending."""
    (tmp_path / "a.py").write_text(
        "def simple():\n"
        "    return 1\n"
        "\n"
        "def complex_one(x, y):\n"
        "    if x:\n"
        "        if y:\n"
        "            return 1\n"
        "    return 0\n"
    )

    _, output = _run(["ccx", "--root", str(tmp_path)])
    data = json.loads(output)
    ccxs = [f["ccx"] for f in data["functions"]]
    assert ccxs == sorted(ccxs, reverse=True)


def test_cli_ccx_min_ccx_filter(tmp_path: Path):
    """--min-ccx filters out simple functions."""
    (tmp_path / "a.py").write_text(
        "def simple():\n"
        "    return 1\n"
        "\n"
        "def complex_one(x, y):\n"
        "    if x:\n"
        "        if y:\n"
        "            return 1\n"
        "    return 0\n"
    )

    _, output = _run(["ccx", "--root", str(tmp_path), "--min-ccx", "2"])
    data = json.loads(output)
    names = [f["name"] for f in data["functions"]]
    assert "complex_one" in names
    assert "simple" not in names


def test_cli_ccx_max_results_truncation(tmp_path: Path):
    """--max-results caps the output and sets truncated=True."""
    (tmp_path / "a.py").write_text(
        "def f1(): return 1\n"
        "def f2(): return 2\n"
        "def f3(): return 3\n"
    )

    _, output = _run(["ccx", "--root", str(tmp_path), "--max-results", "2"])
    data = json.loads(output)
    assert len(data["functions"]) == 2
    assert data["summary"].get("truncated") is True


def test_cli_ccx_unsupported_language_in_list(tmp_path: Path):
    """An unsupported language in --language returns error JSON."""
    rc, output = _run(["ccx", "--root", str(tmp_path), "--language", "cobol"])
    data = json.loads(output)
    # Either error field or errors array populated
    assert "error" in data or (data.get("errors") and len(data["errors"]) > 0)
    assert rc == 1


def test_cli_ccx_zone_counts_include_all_zones(tmp_path: Path):
    """zone_counts must always include all standard zones."""
    (tmp_path / "a.py").write_text("def f():\n    return 1\n")

    _, output = _run(["ccx", "--root", str(tmp_path)])
    data = json.loads(output)
    zone_counts = data["summary"]["zone_counts"]
    for zone in ("simple", "moderate", "complex", "untestable", "unknown"):
        assert zone in zone_counts, f"Zone '{zone}' missing from zone_counts"


# ---------------------------------------------------------------------------
# 6. File I/O and error handling
# ---------------------------------------------------------------------------

def test_unparseable_file_does_not_crash(tmp_path: Path):
    """A file with parser-breaking syntax should produce no functions but not crash."""
    # Tree-sitter is generally tolerant; produce structurally invalid code that
    # still won't yield function definitions.
    bad = tmp_path / "broken.py"
    bad.write_text("def f(\n  unclosed paren\nclass\nthis is not python at all (((\n")

    funcs, errors = _walk_file(bad, "python", tmp_path, (10, 20, 50))
    # Either zero functions, or functions with valid metrics; never a crash.
    for fn in funcs:
        assert fn.ccx >= 1


def test_unsupported_language_skipped_silently(tmp_path: Path):
    """A file in an unsupported language is skipped without crashing."""
    f = tmp_path / "code.cobol"
    f.write_text("IDENTIFICATION DIVISION.\nPROGRAM-ID. HELLO.\n")

    result = ccx_kernel(root=tmp_path)  # auto-detect; cobol has no entry
    # cobol is skipped; nothing analyzed; no errors
    assert result.functions_analyzed == 0
    # And the cobol-specific extension didn't appear in the supported globs
    # so find_kernel may not have even discovered it — that's fine.


def test_empty_file_zero_functions(tmp_path: Path):
    """An empty Python file produces zero functions, no errors."""
    empty = tmp_path / "empty.py"
    empty.write_text("")

    funcs, errors = _walk_file(empty, "python", tmp_path, (10, 20, 50))
    assert funcs == []
    assert errors == []


def test_file_with_only_top_level_code(tmp_path: Path):
    """A file with no function definitions yields zero FunctionMetrics."""
    f = tmp_path / "module.py"
    f.write_text("x = 1\ny = 2\nprint(x + y)\n")

    funcs, errors = _walk_file(f, "python", tmp_path, (10, 20, 50))
    assert funcs == []
    assert errors == []


def test_bash_file_excluded_silently(tmp_path: Path):
    """Bash files are explicitly excluded from analysis."""
    sh = tmp_path / "script.sh"
    sh.write_text("#!/bin/bash\nfor f in *.txt; do\n  if [ -f \"$f\" ]; then\n    echo $f\n  fi\ndone\n")

    result = ccx_kernel(root=tmp_path)
    # Bash files don't contribute to functions_analyzed even though fd may discover them
    assert result.functions_analyzed == 0
    assert "bash" not in result.languages


# ---------------------------------------------------------------------------
# 8. Guidance and zone counts (kernel-level)
# ---------------------------------------------------------------------------

def test_kernel_zone_counts_include_all_standard_zones(tmp_path: Path):
    """Even with zero functions, the zone_counts dict has all four named zones plus unknown."""
    result = ccx_kernel(root=tmp_path)
    assert set(result.zone_counts.keys()) >= {
        "simple", "moderate", "complex", "untestable", "unknown",
    }


def test_kernel_guidance_only_for_non_simple(tmp_path: Path):
    """Guidance should not include simple-zone functions."""
    (tmp_path / "a.py").write_text(
        "def simple_fn():\n"
        "    return 1\n"
        "\n"
        "def complex_fn(x):\n"
        # 14 ifs to push into moderate zone
        + "".join(f"    if x == {i}: return {i}\n" for i in range(14))
    )

    result = ccx_kernel(root=tmp_path)
    # The guidance lines should reference complex_fn but not simple_fn
    guidance_text = " ".join(result.guidance)
    assert "complex_fn" in guidance_text
    assert "simple_fn" not in guidance_text


def test_kernel_guidance_format(tmp_path: Path):
    """Guidance entries follow file:line name (Zone): CCX=N, CogC=M. action."""
    (tmp_path / "a.py").write_text(
        "def big_branchy(x):\n"
        + "".join(f"    if x == {i}: return {i}\n" for i in range(15))
    )

    result = ccx_kernel(root=tmp_path)
    assert len(result.guidance) >= 1
    g = result.guidance[0]
    assert "big_branchy" in g
    assert "CCX=" in g
    assert "CogC=" in g
    assert "Moderate" in g or "Complex" in g or "Untestable" in g


def test_kernel_languages_dict_excludes_zero_count(tmp_path: Path):
    """The languages dict should only include languages that produced at least one function."""
    (tmp_path / "a.py").write_text("def f(): return 1\n")

    result = ccx_kernel(root=tmp_path)
    assert result.languages == {"python": 1}
