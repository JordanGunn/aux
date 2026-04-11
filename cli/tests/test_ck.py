"""Tests for aux ck — Chidamber & Kemerer class-level metrics."""

from __future__ import annotations

from pathlib import Path

import pytest

from aux.kernels.ck import ck_kernel


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write(tmp_path: Path, source: str, name: str = "test.py") -> Path:
    f = tmp_path / name
    f.write_text(source)
    return tmp_path


def _by_name(result, name: str):
    for c in result.classes:
        if c.name == name:
            return c
    raise AssertionError(f"Class {name!r} not found in {[c.name for c in result.classes]}")


# ---------------------------------------------------------------------------
# 1. Basic schema / empty
# ---------------------------------------------------------------------------


def test_empty_directory_returns_empty(tmp_path: Path):
    result = ck_kernel(tmp_path)
    assert result.classes == []
    assert result.classes_analyzed == 0


def test_no_classes_in_file(tmp_path: Path):
    _write(tmp_path, "def foo():\n    pass\n")
    result = ck_kernel(tmp_path)
    assert result.classes == []


def test_unsupported_language_returns_error(tmp_path: Path):
    result = ck_kernel(tmp_path, languages=["cobol"])
    assert result.classes == []
    assert any("No supported" in e for e in result.errors)


# ---------------------------------------------------------------------------
# 2. Python class shapes
# ---------------------------------------------------------------------------


def test_single_class_no_deps(tmp_path: Path):
    _write(tmp_path, """\
class Alone:
    def method(self):
        pass
""")
    result = ck_kernel(tmp_path)
    assert len(result.classes) == 1
    c = result.classes[0]
    assert c.name == "Alone"
    assert c.cbo == 0
    assert c.dit == 0
    assert c.noc == 0
    assert c.method_count == 1
    assert c.kind == "class"
    assert c.superclasses == []


def test_two_coupled_classes(tmp_path: Path):
    _write(tmp_path, """\
class Dep:
    pass

class User:
    def method(self, x: Dep):
        d = Dep()
        return d
""")
    result = ck_kernel(tmp_path)
    user = _by_name(result, "User")
    dep = _by_name(result, "Dep")
    # User references Dep (type annotation + constructor call)
    assert user.cbo >= 1
    # Dep doesn't reference User
    assert dep.cbo == 0


def test_class_with_no_methods(tmp_path: Path):
    _write(tmp_path, """\
class Empty:
    pass
""")
    result = ck_kernel(tmp_path)
    c = _by_name(result, "Empty")
    assert c.method_count == 0
    assert c.wmc == 0


def test_nested_class(tmp_path: Path):
    _write(tmp_path, """\
class Outer:
    class Inner:
        def inner_method(self):
            pass
    def outer_method(self):
        pass
""")
    result = ck_kernel(tmp_path)
    outer = _by_name(result, "Outer")
    inner = _by_name(result, "Inner")
    assert inner.method_count == 1
    # Outer should have 1 method (outer_method), not include Inner's methods
    assert outer.method_count == 1


def test_class_referencing_multiple_classes(tmp_path: Path):
    _write(tmp_path, """\
class A:
    pass

class B:
    pass

class C:
    pass

class Hub:
    def method(self, a: A, b: B, c: C):
        pass
""")
    result = ck_kernel(tmp_path)
    hub = _by_name(result, "Hub")
    assert hub.cbo == 3  # A, B, C


# ---------------------------------------------------------------------------
# 3. Inheritance (DIT / NOC)
# ---------------------------------------------------------------------------


def test_linear_inheritance_chain(tmp_path: Path):
    _write(tmp_path, """\
class Base:
    pass

class Mid(Base):
    pass

class Leaf(Mid):
    pass
""")
    result = ck_kernel(tmp_path)
    base = _by_name(result, "Base")
    mid = _by_name(result, "Mid")
    leaf = _by_name(result, "Leaf")
    assert base.dit == 0
    assert mid.dit == 1
    assert leaf.dit == 2


def test_noc_counts_direct_children(tmp_path: Path):
    _write(tmp_path, """\
class Parent:
    pass

class Child1(Parent):
    pass

class Child2(Parent):
    pass

class Child3(Parent):
    pass
""")
    result = ck_kernel(tmp_path)
    parent = _by_name(result, "Parent")
    assert parent.noc == 3
    child = _by_name(result, "Child1")
    assert child.noc == 0


def test_diamond_inheritance(tmp_path: Path):
    _write(tmp_path, """\
class Base:
    pass

class Left(Base):
    pass

class Right(Base):
    pass

class Diamond(Left, Right):
    pass
""")
    result = ck_kernel(tmp_path)
    diamond = _by_name(result, "Diamond")
    # DIT should be 2 (Diamond → Left → Base or Diamond → Right → Base)
    assert diamond.dit == 2
    base = _by_name(result, "Base")
    assert base.noc == 2  # Left and Right


