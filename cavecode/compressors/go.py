"""
Go High-Density Boilerplate & Syntax Compressor for CaveCode.
"""

import re
from typing import Optional
from cavecode.compressors.base import BaseCompressor


class GoCompressor(BaseCompressor):
    """AST & pattern-guided high-density compressor for Go."""

    def __init__(self):
        super().__init__("go")

    def compress(self, source_code: str, mode: Optional[str] = None) -> str:
        if not source_code.strip():
            return source_code

        m = self.normalize_mode(mode or self.mode)
        code = self.prune_ast(source_code, mode=m)

        # 2. Comments based on mode
        code = self.process_c_comments(code, mode=m)

        # 4. String literals & logging
        code = self.condense_string_literals(code, mode=m)
        code = self.strip_verbose_logging(code, mode=m)

        # 5. Keywords & types
        code = re.sub(r'\bfunc\b', 'fn', code)
        code = re.sub(r'\breturn\b', 'ret', code)
        code = re.sub(r'\binterface\{\}', 'any', code)

        # 6. Multiline signatures collapse (anchored fallback)
        code = re.sub(
            r'^[ \t]*fn\s+(?:\([^)]+\)\s+)?[a-zA-Z0-9_]+\s*\([^)]*?\)\s*(?:\([^)]*?\)|[a-zA-Z0-9_*&<>, ]+)?\s*\{',
            lambda m: re.sub(r'\s*\n\s*', ' ', m.group(0)),
            code,
            flags=re.MULTILINE,
        )

        # 7. Condense 'if err != nil'
        code = re.sub(
            r'^[ \t]*if\s+err\s*!=\s*nil\s*\{\s*\r?\n[ \t]*ret(?:urn)?\s*([^;\n]*?)\s*\r?\n[ \t]*\}',
            lambda m: f"if err != nil {{ ret {m.group(1).strip()} }}".replace("ret  }", "ret }"),
            code,
            flags=re.MULTILINE,
        )
        code = re.sub(
            r'^[ \t]*if\s+err\s*!=\s*nil\s*\{\s*\r?\n[ \t]*([^\n]+?)\s*\r?\n[ \t]*ret(?:urn)?\s*([^;\n]*?)\s*\r?\n[ \t]*\}',
            lambda m: f"if err != nil {{ {m.group(1).strip()}; ret {m.group(2).strip()} }}".replace("ret  }", "ret }").replace("ret }", "ret }"),
            code,
            flags=re.MULTILINE,
        )

        # 8. Group imports
        def group_go_imports(m):
            pkgs = re.findall(r'"([^"]+)"', m.group(0))
            return 'import (' + ' '.join(f'"{p}"' for p in pkgs) + ')\n' if len(pkgs) >= 2 else m.group(0)

        code = re.sub(r'import\s*\(\s*\n([^\)]+?)\n\s*\)', group_go_imports, code)

        # 9. Inline small blocks
        code = self.inline_small_blocks(code, mode=m)

        # 10. Normalize indentation and collapse blank lines
        return self.normalize_indentation(code)
