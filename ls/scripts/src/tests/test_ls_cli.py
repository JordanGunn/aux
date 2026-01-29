import json
import os
import tempfile
import unittest
from pathlib import Path

from cli import _compute_inventory, _parse_git_porcelain_v1_z, _parse_plan


class TestLsCli(unittest.TestCase):
    def _make_tree(self, root: Path) -> None:
        (root / "a").mkdir()
        (root / "a" / "f1.txt").write_text("hello", encoding="utf-8")
        (root / "a" / "f2.py").write_text("print('x')\n", encoding="utf-8")
        (root / ".hidden").write_text("h", encoding="utf-8")
        (root / "b").mkdir()
        (root / "b" / "nested.md").write_text("md", encoding="utf-8")
        # Symlink: should be recorded but never traversed.
        try:
            os.symlink(str(root / "a"), str(root / "link_to_a"))
        except OSError:
            # Some environments disallow symlinks; tests that rely on traversal still pass.
            pass

    def _plan_obj(self, *, root: Path, include_hidden: bool, max_entries_scanned: int, top_n: int) -> dict:
        return {
            "schema": "ls_plan_v1",
            "ls": {
                "root": str(root),
                "depth": 2,
                "view": "flat",
                "sort": "name",
                "order": "asc",
                "top_n": top_n,
                "include_hidden": include_hidden,
                "classify": {"by_extension": True, "by_coarse_type": True},
                "git_status": "off",
                "limits": {"max_entries_scanned": max_entries_scanned, "max_bytes_view": 100000},
            },
        }

    def test_determinism_two_runs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._make_tree(root)

            plan = _parse_plan(self._plan_obj(root=root, include_hidden=False, max_entries_scanned=1000, top_n=1000))
            cfg = type("Cfg", (), {"caps": {"max_depth": 128, "max_entries_scanned": 1000000, "max_top_n": 100000, "max_view_bytes": 10485760}})()
            aux_dir = root / ".aux" / "ls"
            aux_dir.mkdir(parents=True, exist_ok=True)

            inv1, rec1, view1 = _compute_inventory(plan, cfg, aux_dir)
            inv2, rec2, view2 = _compute_inventory(plan, cfg, aux_dir)

            self.assertEqual(json.dumps(inv1, sort_keys=True), json.dumps(inv2, sort_keys=True))
            self.assertEqual(json.dumps(rec1, sort_keys=True), json.dumps(rec2, sort_keys=True))
            self.assertEqual(view1, view2)

    def test_include_hidden_affects_scan(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._make_tree(root)

            cfg = type("Cfg", (), {"caps": {"max_depth": 128, "max_entries_scanned": 1000000, "max_top_n": 100000, "max_view_bytes": 10485760}})()
            aux_dir = root / ".aux" / "ls"
            aux_dir.mkdir(parents=True, exist_ok=True)

            p_no = _parse_plan(self._plan_obj(root=root, include_hidden=False, max_entries_scanned=1000, top_n=1000))
            inv_no, _, _ = _compute_inventory(p_no, cfg, aux_dir)
            paths_no = {e["path"] for e in inv_no["entries"]}
            self.assertNotIn(".hidden", paths_no)

            p_yes = _parse_plan(self._plan_obj(root=root, include_hidden=True, max_entries_scanned=1000, top_n=1000))
            inv_yes, _, _ = _compute_inventory(p_yes, cfg, aux_dir)
            paths_yes = {e["path"] for e in inv_yes["entries"]}
            self.assertIn(".hidden", paths_yes)

    def test_scan_truncation_flag(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._make_tree(root)

            cfg = type("Cfg", (), {"caps": {"max_depth": 128, "max_entries_scanned": 1000000, "max_top_n": 100000, "max_view_bytes": 10485760}})()
            aux_dir = root / ".aux" / "ls"
            aux_dir.mkdir(parents=True, exist_ok=True)

            plan = _parse_plan(self._plan_obj(root=root, include_hidden=True, max_entries_scanned=1, top_n=1000))
            _, receipt, _ = _compute_inventory(plan, cfg, aux_dir)
            self.assertTrue(receipt["truncation"]["scan_truncated"])

    def test_git_porcelain_parse_rename(self) -> None:
        out = b"R  old.txt\0new.txt\0 M file.py\0"
        m = _parse_git_porcelain_v1_z(out)
        self.assertIn("new.txt", m)
        self.assertEqual(m["new.txt"][0], "R ")
        self.assertEqual(m["new.txt"][1], "old.txt")
        self.assertIn("file.py", m)
        self.assertEqual(m["file.py"][0], " M")
        self.assertIsNone(m["file.py"][1])


if __name__ == "__main__":
    unittest.main()
