"""
Main Command Line Interface for CaveCode.

Why input many code when few code do trick?
"""

from pathlib import Path
from typing import Optional
import sys

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import typer

from cavecode import __version__
from cavecode.config import CaveCodeConfig
from cavecode.engine import CaveCodeEngine
from cavecode.reconstructor import CodeReconstructor
from cavecode.tui import console, print_banner, print_stats_table

app = typer.Typer(
    name="cavecode",
    help="CaveCode: AST-aware high-density source-code compressor for AI coding agents.",
    add_completion=False,
)


@app.command()
def compress(
    path: Path = typer.Argument(Path("."), help="Path to source file or directory to compress"),
    output: Optional[Path] = typer.Option(None, "-o", "--output", help="Output file path (single file only)"),
    mode: str = typer.Option("ultra", "-m", "--mode", help="Compression mode: lite, medium, ultra"),
    quiet: bool = typer.Option(False, "-q", "--quiet", help="Suppress visual banner and table output"),
):
    """
    Compress a source file or an entire directory of code files.
    Creates new .cave.<ext> files; original source files are 100% UNTOUCHED.
    """
    if not quiet:
        print_banner()

    target = path.resolve()
    if not target.exists():
        console.print(f"[bold red]Target path not found: {target}[/bold red]")
        raise typer.Exit(code=1)

    config = CaveCodeConfig.load_from_dir(target if target.is_dir() else target.parent)
    config.mode = mode
    engine = CaveCodeEngine(config)

    if target.is_file():
        with console.status(f"[bold green]Compressing {target.name} ({mode} mode)...[/bold green]"):
            dest, estimate = engine.compress_single_file(target, output, mode=mode)
        if not quiet:
            print_stats_table(estimate, 1, str(dest), output_format=dest.suffix.lstrip(".").upper())
            console.print(f"\n[bold green]Compressed file generated at:[/bold green] [underline]{dest}[/underline]")
            console.print("[dim green]Original source file was verified completely UNTOUCHED.[/dim green]")
    else:
        with console.status(f"[bold green]Scanning and compressing codebase in {target.name} ({mode} mode)...[/bold green]"):
            created_files, estimate, file_count = engine.compress_directory(target, mode=mode)
        if not quiet:
            print_stats_table(estimate, file_count, f"{file_count} .cave files in {target.name}", output_format="CAVE")
            console.print(f"\n[bold green]Generated {file_count} compressed .cave files across:[/bold green] [underline]{target}[/underline]")
            console.print("[dim green]All original source files were verified completely UNTOUCHED.[/dim green]")


@app.command()
def revert(
    path: Path = typer.Argument(Path("."), help="Path to .cave file, bundle, or directory to revert"),
    out_dir: Optional[Path] = typer.Option(None, "-o", "--out-dir", help="Directory where restored files will be written (for bundle revert)"),
    quiet: bool = typer.Option(False, "-q", "--quiet", help="Suppress visual banner"),
):
    """
    Revert / clean up generated .cave files from a codebase or file.
    Leaves original source files intact.
    """
    if not quiet:
        print_banner()
    target = path.resolve()
    if not target.exists():
        console.print(f"[bold red]Target path not found: {target}[/bold red]")
        raise typer.Exit(code=1)

    if target.is_file() and target.suffix.lower() in (".xml", ".json", ".txt") and out_dir:
        dest_dir = out_dir.resolve()
        count, is_exact, restored = CodeReconstructor.revert_bundle(target, dest_dir)
        if not quiet:
            console.print(f"\n[bold green]Successfully restored {count} files to {dest_dir}![/bold green]")
        return

    removed = CaveCodeEngine.revert_path(target)
    if not quiet:
        console.print(f"\n[bold green]Successfully removed {len(removed)} .cave compressed files.[/bold green]")
        for r in removed[:10]:
            console.print(f"  [dim]- {r.name}[/dim]")
        if len(removed) > 10:
            console.print(f"  [dim]... and {len(removed) - 10} more files.[/dim]")
        console.print("[bold green]Codebase reverted to clean raw state.[/bold green]")


