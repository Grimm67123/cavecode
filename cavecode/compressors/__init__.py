"""
Language compressor registry for CaveCode.
"""

from typing import Dict
from cavecode.compressors.base import BaseCompressor
from cavecode.compressors.python import PythonCompressor
from cavecode.compressors.javascript import JavaScriptCompressor
from cavecode.compressors.java import JavaCompressor
from cavecode.compressors.csharp import CSharpCompressor
from cavecode.compressors.cpp import CppCompressor
from cavecode.compressors.go import GoCompressor
from cavecode.compressors.rust import RustCompressor

_REGISTRY: Dict[str, BaseCompressor] = {
    "python": PythonCompressor(),
    "javascript": JavaScriptCompressor("javascript"),
    "typescript": JavaScriptCompressor("typescript"),
    "rust": RustCompressor(),
    "go": GoCompressor(),
    "java": JavaCompressor(),
    "cpp": CppCompressor("cpp"),
    "c": CppCompressor("c"),
    "csharp": CSharpCompressor(),
}


def get_compressor(language: str) -> BaseCompressor:
    """Return the compressor instance for the specified language."""
    lang_clean = language.lower().strip()
    if lang_clean not in _REGISTRY:
        raise ValueError(
            f"Unsupported language '{language}'. Supported: {', '.join(sorted(_REGISTRY.keys()))}"
        )
    return _REGISTRY[lang_clean]
