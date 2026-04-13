"""Tests for C# (.NET) language support across all metric kernels."""

from __future__ import annotations

from pathlib import Path

from aux.kernels.ccx import ccx_kernel
from aux.kernels.ck import ck_kernel
from aux.kernels.halstead import halstead_kernel
from aux.kernels.npath import npath_kernel
from aux.kernels.usages import usages_kernel
from aux.util.treesitter import detect_language


def _write(tmp_path: Path, source: str, name: str = "Test.cs") -> Path:
    f = tmp_path / name
    f.write_text(source)
    return tmp_path


# ---------------------------------------------------------------------------
# 1. Language detection
# ---------------------------------------------------------------------------


def test_cs_extension_detected():
    assert detect_language(Path("Foo.cs")) == "c_sharp"


# ---------------------------------------------------------------------------
# 2. CCX — cyclomatic + cognitive complexity
# ---------------------------------------------------------------------------


def test_ccx_simple_method(tmp_path: Path):
    _write(tmp_path, """\
class X {
    int Add(int a, int b) {
        return a + b;
    }
}
""")
    result = ccx_kernel(tmp_path, languages=["c_sharp"])
    assert len(result.functions) == 1
    fn = result.functions[0]
    assert fn.name == "Add"
    assert fn.ccx == 1
    assert fn.language == "c_sharp"


def test_ccx_branching_method(tmp_path: Path):
    _write(tmp_path, """\
class X {
    string Classify(int x) {
        if (x < 0) return "negative";
        else if (x == 0) return "zero";
        else if (x < 10) return "small";
        else return "big";
    }
}
""")
    result = ccx_kernel(tmp_path, languages=["c_sharp"])
    fn = result.functions[0]
    assert fn.ccx >= 4  # 1 + 3 if/else-if branches


def test_ccx_foreach_and_switch(tmp_path: Path):
    _write(tmp_path, """\
class X {
    void Process(int[] items) {
        foreach (var item in items) {
            switch (item) {
                case 0: break;
                case 1: break;
                default: break;
            }
        }
    }
}
""")
    result = ccx_kernel(tmp_path, languages=["c_sharp"])
    fn = result.functions[0]
    # foreach + 3 switch sections
    assert fn.ccx >= 4


def test_ccx_ternary_counted(tmp_path: Path):
    _write(tmp_path, """\
class X {
    int Abs(int x) {
        return x > 0 ? x : -x;
    }
}
""")
    result = ccx_kernel(tmp_path, languages=["c_sharp"])
    fn = result.functions[0]
    assert fn.ccx == 2  # 1 + conditional_expression


# ---------------------------------------------------------------------------
# 3. CK — class metrics
# ---------------------------------------------------------------------------


def test_ck_single_class(tmp_path: Path):
    _write(tmp_path, """\
class Calculator {
    int Add(int a, int b) { return a + b; }
    int Sub(int a, int b) { return a - b; }
}
""")
    result = ck_kernel(tmp_path, languages=["c_sharp"])
    assert len(result.classes) == 1
    c = result.classes[0]
    assert c.name == "Calculator"
    assert c.method_count == 2
    assert c.language == "c_sharp"


def test_ck_inheritance(tmp_path: Path):
    _write(tmp_path, """\
class Base { }
class Child : Base { }
class GrandChild : Child { }
""")
    result = ck_kernel(tmp_path, languages=["c_sharp"])
    by_name = {c.name: c for c in result.classes}
    assert by_name["Base"].dit == 0
    assert by_name["Child"].dit == 1
    assert by_name["Child"].superclasses == ["Base"]
    assert by_name["GrandChild"].dit == 2


def test_ck_noc(tmp_path: Path):
    _write(tmp_path, """\
class Parent { }
class ChildA : Parent { }
class ChildB : Parent { }
class ChildC : Parent { }
""")
    result = ck_kernel(tmp_path, languages=["c_sharp"])
    by_name = {c.name: c for c in result.classes}
    assert by_name["Parent"].noc == 3


def test_ck_struct_and_interface(tmp_path: Path):
    _write(tmp_path, """\
interface IService {
    void Run();
}
struct Point {
    int X;
    int Y;
}
class MyService : IService {
    void Run() { }
}
""")
    result = ck_kernel(tmp_path, languages=["c_sharp"])
    names = {c.name for c in result.classes}
    assert "IService" in names
    assert "Point" in names
    assert "MyService" in names


