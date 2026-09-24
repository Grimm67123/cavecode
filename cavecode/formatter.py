"""
Output Formatter for CaveCode Context Bundles.

Serializes compressed files into XML, plain text, or structured JSON.
Embeds an optional high-density recovery manifest allowing 100% exact bitwise
restoration via `cavecode revert`.
"""

import base64
import json
from typing import Dict, List, Tuple
from xml.sax.saxutils import escape
import zlib


SYSTEM_INSTRUCTION = """Below is the high-density source context of the codebase, optimized by CaveCode.
Syntactic noise and boilerplate have been condensed while 100% of names, logic, and comments are preserved.
Always refer to files by their relative source paths.
"""


class OutputFormatter:
    """Serializes compressed files into LLM-ready bundles with recovery manifests."""

    @staticmethod
    def encode_manifest(raw_files: List[Tuple[str, str]]) -> str:
        """Create a compressed base64 payload of original files for lossless reversion."""
        data = {path: content for path, content in raw_files}
        json_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")
        compressed_bytes = zlib.compress(json_bytes, level=9)
        return base64.b64encode(compressed_bytes).decode("ascii")

    @classmethod
    def to_xml(
        cls,
        compressed_files: List[Tuple[str, str]],
        raw_files: List[Tuple[str, str]] = None,
        summary: str = "",
    ) -> str:
        """Serialize into structured XML with optional recovery manifest."""
        out = [
            "<codebase_context>",
            f"<instruction>{escape(SYSTEM_INSTRUCTION.strip())}</instruction>",
        ]
        if summary:
            out.append(f"<summary>\n{escape(summary)}\n</summary>")

        out.append("<documents>")
        for idx, (path, content) in enumerate(compressed_files, start=1):
            out.append(f'  <document index="{idx}">')
            out.append(f"    <source>{escape(path)}</source>")
            out.append(f"    <document_content><![CDATA[\n{content}\n]]></document_content>")
            out.append("  </document>")
        out.append("</documents>")

        if raw_files:
            manifest_str = cls.encode_manifest(raw_files)
            out.append(f"<cavecode_manifest>{manifest_str}</cavecode_manifest>")

        out.append("</codebase_context>")
        return "\n".join(out)

    @classmethod
    def to_txt(
        cls,
        compressed_files: List[Tuple[str, str]],
        raw_files: List[Tuple[str, str]] = None,
        summary: str = "",
    ) -> str:
        """Serialize into clean text format with file separators and manifest footer."""
        out = [
            "==================================================================",
            "CODEBASE CONTEXT (OPTIMIZED BY CAVECODE)",
            "==================================================================",
            SYSTEM_INSTRUCTION.strip(),
            "",
        ]
        if summary:
            out.extend(["[SUMMARY]", summary, ""])

        for path, content in compressed_files:
            out.append(f"--- FILE: {path} ---")
            out.append(content)
            out.append("")

        if raw_files:
            manifest_str = cls.encode_manifest(raw_files)
            out.append(f"# [cavecode:manifest:{manifest_str}]")

        return "\n".join(out)

    @classmethod
    def to_json(
        cls,
        compressed_files: List[Tuple[str, str]],
        raw_files: List[Tuple[str, str]] = None,
        summary: str = "",
    ) -> str:
        """Serialize into JSON schema."""
        payload = {
            "generator": "CaveCode",
            "instruction": SYSTEM_INSTRUCTION.strip(),
            "summary": summary,
            "total_files": len(compressed_files),
            "files": [
                {"path": path, "content": content}
                for path, content in compressed_files
            ],
        }
        if raw_files:
            payload["manifest"] = cls.encode_manifest(raw_files)
        return json.dumps(payload, indent=2)

    @classmethod
    def format(
        cls,
        compressed_files: List[Tuple[str, str]],
        raw_files: List[Tuple[str, str]] = None,
        fmt: str = "xml",
        summary: str = "",
    ) -> str:
        """Dispatch formatting based on requested format."""
        fmt_clean = fmt.lower().strip()
        if fmt_clean == "xml":
            return cls.to_xml(compressed_files, raw_files, summary)
        elif fmt_clean == "json":
            return cls.to_json(compressed_files, raw_files, summary)
        else:
            return cls.to_txt(compressed_files, raw_files, summary)
