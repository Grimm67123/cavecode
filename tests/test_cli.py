"""
Tests for CaveCode CLI commands.
"""

from pathlib import Path
from typer.testing import CliRunner

from cavecode.cli import app

runner = CliRunner()


def test_cli_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "CaveCode version" in result.output


def test_cli_compress_single_file(tmp_path: Path):
    f = tmp_path / "hello.py"
    f.write_text("# Test script\ndef hello():\n    return 'world'\n", encoding="utf-8")

    out = tmp_path / "hello.out.py"
    result = runner.invoke(app, ["compress", str(f), "-o", str(out), "-q"])
    assert result.exit_code == 0
    assert out.exists()
    assert f.read_text(encoding="utf-8") == "# Test script\ndef hello():\n    return 'world'\n"


def test_cli_pack_and_revert(tmp_path: Path):
    src = tmp_path / "app"
    src.mkdir()
    (src / "test.java").write_text("public class App { private int x; public int getX() { return this.x; } }", encoding="utf-8")

    bundle = tmp_path / "out.xml"
    res_pack = runner.invoke(app, ["pack", str(src), "-o", str(bundle), "-q"])
    assert res_pack.exit_code == 0
    assert bundle.exists()

    restored = tmp_path / "restored"
    res_revert = runner.invoke(app, ["revert", str(bundle), "-o", str(restored)])
    assert res_revert.exit_code == 0
    assert (restored / "test.java").exists()


def test_cli_verify(tmp_path: Path):
    p = tmp_path / "demo.py"
    p.write_text("a = 1", encoding="utf-8")
    result = runner.invoke(app, ["verify", str(p)])
    assert result.exit_code == 0
    assert "clean and untouched" in result.output


def test_cli_stats(tmp_path: Path):
    p = tmp_path / "calc.py"
    p.write_text("def f(x):\n    return x * 2\n", encoding="utf-8")
    result = runner.invoke(app, ["stats", str(p)])
    assert result.exit_code == 0
    assert "Raw Tokens (approx.)" in result.output


def test_cli_init(tmp_path: Path):
    result = runner.invoke(app, ["init", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / ".cavecode.yaml").exists()


def test_cli_compress_directory_and_revert(tmp_path: Path):
    d = tmp_path / "project"
    d.mkdir()
    f1 = d / "a.py"
    f1.write_text("def add(x, y):\n    return x + y\n", encoding="utf-8")
    f2 = d / "b.ts"
    f2.write_text("export function sub(x: number, y: number): number { return x - y; }", encoding="utf-8")

    res_comp = runner.invoke(app, ["compress", str(d), "-m", "ultra", "-q"])
    assert res_comp.exit_code == 0
    assert (d / "a.cave.py").exists()
    assert (d / "b.cave.ts").exists()
    assert f1.read_text(encoding="utf-8") == "def add(x, y):\n    return x + y\n"

    res_rev = runner.invoke(app, ["revert", str(d), "-q"])
    assert res_rev.exit_code == 0
    assert not (d / "a.cave.py").exists()
    assert not (d / "b.cave.ts").exists()
    assert f1.exists()
    assert f2.exists()


def test_cli_read_single_file_on_the_fly(tmp_path: Path):
    f = tmp_path / "service.py"
    f.write_text("def compute(x: int) -> int:\n    # expensive math\n    return x * 42\n", encoding="utf-8")

    # Ultra mode: prints signature and stubs
    res_ultra = runner.invoke(app, ["read", str(f), "-m", "ultra"])
    assert res_ultra.exit_code == 0
    assert "fn compute" in res_ultra.output or "compute" in res_ultra.output
    # Verify no file written to disk
    assert not (tmp_path / "service.cave.py").exists()

    # Lite mode: prints 100% full implementation logic
    res_lite = runner.invoke(app, ["read", str(f), "-m", "lite"])
    assert res_lite.exit_code == 0
    assert "return x * 42" in res_lite.output or "ret x * 42" in res_lite.output
    assert not (tmp_path / "service.cave.py").exists()


def test_cli_read_with_line_numbers(tmp_path: Path):
    f = tmp_path / "hello.ts"
    f.write_text("export function greet(): string { return 'hello'; }", encoding="utf-8")

    res = runner.invoke(app, ["read", str(f), "-m", "lite", "-n"])
    assert res.exit_code == 0
    assert "1 |" in res.output


def test_cli_read_directory(tmp_path: Path):
    d = tmp_path / "pkg"
    d.mkdir()
    (d / "mod1.py").write_text("def f1():\n    return 1\n", encoding="utf-8")
    (d / "mod2.py").write_text("def f2():\n    return 2\n", encoding="utf-8")

    res = runner.invoke(app, ["read", str(d), "-m", "ultra"])
    assert res.exit_code == 0
    assert "mod1.py" in res.output
    assert "mod2.py" in res.output


def test_cli_view_and_cat_aliases(tmp_path: Path):
    f = tmp_path / "app.py"
    f.write_text("def run():\n    return True\n", encoding="utf-8")

    res_view = runner.invoke(app, ["view", str(f), "-m", "lite"])
    assert res_view.exit_code == 0

    res_cat = runner.invoke(app, ["cat", str(f), "-m", "lite"])
    assert res_cat.exit_code == 0
    assert res_view.output == res_cat.output


def test_cli_read_line_range_slice(tmp_path: Path):
    f = tmp_path / "long_file.py"
    lines = [f"def func_{i}():\n    return {i}\n" for i in range(10)]
    f.write_text("\n".join(lines), encoding="utf-8")

    res = runner.invoke(app, ["read", str(f), "-m", "lite", "-l", "1:3", "-n"])
    assert res.exit_code == 0
    assert "1 |" in res.output
    assert "3 |" in res.output
    assert "4 |" not in res.output


