"""
Safety and Integrity Engine for CaveCode.

Guarantees that original target source files are NEVER overwritten or modified.
"""

import hashlib
from pathlib import Path
from typing import Dict, List, Tuple


class SafetyViolationError(RuntimeError):
    """Raised if an operation attempts to overwrite or modify an original source file."""
    pass


class SafetyGuard:
    """Monitors and protects source files from being modified during compression."""

    def __init__(self, target_paths: List[Path] = None):
        self._initial_hashes: Dict[str, str] = {}
        if target_paths:
            self.snapshot(target_paths)

    @staticmethod
    def compute_sha256(path: Path) -> str:
        """Compute the SHA256 hash of a file."""
        if not path.is_file():
            return ""
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def snapshot(self, paths: List[Path]) -> None:
        """Take a cryptographic snapshot of target files before any processing."""
        self._initial_hashes.clear()
        for p in paths:
            if p.is_file():
                self._initial_hashes[str(p.resolve())] = self.compute_sha256(p)

    def verify_untouched(self) -> Tuple[bool, List[str]]:
        """
        Verify that none of the snapshot source files have been modified.
        Returns (is_untouched, list_of_violations).
        """
        violations = []
        for path_str, original_hash in self._initial_hashes.items():
            p = Path(path_str)
            if not p.exists():
                violations.append(f"DELETED: {path_str}")
                continue
            current_hash = self.compute_sha256(p)
            if current_hash != original_hash:
                violations.append(f"MODIFIED: {path_str} (expected {original_hash[:8]}..., got {current_hash[:8]}...)")

        return len(violations) == 0, violations

    @staticmethod
    def assert_safe_destination(source_path: Path, dest_path: Path) -> None:
        """
        Ensure destination path does not collide with or overwrite the source path.
        """
        src_resolved = source_path.resolve()
        dest_resolved = dest_path.resolve()
        if src_resolved == dest_resolved:
            raise SafetyViolationError(
                f"SAFETY GUARD TRIGGERED: Destination path '{dest_path}' is identical to the target source file '{source_path}'. "
                "CaveCode strictly forbids compressing files in-place to protect your original code."
            )
