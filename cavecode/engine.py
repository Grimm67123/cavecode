"""
High-Level Orchestration Engine for CaveCode.

Coordinates multi-language AST compression, file discovery, safety verification,
and bundle generation.
"""

import fnmatch
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from cavecode.config import (
    CaveCodeConfig,
    EXTENSION_TO_LANGUAGE,
    SUPPORTED_EXTENSIONS,
)
from cavecode.compressors import get_compressor
from cavecode.safety import SafetyGuard, SafetyViolationError
from cavecode.formatter import OutputFormatter
from cavecode.tokenizer import TokenEstimator, TokenEstimate


class CaveCodeEngine:
    """Core engine for compressing source files and codebases."""

    def __init__(self, config: Optional[CaveCodeConfig] = None):
        self.config = config or CaveCodeConfig()
        self.tokenizer = TokenEstimator()

    @staticmethod
    def should_exclude(rel_path: str, excludes: List[str]) -> bool:
        """Check if relative path matches any exclusion patterns."""
        normalized = rel_path.replace("\\", "/")
        parts = normalized.split("/")
        for pattern in excludes:
            for part in parts:
                if fnmatch.fnmatch(part, pattern):
                    return True
            if fnmatch.fnmatch(normalized, pattern):
                return True
        return False

    def collect_files(self, root: Path) -> List[Tuple[str, Path]]:
        """
        Recursively discover all compatible source files within a directory.
        Returns list of (rel_path_str, absolute_Path).
        """
        collected = []
        root_resolved = root.resolve()

        for dirpath, dirnames, filenames in os.walk(root_resolved):
            rel_dir = os.path.relpath(dirpath, root_resolved)
            if rel_dir != "." and self.should_exclude(rel_dir, self.config.excludes):
                dirnames.clear()
                continue

            dirnames[:] = [d for d in dirnames if not self.should_exclude(d, self.config.excludes)]

            for fname in filenames:
                rel_file = os.path.normpath(
                    os.path.join(rel_dir if rel_dir != "." else "", fname)
                ).replace("\\", "/")

                if self.should_exclude(rel_file, self.config.excludes):
                    continue

                full_path = Path(dirpath) / fname
                ext = full_path.suffix.lower()

                if ext not in SUPPORTED_EXTENSIONS and not self.config.includes:
                    continue

                try:
                    if full_path.stat().st_size > self.config.max_file_size_kb * 1024:
                        continue
                    collected.append((rel_file, full_path))
                except Exception:
                    continue

        return collected

    def compress_file_content(
        self, file_path_str: str, content: str, mode: Optional[str] = None
    ) -> str:
        """Compress source code based on its file extension and mode."""
        ext = Path(file_path_str).suffix.lower()
        lang = EXTENSION_TO_LANGUAGE.get(ext)
        if not lang:
            return content

        mode_chosen = mode or self.config.mode
        compressor = get_compressor(lang)
        return compressor.compress(content, mode=mode_chosen)

    def compress_single_file(
        self,
        input_file: Path,
        output_file: Optional[Path] = None,
        mode: Optional[str] = None,
    ) -> Tuple[Path, TokenEstimate]:
        """
        Compress a single target file and write to output_file.
        The original target file is guaranteed to remain 100% UNTOUCHED.
        """
        input_resolved = input_file.resolve()
        if not input_resolved.is_file():
            raise FileNotFoundError(f"Source file not found: {input_file}")

        dest = output_file or input_resolved.with_name(
            f"{input_resolved.stem}.cave{input_resolved.suffix}"
        )
        dest_resolved = dest.resolve()

        SafetyGuard.assert_safe_destination(input_resolved, dest_resolved)

        guard = SafetyGuard([input_resolved])

        with open(input_resolved, "r", encoding="utf-8", errors="ignore") as f:
            raw_content = f.read()

        mode_chosen = mode or self.config.mode
        compressed_content = self.compress_file_content(
            str(input_resolved), raw_content, mode=mode_chosen
        )

        dest_resolved.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_resolved, "w", encoding="utf-8") as f:
            f.write(compressed_content)

        is_safe, violations = guard.verify_untouched()
        if not is_safe:
            raise SafetyViolationError(f"Safety invariant failed: {violations}")

        estimate = self.tokenizer.estimate(raw_content, compressed_content)
        return dest_resolved, estimate

    def compress_directory(
        self,
        directory: Path,
        mode: Optional[str] = None,
    ) -> Tuple[List[Path], TokenEstimate, int]:
        """
        Compress all compatible files in a directory and write corresponding .cave.<ext> files.
        Original files are guaranteed to remain 100% UNTOUCHED.
        """
        root_resolved = directory.resolve()
        target_files = self.collect_files(root_resolved)

        if not target_files:
            raise ValueError(f"No compatible source files found in {directory}")

        mode_chosen = mode or self.config.mode
        all_paths = [p for _, p in target_files]
        guard = SafetyGuard(all_paths)

        raw_all = []
        comp_all = []
        created_paths = []

        for rel_path, full_path in target_files:
            dest = full_path.with_name(f"{full_path.stem}.cave{full_path.suffix}")
            SafetyGuard.assert_safe_destination(full_path, dest)

            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            raw_all.append(content)
            comp = self.compress_file_content(rel_path, content, mode=mode_chosen)
            comp_all.append(comp)

            with open(dest, "w", encoding="utf-8") as f:
                f.write(comp)
            created_paths.append(dest)

        is_safe, violations = guard.verify_untouched()
        if not is_safe:
            raise SafetyViolationError(f"Safety invariant violated: {violations}")

        estimate = self.tokenizer.estimate("\n".join(raw_all), "\n".join(comp_all))
        return created_paths, estimate, len(created_paths)

    @staticmethod
    def revert_path(path: Path) -> List[Path]:
        """
        Remove generated .cave files to clean/revert codebase.
        Returns list of removed .cave file paths.
        """
        p = path.resolve()
        removed = []
        if p.is_file():
            if ".cave" in p.name:
                p.unlink(missing_ok=True)
                removed.append(p)
            else:
                cave_cand = p.with_name(f"{p.stem}.cave{p.suffix}")
                if cave_cand.exists():
                    cave_cand.unlink(missing_ok=True)
                    removed.append(cave_cand)
        else:
            for root, _, files in os.walk(p):
                for f in files:
                    if ".cave" in f:
                        file_p = Path(root) / f
                        file_p.unlink(missing_ok=True)
                        removed.append(file_p)
        return removed

    def pack_directory(
        self,
        directory: Path,
        output_file: Optional[Path] = None,
        fmt: Optional[str] = None,
        mode: Optional[str] = None,
    ) -> Tuple[Path, TokenEstimate, int]:
        """
        Compress all compatible files in a directory and package them into a bundle.
        Original files are guaranteed to remain 100% UNTOUCHED.
        """
        root_resolved = directory.resolve()
        target_files = self.collect_files(root_resolved)

        if not target_files:
            raise ValueError(f"No compatible source files found in {directory}")

        format_chosen = (fmt or self.config.output_format).lower().strip()
        mode_chosen = mode or self.config.mode
        ext_map = {"xml": ".xml", "json": ".json", "txt": ".txt"}
        bundle_ext = ext_map.get(format_chosen, ".xml")

        dest = output_file or (root_resolved / f"cavecode-bundle{bundle_ext}")
        dest_resolved = dest.resolve()

        all_paths = [p for _, p in target_files]
        guard = SafetyGuard(all_paths)

        raw_files: List[Tuple[str, str]] = []
        compressed_files: List[Tuple[str, str]] = []

        for rel_path, full_path in target_files:
            SafetyGuard.assert_safe_destination(full_path, dest_resolved)

            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            raw_files.append((rel_path, content))
            comp = self.compress_file_content(rel_path, content, mode=mode_chosen)
            compressed_files.append((rel_path, comp))

        raw_combined = "\n".join(c for _, c in raw_files)
        comp_combined = "\n".join(c for _, c in compressed_files)

        estimate = self.tokenizer.estimate(raw_combined, comp_combined)

        summary_msg = (
            f"CaveCode Bundle: {len(compressed_files)} files compressed.\n"
            f"Approximate Tokens: ~{estimate.raw_approx_tokens:,} raw -> ~{estimate.compressed_approx_tokens:,} compressed "
            f"(~{estimate.percent_saved}% reduction)."
        )

        manifest_files = raw_files if self.config.embed_recovery_manifest else None
        bundle_text = OutputFormatter.format(
            compressed_files=compressed_files,
            raw_files=manifest_files,
            fmt=format_chosen,
            summary=summary_msg,
        )

        dest_resolved.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_resolved, "w", encoding="utf-8") as f:
            f.write(bundle_text)

        is_safe, violations = guard.verify_untouched()
        if not is_safe:
            raise SafetyViolationError(f"Safety invariant violated: {violations}")

        return dest_resolved, estimate, len(compressed_files)
