"""
Configuration management for CaveCode.
"""

from pathlib import Path
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field
import yaml
import json


# The 9 official supported languages and their file extensions
LANGUAGE_EXTENSIONS: Dict[str, Set[str]] = {
    "python": {".py", ".pyi"},
    "javascript": {".js", ".jsx", ".mjs", ".cjs"},
    "typescript": {".ts", ".tsx", ".mts", ".cts"},
    "rust": {".rs"},
    "go": {".go"},
    "java": {".java"},
    "cpp": {".cpp", ".cc", ".cxx", ".hpp", ".hxx", ".hh"},
    "csharp": {".cs"},
    "c": {".c", ".h"},
}

EXTENSION_TO_LANGUAGE: Dict[str, str] = {}
for lang, exts in LANGUAGE_EXTENSIONS.items():
    for ext in exts:
        EXTENSION_TO_LANGUAGE[ext] = lang

SUPPORTED_EXTENSIONS: Set[str] = set(EXTENSION_TO_LANGUAGE.keys())

DEFAULT_EXCLUDES: List[str] = [
    ".git",
    ".svn",
    ".hg",
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".nox",
    ".coverage",
    "htmlcov",
    "venv",
    ".venv",
    "env",
    ".env",
    ".env.*",
    "node_modules",
    "bower_components",
    "dist",
    "build",
    "*.egg-info",
    "target",
    "bin",
    "obj",
    "out",
    ".next",
    ".nuxt",
    ".cargo",
    "vendor",
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.gif",
    "*.ico",
    "*.svg",
    "*.mp3",
    "*.mp4",
    "*.wav",
    "*.pdf",
    "*.zip",
    "*.tar",
    "*.gz",
    "*.7z",
    "*.rar",
    "*.exe",
    "*.dll",
    "*.so",
    "*.dylib",
    "*.bin",
    "*.iso",
    "*.woff",
    "*.woff2",
    "*.ttf",
    "*.eot",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "Cargo.lock",
    "*.sqlite3",
    "*.db",
    "*.cave.*",
    "*.cave",
    "do_not_upload",
    "_do_not_upload",
]


class CaveCodeConfig(BaseModel):
    """Runtime configuration for CaveCode."""

    root_path: Path = Field(default_factory=lambda: Path("."))
    output_format: str = "xml"  # 'xml', 'txt', 'json'
    includes: List[str] = Field(default_factory=list)
    excludes: List[str] = Field(default_factory=lambda: list(DEFAULT_EXCLUDES))
    mode: str = "ultra"  # 'lite', 'medium', 'ultra'
    max_file_size_kb: int = 2000  # 2 MB threshold per file
    embed_recovery_manifest: bool = True  # Allows 100% exact bitwise revert of original code
    verify_untouched: bool = True

    @classmethod
    def load_from_dir(cls, directory: Path) -> "CaveCodeConfig":
        """Load configuration from .cavecode.yaml, .cavecode.yml, or default."""
        for name in [".cavecode.yaml", ".cavecode.yml"]:
            cand = directory / name
            if cand.exists():
                try:
                    with open(cand, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f) or {}
                        return cls(**data)
                except Exception:
                    pass
        return cls(root_path=directory)

    def save_to_dir(self, directory: Path) -> Path:
        """Save configuration file to directory."""
        dest = directory / ".cavecode.yaml"
        data = self.model_dump(mode="json")
        data["root_path"] = str(data["root_path"])
        with open(dest, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        return dest
