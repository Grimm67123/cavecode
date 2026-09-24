"""
Tests for CaveCode safety and source file integrity guarantees.
"""

from pathlib import Path
import pytest

from cavecode.engine import CaveCodeEngine
from cavecode.safety import SafetyGuard, SafetyViolationError


def test_single_file_target_untouched(tmp_path: Path):
    src_file = tmp_path / "app.py"
    initial_content = """# Inviolate source file
def add(a, b):
    # Sum logic
    return a + b
"""
    src_file.write_text(initial_content, encoding="utf-8")
    initial_hash = SafetyGuard.compute_sha256(src_file)

    engine = CaveCodeEngine()
    dest, estimate = engine.compress_single_file(src_file)

    # 1. Output destination was created
    assert dest.exists()
    assert dest != src_file

    # 2. Original target file is 100% UNTOUCHED
    current_content = src_file.read_text(encoding="utf-8")
    current_hash = SafetyGuard.compute_sha256(src_file)

    assert current_content == initial_content
    assert current_hash == initial_hash


def test_directory_targets_untouched(tmp_path: Path):
    proj_dir = tmp_path / "project"
    proj_dir.mkdir()

    f1 = proj_dir / "main.go"
    f1.write_text('package main\nimport ("fmt")\nfunc main() { fmt.Println("ok") }', encoding="utf-8")

    f2 = proj_dir / "User.java"
    f2.write_text('public class User { private String name; public String getName() { return this.name; } }', encoding="utf-8")

    guard = SafetyGuard([f1, f2])

    engine = CaveCodeEngine()
    bundle_path, estimate, count = engine.pack_directory(proj_dir)

    assert bundle_path.exists()
    assert count == 2

    is_safe, violations = guard.verify_untouched()
    assert is_safe is True
    assert len(violations) == 0


def test_in_place_overwrite_prevented(tmp_path: Path):
    src = tmp_path / "test.py"
    src.write_text("x = 1", encoding="utf-8")

    engine = CaveCodeEngine()
    with pytest.raises(SafetyViolationError):
        engine.compress_single_file(src, output_file=src)