def test_unknown_parent_does_not_contribute_to_dit(tmp_path: Path):
    _write(tmp_path, """\
class Child(ExternalBase):
    pass
""")
    result = ck_kernel(tmp_path)
    child = _by_name(result, "Child")
    # ExternalBase is not in the registry → DIT stays 0
    assert child.dit == 0
    assert child.superclasses == ["ExternalBase"]


def test_superclass_counted_in_cbo(tmp_path: Path):
    _write(tmp_path, """\
class Parent:
    pass

class Child(Parent):
    pass
""")
    result = ck_kernel(tmp_path)
    child = _by_name(result, "Child")
    # Parent is a known class referenced via inheritance
    assert child.cbo >= 1


# ---------------------------------------------------------------------------
# 4. WMC (stubbed to 0 until Phase 2)
# ---------------------------------------------------------------------------


def test_wmc_sum_of_method_ccx(tmp_path: Path):
    _write(tmp_path, """\
class Foo:
    def simple(self):
        return 1

    def branchy(self):
        if True:
            pass
        if True:
            pass
        if True:
            pass
""")
    result = ck_kernel(tmp_path)
    foo = _by_name(result, "Foo")
    assert foo.method_count == 2
    # simple: ccx=1, branchy: ccx=4 (1 + 3 ifs)
    assert foo.wmc == 5


def test_wmc_zero_for_empty_class(tmp_path: Path):
    _write(tmp_path, """\
class Empty:
    pass
""")
    result = ck_kernel(tmp_path)
    c = _by_name(result, "Empty")
    assert c.wmc == 0


def test_wmc_nested_class_separate(tmp_path: Path):
    _write(tmp_path, """\
class Outer:
    def outer_method(self):
        if True:
            pass

    class Inner:
        def inner_method(self):
            return 1
""")
    result = ck_kernel(tmp_path)
    outer = _by_name(result, "Outer")
    inner = _by_name(result, "Inner")
    # outer_method: ccx=2, inner_method: ccx=1
    # Inner's method should NOT be counted in Outer's WMC
    assert inner.wmc == 1
    assert outer.wmc == 2  # only outer_method


# ---------------------------------------------------------------------------
# 5. Sorting and truncation
# ---------------------------------------------------------------------------


def test_sorted_by_cbo_desc(tmp_path: Path):
    _write(tmp_path, """\
class A:
    pass

class B:
    pass

class C:
    pass

class HighCBO:
    def method(self, a: A, b: B, c: C):
        pass

class LowCBO:
    pass
""")
    result = ck_kernel(tmp_path)
    assert result.classes[0].name == "HighCBO"
    assert result.classes[0].cbo == 3


def test_max_results_truncates(tmp_path: Path):
    source = "\n\n".join(f"class C{i}:\n    pass" for i in range(10))
    _write(tmp_path, source)
    result = ck_kernel(tmp_path, max_results=3)
    assert len(result.classes) == 3
    assert result.truncated is True


# ---------------------------------------------------------------------------
# 6. Interpretation
# ---------------------------------------------------------------------------


def test_interpretation_includes_metrics(tmp_path: Path):
    _write(tmp_path, """\
class Simple:
    def method(self):
        pass
""")
    result = ck_kernel(tmp_path)
    c = _by_name(result, "Simple")
    assert "CBO=" in c.interpretation
    assert "DIT=" in c.interpretation
    assert "NOC=" in c.interpretation
    assert "WMC=" in c.interpretation


# ---------------------------------------------------------------------------
# 5. Per-language tests
# ---------------------------------------------------------------------------


def test_java_class_with_inheritance(tmp_path: Path):
    (tmp_path / "test.java").write_text("""\
public class Animal {
    public void speak() {}
}

public class Dog extends Animal {
    public void speak() { return; }
    public void fetch(Animal target) {}
}
""")
    result = ck_kernel(tmp_path, languages=["java"])
    dog = _by_name(result, "Dog")
    animal = _by_name(result, "Animal")
    assert dog.superclasses == ["Animal"]
    assert dog.dit == 1
    assert dog.cbo >= 1  # references Animal
    assert animal.noc == 1  # Dog is its child
    assert dog.method_count == 2


def test_java_interface_counted(tmp_path: Path):
    (tmp_path / "test.java").write_text("""\
public interface Runnable {
    void run();
}

public class Worker implements Runnable {
    public void run() {}
}
""")
    result = ck_kernel(tmp_path, languages=["java"])
    assert any(c.name == "Runnable" and c.kind == "interface" for c in result.classes)
    worker = _by_name(result, "Worker")
    assert "Runnable" in worker.superclasses
    assert worker.cbo >= 1