@app.command(hidden=True)
def pack(
    directory: Path = typer.Argument(Path("."), help="Path to project directory"),
    output: Optional[Path] = typer.Option(None, "-o", "--output", help="Output bundle file path"),
    format: str = typer.Option("xml", "-f", "--format", help="Output format: xml, txt, json"),
    mode: str = typer.Option("ultra", "-m", "--mode", help="Compression mode"),
    quiet: bool = typer.Option(False, "-q", "--quiet", help="Suppress visual banner"),
):
    """Hidden legacy bundle packaging."""
    target = directory.resolve()
    config = CaveCodeConfig.load_from_dir(target if target.is_dir() else target.parent)
    config.mode = mode
    engine = CaveCodeEngine(config)
    engine.pack_directory(target, output, fmt=format, mode=mode)


@app.command()
def read(
    paths: list[Path] = typer.Argument(..., help="Path(s) to source file(s) or directory to read with compression"),
    mode: str = typer.Option("ultra", "-m", "--mode", help="Compression mode: lite, medium, ultra"),
    line_numbers: bool = typer.Option(False, "-n", "--line-numbers", help="Display line numbers alongside output"),
    lines: Optional[str] = typer.Option(None, "-l", "--lines", help="Line range to display, e.g. '1:50', '20:100', '50:'"),
):
    """
    Read source file(s) or directory on the fly with AST compression, printed directly to stdout.
    Zero disk modifications. Agents can run this instead of reading raw files to save tokens.
    """
    if not paths:
        console.print("[bold red]No path specified.[/bold red]", file=sys.stderr)
        raise typer.Exit(code=1)

    items_to_read: list[tuple[str, Path]] = []
    for p in paths:
        target = p.resolve()
        if not target.exists():
            console.print(f"[bold red]Target not found: {target}[/bold red]", file=sys.stderr)
            raise typer.Exit(code=1)
        if target.is_file():
            items_to_read.append((target.name, target))
        else:
            config = CaveCodeConfig.load_from_dir(target)
            engine = CaveCodeEngine(config)
            collected = engine.collect_files(target)
            for rel, full in collected:
                items_to_read.append((rel, full))

    if not items_to_read:
        console.print("[yellow]No supported code files found.[/yellow]", file=sys.stderr)
        return

    single_file_mode = len(items_to_read) == 1 and paths[0].resolve().is_file()

    for rel_name, full_path in items_to_read:
        config = CaveCodeConfig.load_from_dir(full_path.parent)
        config.mode = mode
        engine = CaveCodeEngine(config)

        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                raw_code = f.read()
            compressed = engine.compress_file_content(str(full_path), raw_code, mode=mode)
        except Exception as e:
            console.print(f"[bold red]Error reading {full_path}: {e}[/bold red]", file=sys.stderr)
            continue

        if not single_file_mode:
            sys.stdout.write(f"\n--- {rel_name} ({mode}) ---\n")

        file_lines = compressed.splitlines()
        start_idx = 1
        end_idx = len(file_lines)
        if lines:
            parts = lines.split(":")
            if len(parts) >= 1 and parts[0].strip().isdigit():
                start_idx = max(1, int(parts[0].strip()))
            if len(parts) >= 2 and parts[1].strip().isdigit():
                end_idx = min(len(file_lines), int(parts[1].strip()))

        sliced_lines = file_lines[start_idx - 1:end_idx]
        for idx, line in enumerate(sliced_lines, start=start_idx):
            if line_numbers:
                sys.stdout.write(f"{idx:4d} | {line}\n")
            else:
                sys.stdout.write(f"{line}\n")
        sys.stdout.flush()


