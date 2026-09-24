"""
Tests for CaveCode bundle reversion and reconstruction.
"""

from pathlib import Path
from cavecode.engine import CaveCodeEngine
from cavecode.reconstructor import CodeReconstructor
from cavecode.config import CaveCodeConfig


def test_roundtrip_revert_xml(tmp_path: Path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    f1 = src_dir / "math.py"
    content1 = "# Python math module\ndef square(n):\n    return n * n\n"
    f1.write_text(content1, encoding="utf-8")

    f2 = src_dir / "service.go"
    content2 = '// Go handler\npackage main\nfunc Run() int {\n    return 42\n}\n'
    f2.write_text(content2, encoding="utf-8")

    bundle_dest = tmp_path / "bundle.xml"
    engine = CaveCodeEngine()
    engine.pack_directory(src_dir, output_file=bundle_dest, fmt="xml")

    assert bundle_dest.exists()

    restore_dir = tmp_path / "restored"
    count, is_exact, restored = CodeReconstructor.revert_bundle(bundle_dest, restore_dir)

    assert count == 2
    assert is_exact is True

    restored_f1 = restore_dir / "math.py"
    restored_f2 = restore_dir / "service.go"

    assert restored_f1.exists()
    assert restored_f2.exists()
    assert restored_f1.read_text(encoding="utf-8") == content1
    assert restored_f2.read_text(encoding="utf-8") == content2


def test_roundtrip_revert_txt(tmp_path: Path):
    src_dir = tmp_path / "src_txt"
    src_dir.mkdir()

    f1 = src_dir / "main.rs"
    content1 = '// Rust main\nfn main() {\n    println!("hello");\n}\n'
    f1.write_text(content1, encoding="utf-8")

    bundle_dest = tmp_path / "bundle.txt"
    engine = CaveCodeEngine()
    engine.pack_directory(src_dir, output_file=bundle_dest, fmt="txt")

    assert bundle_dest.exists()

    restore_dir = tmp_path / "restored_txt"
    count, is_exact, restored = CodeReconstructor.revert_bundle(bundle_dest, restore_dir)

    assert count == 1
    assert is_exact is True
    assert (restore_dir / "main.rs").read_text(encoding="utf-8") == content1


def test_roundtrip_revert_json(tmp_path: Path):
    src_dir = tmp_path / "src_json"
    src_dir.mkdir()

    f1 = src_dir / "index.ts"
    content1 = '// TS file\nexport const x: number = 100;\n'
    f1.write_text(content1, encoding="utf-8")

    bundle_dest = tmp_path / "bundle.json"
    engine = CaveCodeEngine()
    engine.pack_directory(src_dir, output_file=bundle_dest, fmt="json")

    assert bundle_dest.exists()

    restore_dir = tmp_path / "restored_json"
    count, is_exact, restored = CodeReconstructor.revert_bundle(bundle_dest, restore_dir)

    assert count == 1
    assert is_exact is True
    assert (restore_dir / "index.ts").read_text(encoding="utf-8") == content1
