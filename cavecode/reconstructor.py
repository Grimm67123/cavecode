"""
Code Reconstructor and Reversion Engine for CaveCode.

Provides commands and utilities to revert compressed files and bundles
back to their original source code.
"""

import base64
import json
from pathlib import Path
import re
from typing import Dict, List, Tuple
import zlib


class CodeReconstructor:
    """Reverts compressed bundles or files back into original code."""

    @staticmethod
    def decode_manifest(manifest_str: str) -> Dict[str, str]:
        """Decode base64+zlib encoded manifest back to file map."""
        try:
            compressed_bytes = base64.b64decode(manifest_str.strip())
            json_bytes = zlib.decompress(compressed_bytes)
            return json.loads(json_bytes.decode("utf-8"))
        except Exception as e:
            raise ValueError(f"Failed to decode CaveCode recovery manifest: {e}")

    @classmethod
    def extract_from_xml(cls, xml_text: str) -> Tuple[Dict[str, str], bool]:
        """
        Extract files from XML bundle.
        Returns (file_map, is_exact_bitwise_revert).
        """
        # 1. Check for exact recovery manifest
        m = re.search(r'<cavecode_manifest>([\s\S]*?)</cavecode_manifest>', xml_text)
        if m:
            manifest_str = m.group(1).strip()
            return cls.decode_manifest(manifest_str), True

        # 2. Fallback: extract compressed documents
        files = {}
        doc_matches = re.finditer(
            r'<document[^>]*>\s*<source>(.*?)</source>\s*<document_content><!\[CDATA\[([\s\S]*?)\]\]></document_content>\s*</document>',
            xml_text,
        )
        for dm in doc_matches:
            path = dm.group(1).strip()
            content = dm.group(2).strip()
            files[path] = content

        return files, False

    @classmethod
    def extract_from_txt(cls, txt_text: str) -> Tuple[Dict[str, str], bool]:
        """
        Extract files from plain-text bundle.
        Returns (file_map, is_exact_bitwise_revert).
        """
        # 1. Check for manifest
        m = re.search(r'#\s*\[cavecode:manifest:([a-zA-Z0-9+/=]+)\]', txt_text)
        if m:
            return cls.decode_manifest(m.group(1)), True

        # 2. Fallback: split on file separators
        files = {}
        pattern = re.compile(r'--- FILE:\s*([^\s-]+)\s*---([\s\S]*?)(?=(?:--- FILE:|$|#\s*\[cavecode))')
        for match in pattern.finditer(txt_text):
            path = match.group(1).strip()
            content = match.group(2).strip()
            files[path] = content

        return files, False

    @classmethod
    def extract_from_json(cls, json_text: str) -> Tuple[Dict[str, str], bool]:
        """Extract files from JSON bundle."""
        data = json.loads(json_text)
        if "manifest" in data:
            return cls.decode_manifest(data["manifest"]), True
        files = {item["path"]: item["content"] for item in data.get("files", [])}
        return files, False

    @classmethod
    def revert_bundle(
        cls, bundle_path: Path, output_dir: Path
    ) -> Tuple[int, bool, List[str]]:
        """
        Revert an entire bundle file to source files in output_dir.
        Returns (count_files_restored, is_exact_bitwise, list_of_restored_paths).
        """
        with open(bundle_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        file_map: Dict[str, str] = {}
        is_exact = False

        if bundle_path.suffix.lower() == ".xml" or "<codebase_context>" in content:
            file_map, is_exact = cls.extract_from_xml(content)
        elif bundle_path.suffix.lower() == ".json":
            file_map, is_exact = cls.extract_from_json(content)
        else:
            file_map, is_exact = cls.extract_from_txt(content)

        if not file_map:
            raise ValueError(f"No files could be extracted from bundle: {bundle_path}")

        output_dir.mkdir(parents=True, exist_ok=True)
        restored = []

        for rel_path, file_content in file_map.items():
            dest = output_dir / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(dest, "w", encoding="utf-8") as out_f:
                out_f.write(file_content)
            restored.append(str(dest))

        return len(restored), is_exact, restored