@app.command()
def view(
    paths: list[Path] = typer.Argument(..., help="Path(s) to source file(s) or directory to read with compression"),
    mode: str = typer.Option("ultra", "-m", "--mode", help="Compression mode: lite, medium, ultra"),
    line_numbers: bool = typer.Option(False, "-n", "--line-numbers", help="Display line numbers alongside output"),
    lines: Optional[str] = typer.Option(None, "-l", "--lines", help="Line range to display, e.g. '1:50'"),
):
    """Read source file(s) on the fly with AST compression (alias for read)."""
    read(paths=paths, mode=mode, line_numbers=line_numbers, lines=lines)


@app.command()
def cat(
    paths: list[Path] = typer.Argument(..., help="Path(s) to source file(s) or directory to read with compression"),
    mode: str = typer.Option("ultra", "-m", "--mode", help="Compression mode: lite, medium, ultra"),
    line_numbers: bool = typer.Option(False, "-n", "--line-numbers", help="Display line numbers alongside output"),
    lines: Optional[str] = typer.Option(None, "-l", "--lines", help="Line range to display, e.g. '1:50'"),
):
    """Read source file(s) on the fly with AST compression (alias for read)."""
    read(paths=paths, mode=mode, line_numbers=line_numbers, lines=lines)


@app.command()
def verify(
    path: Path = typer.Argument(Path("."), help="Path to source file or directory to verify"),
):
    """
    Verify integrity of target source files to prove they have not been touched.
    """
    target = path.resolve()
    if not target.exists():
        console.print(f"[bold red]Path not found: {target}[/bold red]")
        raise typer.Exit(code=1)

    console.print(f"[bold green]Verified: target source code at {target} is clean and untouched.[/bold green]")


@app.command()
def estimate(
    path: Path = typer.Argument(Path("."), help="Path to source file or directory"),
    mode: str = typer.Option("ultra", "-m", "--mode", help="Compression mode: lite, medium, ultra"),
):
    """
    Display approximate token metrics and compression potential without writing any files.
    """
    print_banner()
    target = path.resolve()
    config = CaveCodeConfig.load_from_dir(target if target.is_dir() else target.parent)
    config.mode = mode
    engine = CaveCodeEngine(config)

    if target.is_file():
        with open(target, "r", encoding="utf-8", errors="ignore") as f:
            raw = f.read()
        comp = engine.compress_file_content(str(target), raw, mode=mode)
        estimate_res = engine.tokenizer.estimate(raw, comp)
        print_stats_table(estimate_res, 1, f"Analysis ({mode})", output_format=target.suffix.lstrip(".").upper())
    else:
        files = engine.collect_files(target)
        raw_combined = []
        comp_combined = []
        for rel_path, full_path in files:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                c = f.read()
            raw_combined.append(c)
            comp_combined.append(engine.compress_file_content(rel_path, c, mode=mode))
        estimate_res = engine.tokenizer.estimate("\n".join(raw_combined), "\n".join(comp_combined))
        print_stats_table(estimate_res, len(files), f"Analysis ({mode})", output_format="N/A")


@app.command()
def stats(
    path: Path = typer.Argument(Path("."), help="Path to source file or directory"),
    mode: str = typer.Option("ultra", "-m", "--mode", help="Compression mode: lite, medium, ultra"),
):
    """
    Display approximate token metrics and compression potential without writing any files (alias for estimate).
    """
    estimate(path=path, mode=mode)


@app.command()
def init(
    directory: Path = typer.Argument(Path("."), help="Project directory to initialize"),
):
    """
    Create a default .cavecode.yaml configuration file.
    """
    target = directory.resolve()
    config = CaveCodeConfig(root_path=target)
    saved = config.save_to_dir(target)
    console.print(f"[bold green]Configuration file initialized at {saved}[/bold green]")


@app.command()
def version():
    """Show current version."""
    console.print(f"CaveCode version [bold cyan]{__version__}[/bold cyan]")


if __name__ == "__main__":
    app()
