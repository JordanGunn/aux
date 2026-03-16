"""Tests for aux robert command — Robert C. Martin package design metrics."""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import pytest
from pydantic import ValidationError

from aux.cli import create_parser
from aux.kernels.robert import (
    _compute_distance,
    _compute_zone,
    _compute_instability,
    _compute_abstractness_score,
    _resolve_packages,
    _compute_abstractness,
    robert_kernel,
)
from aux.plans.schemas import RobertPlan


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
# 1. Schema / plan validation tests
# ---------------------------------------------------------------------------

def test_robert_plan_requires_root():
    with pytest.raises(ValidationError):
        RobertPlan(language="go")


def test_robert_plan_requires_language():
    with pytest.raises(ValidationError):
        RobertPlan(root="/tmp")


def test_robert_plan_valid_go():
    plan = RobertPlan(root="/tmp", language="go")
    assert plan.language == "go"
    assert plan.include_main is False
    assert plan.globs == []
    assert plan.excludes == []
    assert plan.hidden is False
    assert plan.no_ignore is False
    assert plan.max_results is None


def test_robert_plan_valid_python():
    plan = RobertPlan(root="/tmp", language="python")
    assert plan.language == "python"


def test_robert_plan_max_results_ge_1():
    with pytest.raises(ValidationError):
        RobertPlan(root="/tmp", language="go", max_results=0)


def test_robert_plan_max_results_valid():
    plan = RobertPlan(root="/tmp", language="go", max_results=5)
    assert plan.max_results == 5


def test_robert_plan_include_main():
    plan = RobertPlan(root="/tmp", language="go", include_main=True)
    assert plan.include_main is True


# ---------------------------------------------------------------------------
# 2. Metric math unit tests
# ---------------------------------------------------------------------------

def test_instability_zero_when_all_afferent():
    assert _compute_instability(ca=5, ce=0) == 0.0


def test_instability_one_when_all_efferent():
    assert _compute_instability(ca=0, ce=5) == 1.0


def test_instability_half():
    assert _compute_instability(ca=3, ce=3) == pytest.approx(0.5)


def test_instability_none_when_both_zero():
    assert _compute_instability(ca=0, ce=0) is None


def test_abstractness_zero_when_all_concrete():
    assert _compute_abstractness_score(na=0, nc=5) == 0.0


def test_abstractness_one_when_all_abstract():
    assert _compute_abstractness_score(na=5, nc=0) == 1.0


def test_abstractness_half():
    assert _compute_abstractness_score(na=2, nc=2) == pytest.approx(0.5)


def test_abstractness_none_when_both_zero():
    assert _compute_abstractness_score(na=0, nc=0) is None


def test_distance_formula():
    d = _compute_distance(i=0.3, a=0.5)
    assert d == pytest.approx(abs(0.3 + 0.5 - 1.0))


def test_distance_zero_on_main_sequence():
    d = _compute_distance(i=0.5, a=0.5)
    assert d == pytest.approx(0.0)


def test_distance_one_at_worst():
    d = _compute_distance(i=0.0, a=0.0)
    assert d == pytest.approx(1.0)


def test_distance_none_when_i_none():
    assert _compute_distance(i=None, a=0.5) is None


def test_distance_none_when_a_none():
    assert _compute_distance(i=0.5, a=None) is None


def test_compute_zone_pain():
    assert _compute_zone(i=0.1, a=0.1, d=0.8) == "pain"


def test_compute_zone_uselessness():
    assert _compute_zone(i=0.9, a=0.9, d=0.8) == "uselessness"


def test_compute_zone_warning():
    # Not pain or uselessness, D'=0.5
    assert _compute_zone(i=0.5, a=0.0, d=0.5) == "warning"


def test_compute_zone_clean():
    # On main sequence
    assert _compute_zone(i=0.5, a=0.5, d=0.0) == "clean"


def test_compute_zone_ok():
    # Not in any named zone
    assert _compute_zone(i=0.5, a=0.3, d=0.2) == "ok"


def test_compute_zone_unknown_when_i_none():
    assert _compute_zone(i=None, a=0.5, d=None) == "unknown"


def test_compute_zone_unknown_when_a_none():
    assert _compute_zone(i=0.5, a=None, d=None) == "unknown"


# ---------------------------------------------------------------------------
# 3. Package resolver tests
# ---------------------------------------------------------------------------