def test_ck_cbo(tmp_path: Path):
    _write(tmp_path, """\
class Foo { }
class Bar { }
class Baz {
    void DoWork() {
        Foo f;
        Bar b;
    }
}
""")
    result = ck_kernel(tmp_path, languages=["c_sharp"])
    by_name = {c.name: c for c in result.classes}
    assert by_name["Baz"].cbo >= 2  # references Foo and Bar


# ---------------------------------------------------------------------------
# 4. Halstead
# ---------------------------------------------------------------------------


def test_halstead_simple_method(tmp_path: Path):
    _write(tmp_path, """\
class X {
    int Add(int a, int b) {
        return a + b;
    }
}
""")
    result = halstead_kernel(tmp_path, languages=["c_sharp"])
    assert len(result.functions) >= 1
    fn = result.functions[0]
    assert fn.name == "Add"
    assert fn.volume > 0
    assert fn.n1 > 0
    assert fn.n2 > 0
    assert fn.language == "c_sharp"


def test_halstead_invariants(tmp_path: Path):
    _write(tmp_path, """\
class X {
    int Compute(int a, int b) {
        if (a > b) return a + b;
        return a - b;
    }
}
""")
    result = halstead_kernel(tmp_path, languages=["c_sharp"])
    for fn in result.functions:
        assert fn.vocabulary == fn.n1 + fn.n2
        assert fn.length == fn.total_n1 + fn.total_n2


# ---------------------------------------------------------------------------
# 5. NPATH
# ---------------------------------------------------------------------------


def test_npath_straight_line(tmp_path: Path):
    _write(tmp_path, """\
class X {
    int F(int a, int b) {
        int x = a + b;
        int y = x * 2;
        return y;
    }
}
""")
    result = npath_kernel(tmp_path, languages=["c_sharp"])
    fn = result.functions[0]
    assert fn.npath == 1


def test_npath_sequential_ifs(tmp_path: Path):
    _write(tmp_path, """\
class X {
    int F(int x) {
        if (x > 0) { x = x + 1; }
        if (x > 10) { x = x + 2; }
        if (x > 100) { x = x + 3; }
        return x;
    }
}
""")
    result = npath_kernel(tmp_path, languages=["c_sharp"])
    fn = result.functions[0]
    assert fn.npath == 8  # 2 * 2 * 2


def test_npath_if_else(tmp_path: Path):
    _write(tmp_path, """\
class X {
    int F(int x) {
        if (x > 0) {
            return 1;
        } else {
            return 0;
        }
    }
}
""")
    result = npath_kernel(tmp_path, languages=["c_sharp"])
    fn = result.functions[0]
    assert fn.npath == 2


def test_npath_if_else_if_else(tmp_path: Path):
    """if/else if/else → 3 branches."""
    _write(tmp_path, """\
class X {
    int F(int x) {
        if (x > 0) {
            return 1;
        } else if (x < 0) {
            return -1;
        } else {
            return 0;
        }
    }
}
""")
    result = npath_kernel(tmp_path, languages=["c_sharp"])
    fn = result.functions[0]
    assert fn.npath == 3


def test_npath_loop(tmp_path: Path):
    _write(tmp_path, """\
class X {
    int F(int x) {
        while (x > 0) { x--; }
        return x;
    }
}
""")
    result = npath_kernel(tmp_path, languages=["c_sharp"])
    fn = result.functions[0]
    assert fn.npath == 2  # loop body(1) + 1


# ---------------------------------------------------------------------------
# 6. Usages — symbol definitions
# ---------------------------------------------------------------------------


def test_usages_finds_csharp_definitions(tmp_path: Path):
    _write(tmp_path, """\
class MyClass {
    void MyMethod() { }
}
interface IMyInterface { }
struct MyStruct { }
""")
    result = usages_kernel(tmp_path, symbol="MyClass", language="c_sharp")
    assert len(result.definitions) >= 1
    assert any(d.symbol_type == "class" for d in result.definitions)

    result2 = usages_kernel(tmp_path, symbol="MyMethod", language="c_sharp")
    assert len(result2.definitions) >= 1
    assert any(d.symbol_type == "method" for d in result2.definitions)