def test_ts_class_extends_and_implements(tmp_path: Path):
    (tmp_path / "test.ts").write_text("""\
class Animal {
    speak(): void {}
}

interface Serializable {
    serialize(): string;
}

class Dog extends Animal {
    speak(): void {}
    fetch(target: Animal): void {}
}
""")
    result = ck_kernel(tmp_path, languages=["typescript"])
    dog = _by_name(result, "Dog")
    assert "Animal" in dog.superclasses
    assert dog.dit == 1
    assert dog.cbo >= 1


def test_ts_interface_enumerated(tmp_path: Path):
    (tmp_path / "test.ts").write_text("""\
interface Serializable {
    serialize(): string;
}
""")
    result = ck_kernel(tmp_path, languages=["typescript"])
    assert len(result.classes) == 1
    assert result.classes[0].kind == "interface"


def test_js_class_extends(tmp_path: Path):
    (tmp_path / "test.js").write_text("""\
class Animal {
    speak() {}
}

class Dog extends Animal {
    speak() { return 'woof'; }
}
""")
    result = ck_kernel(tmp_path, languages=["javascript"])
    dog = _by_name(result, "Dog")
    assert "Animal" in dog.superclasses
    assert dog.dit == 1
    assert dog.method_count == 1


def test_go_struct_with_methods(tmp_path: Path):
    (tmp_path / "test.go").write_text("""\
package main

type Animal struct {
    Name string
}

func (a *Animal) Speak() string {
    return ""
}

func (a *Animal) Move() {
}
""")
    result = ck_kernel(tmp_path, languages=["go"])
    assert len(result.classes) == 1
    animal = result.classes[0]
    assert animal.name == "Animal"
    assert animal.kind == "struct"
    assert animal.method_count == 2


def test_go_embedding_as_inheritance(tmp_path: Path):
    (tmp_path / "test.go").write_text("""\
package main

type Animal struct {
    Name string
}

type Dog struct {
    Animal
    Breed string
}
""")
    result = ck_kernel(tmp_path, languages=["go"])
    dog = _by_name(result, "Dog")
    assert "Animal" in dog.superclasses
    assert dog.dit == 1
    animal = _by_name(result, "Animal")
    assert animal.noc == 1


def test_go_pointer_receiver_matched(tmp_path: Path):
    (tmp_path / "test.go").write_text("""\
package main

type Foo struct {}

func (f *Foo) Bar() {}
func (f Foo) Baz() {}
""")
    result = ck_kernel(tmp_path, languages=["go"])
    foo = _by_name(result, "Foo")
    # Both pointer and value receivers should match
    assert foo.method_count == 2


def test_rust_struct_with_impl_methods(tmp_path: Path):
    (tmp_path / "test.rs").write_text("""\
struct Animal {
    name: String,
}

impl Animal {
    fn speak(&self) -> String {
        String::new()
    }
    fn move_to(&self, x: i32) {}
}
""")
    result = ck_kernel(tmp_path, languages=["rust"])
    assert len(result.classes) == 1
    animal = result.classes[0]
    assert animal.name == "Animal"
    assert animal.kind == "struct"
    assert animal.method_count == 2


def test_rust_trait_impl_as_coupling(tmp_path: Path):
    (tmp_path / "test.rs").write_text("""\
trait Runnable {
    fn run(&self);
}

struct Dog {
    name: String,
}

impl Runnable for Dog {
    fn run(&self) {}
}
""")
    result = ck_kernel(tmp_path, languages=["rust"])
    dog = _by_name(result, "Dog")
    assert "Runnable" in dog.superclasses
    assert dog.cbo >= 1


def test_rust_enum_counted(tmp_path: Path):
    (tmp_path / "test.rs").write_text("""\
enum Color {
    Red,
    Green,
    Blue,
}
""")
    result = ck_kernel(tmp_path, languages=["rust"])
    assert len(result.classes) == 1
    assert result.classes[0].name == "Color"
    assert result.classes[0].kind == "enum"


# ---------------------------------------------------------------------------
# 6. Interpretation
# ---------------------------------------------------------------------------


def test_interpretation_flags_high_coupling(tmp_path: Path):
    # Create > 8 classes and one class that references them all
    classes = [f"class Dep{i}:\n    pass" for i in range(10)]
    refs = ", ".join(f"d{i}: Dep{i}" for i in range(10))
    classes.append(f"class HighCoupling:\n    def m(self, {refs}):\n        pass")
    _write(tmp_path, "\n\n".join(classes))
    result = ck_kernel(tmp_path)
    hc = _by_name(result, "HighCoupling")
    assert hc.cbo >= 9
    assert "high coupling" in hc.interpretation.lower()
