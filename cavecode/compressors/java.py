"""
Java High-Density Boilerplate & Syntax Compressor for CaveCode.
"""

import re
from typing import Optional
from cavecode.compressors.base import BaseCompressor


class JavaCompressor(BaseCompressor):
    """AST & pattern-guided high-density compressor for Java."""

    def __init__(self):
        super().__init__("java")

    def compress(self, source_code: str, mode: Optional[str] = None) -> str:
        if not source_code.strip():
            return source_code

        m = self.normalize_mode(mode or self.mode)
        code = self.prune_ast(source_code, mode=m)

        # 2. Comments based on mode
        code = self.process_c_comments(code, mode=m)

        # 3. String literals & logging
        code = self.condense_string_literals(code, mode=m)
        code = self.strip_verbose_logging(code, mode=m)

        # 4. Strip compiler annotations & boilerplate
        code = re.sub(r'@SuppressWarnings\([^)]*\)\s*', '', code)
        code = re.sub(r'@Generated\([^)]*\)\s*', '', code)
        code = re.sub(r'@Override\s*', '', code)
        code = re.sub(r'@Nullable\s*', '?', code)

        # 5. Keywords & modifiers
        code = re.sub(r'\bpublic\s+static\s+final\b', 'const', code)
        code = re.sub(r'\bprivate\s+static\s+final\b', 'priv const', code)
        code = re.sub(r'\bpublic\s+static\b', 'pub static', code)
        code = re.sub(r'\bprivate\s+static\b', 'priv static', code)
        code = re.sub(r'\bpublic\b', 'pub', code)
        code = re.sub(r'\bprivate\b', 'priv', code)
        code = re.sub(r'\bprotected\b', 'prot', code)
        code = re.sub(r'\bboolean\b', 'bool', code)
        code = re.sub(r'\breturn\b', 'ret', code)
        code = re.sub(r'\bthis\.', '', code)

        # 6. Diamond operator instantiation
        code = re.sub(r'new\s+([A-Z]\w*)<[^>]+>\s*\(', r'new \1<>(', code)

        # 7. Group imports
        def group_java_imports(m):
            lines = [l.strip().rstrip(';') for l in m.group(0).splitlines() if l.strip()]
            return '; '.join(lines) + ';\n'

        code = re.sub(r'(?:^[ \t]*import\s+[^;\n]+;\s*\r?\n){2,}', group_java_imports, code, flags=re.MULTILINE)

        # 8. Multiline signatures collapse
        code = re.sub(
            r'(?:static\s+|pub\s+|priv\s+|prot\s+|final\s+|volatile\s+|synchronized\s+)*[a-zA-Z0-9_*&<>, \[\]?]+\s+[a-zA-Z0-9_]+\s*\([^)]*?\)\s*(?:throws\s+[a-zA-Z0-9_, ]+)?\s*\{',
            lambda m: re.sub(r'\s*\n\s*', ' ', m.group(0)),
            code,
        )

        # 9. Semicolons
        code = self.strip_semicolons(code)

        # 10. Inline small blocks
        code = self.inline_small_blocks(code, mode=m)

        # 11. Normalize indentation and collapse blank lines
        return self.normalize_indentation(code)