def test_go_resolver_groups_by_dir(tmp_path: Path):
    pkg_a = tmp_path / "pkg_a"
    pkg_b = tmp_path / "pkg_b"
    pkg_a.mkdir()
    pkg_b.mkdir()

    a1 = pkg_a / "a1.go"
    a2 = pkg_a / "a2.go"
    b1 = pkg_b / "b1.go"
    a1.write_text("package pkga\n")
    a2.write_text("package pkga\n")
    b1.write_text("package pkgb\n")

    pkg_map = _resolve_packages([a1, a2, b1], "go")
    assert str(pkg_a) in pkg_map
    assert str(pkg_b) in pkg_map
    assert set(pkg_map[str(pkg_a)]) == {a1, a2}
    assert pkg_map[str(pkg_b)] == [b1]


def test_python_resolver_requires_init(tmp_path: Path):
    pkg_a = tmp_path / "pkg_a"
    not_a_pkg = tmp_path / "not_a_pkg"
    pkg_a.mkdir()
    not_a_pkg.mkdir()

    init = pkg_a / "__init__.py"
    mod_a = pkg_a / "a.py"
    mod_b = not_a_pkg / "b.py"
    init.write_text("")
    mod_a.write_text("class Foo: pass\n")
    mod_b.write_text("class Bar: pass\n")

    pkg_map = _resolve_packages([init, mod_a, mod_b], "python")
    assert str(pkg_a) in pkg_map
    assert str(not_a_pkg) not in pkg_map


def test_python_resolver_excludes_dir_without_init(tmp_path: Path):
    plain_dir = tmp_path / "plain"
    plain_dir.mkdir()
    f = plain_dir / "module.py"
    f.write_text("x = 1\n")

    pkg_map = _resolve_packages([f], "python")
    assert len(pkg_map) == 0


# ---------------------------------------------------------------------------
# 4. Abstractness query tests
# ---------------------------------------------------------------------------

def test_go_abstractness_counts_interface_and_struct(tmp_path: Path):
    go_file = tmp_path / "types.go"
    go_file.write_text(
        "package myp\n\n"
        "type Reader interface {\n    Read() error\n}\n\n"
        "type Buffer struct {\n    data []byte\n}\n"
    )
    na, nc, errs = _compute_abstractness([go_file], "go")
    # Even if tree-sitter unavailable, regex fallback should detect them
    assert na == 1
    assert nc == 1
    # No critical errors (tree-sitter warnings are acceptable)
    assert not any("read error" in e for e in errs)


def test_python_abstractness_counts_abc_and_concrete(tmp_path: Path):
    py_file = tmp_path / "types.py"
    py_file.write_text(
        "from abc import ABC\n\n"
        "class AbstractBase(ABC):\n    pass\n\n"
        "class ConcreteImpl:\n    pass\n"
    )
    na, nc, errs = _compute_abstractness([py_file], "python")
    assert na == 1
    assert nc == 1
    assert not any("read error" in e for e in errs)


def test_python_abstractness_protocol(tmp_path: Path):
    py_file = tmp_path / "proto.py"
    py_file.write_text(
        "from typing import Protocol\n\n"
        "class Runnable(Protocol):\n    def run(self) -> None: ...\n\n"
        "class Worker:\n    def run(self) -> None: pass\n"
    )
    na, nc, _ = _compute_abstractness([py_file], "python")
    assert na == 1
    assert nc == 1


def test_go_abstractness_multiple_types(tmp_path: Path):
    go_file = tmp_path / "multi.go"
    go_file.write_text(
        "package myp\n\n"
        "type A interface { Do() }\n"
        "type B interface { Undo() }\n"
        "type C struct { val int }\n"
        "type D struct { name string }\n"
        "type E struct { inner C }\n"
    )
    na, nc, _ = _compute_abstractness([go_file], "go")
    assert na == 2
    assert nc == 3


# ---------------------------------------------------------------------------
# 5. Integration — Go
# ---------------------------------------------------------------------------

