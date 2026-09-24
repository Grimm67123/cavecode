"""
Rich Terminal Interface and Formatting for CaveCode.
"""

import os
import sys
from rich.console import Console
from rich.table import Table

from cavecode.tokenizer import TokenEstimate

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

console = Console(force_terminal=True if os.getenv("CI") else None)

BANNER_TEXT = r"""
   ______                   ______          __   
  / ____/___ __   _____    / ____/___  ____/ /__ 
 / /   / __ `/ | / / _ \  / /   / __ \/ __  / _ \
/ /___/ /_/ /| |/ /  __/ / /___/ /_/ / /_/ /  __/
\____/\__,_/ |___/\___/  \____/\____/\__,_/\___/ 
  Why Input Many Code When Few Code Do Trick?
"""


def print_banner():
    """Print the CaveCode banner."""
    console.print(f"[bold cyan]{BANNER_TEXT}[/bold cyan]")
    console.print("[dim]v1.0.0 | High-Density Source-Code Compressor | Original Files Untouched[/dim]\n")


def print_stats_table(
    estimate: TokenEstimate,
    file_count: int,
    output_path: str,
    output_format: str = "XML",
):
    """Print comparative approximate token savings and safety metrics table."""
    summary_table = Table(
        title="CaveCode Compression & Token Metrics",
        show_header=True,
        header_style="bold magenta",
    )
    summary_table.add_column("Metric", style="dim", width=26)
    summary_table.add_column("Value", justify="right")

    summary_table.add_row("Processed Files", f"[bold green]{file_count}[/bold green]")
    summary_table.add_row("Raw Tokens (approx.)", f"~{estimate.raw_approx_tokens:,}")
    summary_table.add_row(
        "Compressed Tokens (approx.)",
        f"[bold cyan]~{estimate.compressed_approx_tokens:,}[/bold cyan]",
    )
    summary_table.add_row(
        "Tokens Saved (approx.)",
        f"[bold green]~{estimate.saved_approx_tokens:,}[/bold green]",
    )
    summary_table.add_row(
        "Estimated Reduction",
        f"[bold yellow]~{estimate.percent_saved}%[/bold yellow]",
    )
    summary_table.add_row("Target Source Files", "[bold green]100% UNTOUCHED[/bold green]")
    summary_table.add_row("Output Format", output_format.upper())
    summary_table.add_row("Output Bundle", output_path)

    console.print(summary_table)

    if estimate.model_estimates:
        arch_table = Table(
            title="Approximate Tokens by Tokenizer Architecture",
            show_header=True,
            header_style="bold green",
        )
        arch_table.add_column("Tokenizer Architecture", style="bold")
        arch_table.add_column("Raw Load (approx.)", justify="right")
        arch_table.add_column("Compressed Load (approx.)", justify="right")
        arch_table.add_column("Savings (approx.)", justify="right", style="bold green")

        for arch_name, data in estimate.model_estimates.items():
            saved = data["raw"] - data["compressed"]
            arch_table.add_row(
                arch_name,
                f"~{data['raw']:,}",
                f"~{data['compressed']:,}",
                f"-~{saved:,}",
            )

        console.print(arch_table)