def test_integration_go_coupling(tmp_path: Path):
    """pkg_a imports pkg_b; verify Ca/Ce and zones."""
    module_root = tmp_path / "mymod"
    pkg_a_dir = module_root / "pkg_a"
    pkg_b_dir = module_root / "pkg_b"
    pkg_a_dir.mkdir(parents=True)
    pkg_b_dir.mkdir(parents=True)

    # pkg_b: exported interface + struct
    # File named pkg_b.go so stem matches import path last component "pkg_b"
    (pkg_b_dir / "pkg_b.go").write_text(
        "package pkg_b\n\n"
        "type Doer interface { Do() }\n"
        "type Impl struct{}\n"
    )

    # pkg_a: imports pkg_b; has only a struct (no interface)
    # File named pkg_a.go for consistency; import uses last component "pkg_b"
    (pkg_a_dir / "pkg_a.go").write_text(
        'package pkg_a\n\nimport "mymod/pkg_b"\n\n'
        "var _ pkg_b.Doer = (*Impl)(nil)\n"
        "type Impl struct{}\n"
    )

    result = robert_kernel(root=module_root, language="go", include_main=True)

    by_pkg = {pm.package: pm for pm in result.packages}
    assert len(by_pkg) == 2

    pkg_a = by_pkg["pkg_a"]
    pkg_b = by_pkg["pkg_b"]

    # pkg_a imports pkg_b → Ce(pkg_a)=1, Ca(pkg_a)=0
    assert pkg_a.ce == 1
    assert pkg_a.ca == 0
    assert pkg_a.instability == pytest.approx(1.0)

    # pkg_b is imported by pkg_a → Ca(pkg_b)=1, Ce(pkg_b)=0
    assert pkg_b.ca == 1
    assert pkg_b.ce == 0
    assert pkg_b.instability == pytest.approx(0.0)

    # Sorted by distance descending
    assert result.packages[0].distance >= result.packages[1].distance


def test_integration_go_main_excluded_by_default(tmp_path: Path):
    """package main is excluded when include_main=False (default)."""
    pkg_a_dir = tmp_path / "pkg_a"
    main_dir = tmp_path / "cmd"
    pkg_a_dir.mkdir()
    main_dir.mkdir()

    (pkg_a_dir / "a.go").write_text("package pkg_a\ntype Svc struct{}\n")
    (main_dir / "main.go").write_text("package main\nfunc main() {}\n")

    result = robert_kernel(root=tmp_path, language="go", include_main=False)
    pkg_names = {pm.package for pm in result.packages}
    assert "cmd" not in pkg_names
    assert "pkg_a" in pkg_names


def test_integration_go_main_included_when_flag_set(tmp_path: Path):
    """package main is included when include_main=True."""
    pkg_a_dir = tmp_path / "pkg_a"
    main_dir = tmp_path / "cmd"
    pkg_a_dir.mkdir()
    main_dir.mkdir()

    (pkg_a_dir / "a.go").write_text("package pkg_a\ntype Svc struct{}\n")
    (main_dir / "main.go").write_text("package main\nfunc main() {}\n")

    result = robert_kernel(root=tmp_path, language="go", include_main=True)
    pkg_names = {pm.package for pm in result.packages}
    assert "cmd" in pkg_names


# ---------------------------------------------------------------------------
# 6. Integration — Python
# ---------------------------------------------------------------------------

def test_integration_python_coupling(tmp_path: Path):
    """pkg_a imports pkg_b; dir without __init__.py is excluded."""
    pkg_a_dir = tmp_path / "pkg_a"
    pkg_b_dir = tmp_path / "pkg_b"
    not_pkg_dir = tmp_path / "not_pkg"
    pkg_a_dir.mkdir()
    pkg_b_dir.mkdir()
    not_pkg_dir.mkdir()

    # pkg_b: one abstract, one concrete
    (pkg_b_dir / "__init__.py").write_text("")
    (pkg_b_dir / "base.py").write_text(
        "from abc import ABC\n\nclass Base(ABC): pass\nclass Impl: pass\n"
    )

    # pkg_a: imports pkg_b, one abstract class
    (pkg_a_dir / "__init__.py").write_text("")
    (pkg_a_dir / "module.py").write_text(
        "from pkg_b import base\nfrom abc import ABC\nclass MyABC(ABC): pass\n"
    )

    # not_pkg: no __init__.py — should be excluded
    (not_pkg_dir / "orphan.py").write_text("class Orphan: pass\n")

    result = robert_kernel(root=tmp_path, language="python")
    pkg_names = {pm.package for pm in result.packages}

    assert "not_pkg" not in pkg_names
    assert "pkg_a" in pkg_names or "pkg_b" in pkg_names


def test_integration_python_no_init_excluded(tmp_path: Path):
    """All dirs without __init__.py are excluded entirely."""
    no_init = tmp_path / "no_init"
    no_init.mkdir()
    (no_init / "module.py").write_text("class X: pass\n")

    result = robert_kernel(root=tmp_path, language="python")
    assert result.packages_analyzed == 0


# ---------------------------------------------------------------------------
# 7. CLI round-trip tests
# ---------------------------------------------------------------------------

def test_cli_robert_schema():
    rc, output = _run(["robert", "--schema"])
    assert rc == 0
    schema = json.loads(output)
    assert "properties" in schema
    props = schema["properties"]
    assert "root" in props
    assert "language" in props
    assert "include_main" in props


def test_cli_robert_missing_root():
    rc, output = _run(["robert", "--language", "python"])
    assert rc == 1
    data = json.loads(output)
    assert "error" in data


def test_cli_robert_missing_language():
    rc, output = _run(["robert", "--root", "/tmp"])
    assert rc == 1
    data = json.loads(output)
    assert "error" in data


def test_cli_robert_valid_json_output(tmp_path: Path):
    """Full round-trip: produces valid JSON with all required top-level keys."""
    pkg_dir = tmp_path / "mypkg"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("class Foo: pass\n")

    _, output = _run(["robert", "--root", str(tmp_path), "--language", "python"])
    # May exit 0 or 1, but output must be valid JSON
    data = json.loads(output)
    assert "summary" in data
    assert "packages" in data
    assert "errors" in data


def test_cli_robert_summary_keys(tmp_path: Path):
    """Summary must have all expected keys."""
    pkg_dir = tmp_path / "mypkg"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("from abc import ABC\nclass Base(ABC): pass\n")

    _, output = _run(["robert", "--root", str(tmp_path), "--language", "python"])
    data = json.loads(output)
    summary = data["summary"]

    assert "language" in summary
    assert "packages_analyzed" in summary
    assert "files_searched" in summary
    assert "zone_counts" in summary
    assert "mean_distance" in summary
    assert "guidance" in summary


def test_cli_robert_packages_have_required_fields(tmp_path: Path):
    """Every package entry must have zone + interpretation."""
    pkg_dir = tmp_path / "mypkg"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("class Foo: pass\n")

    _, output = _run(["robert", "--root", str(tmp_path), "--language", "python"])
    data = json.loads(output)

    for pkg in data["packages"]:
        assert "zone" in pkg, f"Missing zone in {pkg}"
        assert "interpretation" in pkg, f"Missing interpretation in {pkg}"
        assert "distance" in pkg
        assert "instability" in pkg
        assert "abstractness" in pkg


def test_cli_robert_plan_mode(tmp_path: Path):
    """Plan mode round-trip."""
    pkg_dir = tmp_path / "mypkg"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "mod.py").write_text("class A: pass\n")

    plan_json = json.dumps({"root": str(tmp_path), "language": "python"})
    _, output = _run(["robert", "--plan", plan_json])
    data = json.loads(output)
    assert "summary" in data


def test_cli_robert_sorted_by_distance_desc(tmp_path: Path):
    """Packages must be sorted by distance descending."""
    pkg_a = tmp_path / "pkg_a"
    pkg_b = tmp_path / "pkg_b"
    pkg_a.mkdir()
    pkg_b.mkdir()

    (pkg_a / "__init__.py").write_text("")
    (pkg_a / "a.py").write_text("from abc import ABC\nclass A(ABC): pass\n")
    (pkg_b / "__init__.py").write_text("")
    (pkg_b / "b.py").write_text("class B: pass\nclass C: pass\n")

    _, output = _run(["robert", "--root", str(tmp_path), "--language", "python"])
    data = json.loads(output)
    packages = data["packages"]

    if len(packages) >= 2:
        distances = [p["distance"] for p in packages if p["distance"] is not None]
        assert distances == sorted(distances, reverse=True)


def test_cli_robert_unsupported_language():
    """Unsupported language returns error without crashing."""
    _, output = _run(["robert", "--root", "/tmp", "--language", "cobol"])
    data = json.loads(output)
    # Should still be valid JSON; errors field populated or summary shows 0 packages
    assert "summary" in data or "error" in data


# ---------------------------------------------------------------------------
# 8. Zone counts
# ---------------------------------------------------------------------------

def test_zone_counts_include_all_zones(tmp_path: Path):
    """zone_counts must always include all five standard zones."""
    pkg_dir = tmp_path / "p"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "m.py").write_text("class X: pass\n")

    _, output = _run(["robert", "--root", str(tmp_path), "--language", "python"])
    data = json.loads(output)
    zone_counts = data["summary"]["zone_counts"]

    for zone in ("pain", "uselessness", "warning", "clean", "ok"):
        assert zone in zone_counts, f"Zone '{zone}' missing from zone_counts"
