"""
Python High-Density Syntax Compressor for CaveCode.
"""

import re
from typing import Optional
from cavecode.compressors.base import BaseCompressor


class PythonCompressor(BaseCompressor):
    """AST & pattern-guided high-density compressor for Python."""

    def __init__(self):
        super().__init__("python")

    def compress(self, source_code: str, mode: Optional[str] = None) -> str:
        if not source_code.strip():
            return source_code

        m = self.normalize_mode(mode or self.mode)
        code = self.prune_ast(source_code, mode=m)

        # 2. Process comments & docstrings based on mode
        code = self.process_python_comments(code, mode=m)

        # 3. String literals & logging
        code = self.condense_string_literals(code, mode=m)
        code = self.strip_verbose_logging(code, mode=m)

        # Ultra optimizations
        if m == "ultra":
            code = re.sub(r'^[ \t]*if\s+TYPE_CHECKING:[\s\S]*?(?=^[a-zA-Z0-9_#])', '', code, flags=re.MULTILINE)
            code = re.sub(r'\bself\.', '', code)

        # 4. Multiline def signatures collapse
        code = re.sub(
            r'(?:async\s+)?(?:def|fn)\s+[a-zA-Z0-9_]+\s*\([^:]*?\)\s*(?:->[^:]+?)?:',
            lambda match: re.sub(r'\s*\n\s*', ' ', match.group(0)),
            code,
        )

        # 5. Collapse simple 1-line if/ret/raise (preserving indentation)
        code = re.sub(
            r'^([ \t]*)if\s+([^\n:]+):\s*\n[ \t]+(return\b[^\n]+|raise\b[^\n]+)',
            r'\1if \2: \3',
            code,
            flags=re.MULTILINE,
        )

        # 6. Group imports & clean multiline import tuples
        code = re.sub(
            r'from\s+([a-zA-Z0-9_\.]+)\s+import\s*\(([^)]+)\)',
            lambda m: f"from {m.group(1)} import " + ", ".join(x.strip().rstrip(',') for x in m.group(2).split() if x.strip().rstrip(',')),
            code,
        )

        # Strip linter directives (# type: ignore, # noqa)
        code = re.sub(r'[ \t]*#\s*(?:type:\s*ignore(?:\[[^\]]*\])?|noqa:[^\n]+|noqa\b)', '', code)

        # Collapse small multi-line tuples/lists: ( \n a,\n b\n ) -> (a, b)
        def collapse_tuple(m):
            inner = m.group(1)
            lines = [l.strip().rstrip(',') for l in inner.splitlines() if l.strip()]
            if 2 <= len(lines) <= 8 and sum(len(l) for l in lines) <= 180 and not any(l.startswith('#') for l in lines):
                return f"({', '.join(lines)})"
            return m.group(0)

        code = re.sub(r'\(\s*\n([^\(\)]+?)\n\s*\)', collapse_tuple, code)

        def group_imports(m):
            lines = [l.strip() for l in m.group(0).splitlines() if l.strip()]
            mods = [l[7:].strip() for l in lines if l.startswith("import ")]
            return f"import {', '.join(mods)}\n" if len(mods) >= 2 else m.group(0)

        code = re.sub(r'(?:^[ \t]*import\s+[a-zA-Z0-9_\.]+\s*\r?\n){2,}', group_imports, code, flags=re.MULTILINE)

        # 7. Type annotations
        code = re.sub(r'\b(?:typing\.)?Optional\[([a-zA-Z0-9_\[\],\s]+)\]', r'\1?', code)
        code = re.sub(r'\b(?:typing\.)?Union\[([a-zA-Z0-9_]+),\s*([a-zA-Z0-9_]+)\]', r'\1 | \2', code)
        code = re.sub(r'\btyping\.List\b', 'list', code)
        code = re.sub(r'\btyping\.Dict\b', 'dict', code)
        code = re.sub(r'\btyping\.Set\b', 'set', code)
        code = re.sub(r'\btyping\.Tuple\b', 'tuple', code)
        code = re.sub(r'\btyping\.Any\b', 'any', code)

        # 8. Keywords
        code = re.sub(r'\breturn\b', 'ret', code)
        code = re.sub(r'\bdef\b', 'fn', code)
        code = re.sub(r'if\s+__name__\s*==\s*[\'"]__main__[\'"]\s*:', 'if __main__:', code)

        # 9. Strip redundant 'pass'
        code = re.sub(r'([:\n]\s*"""[\s\S]*?"""\s*)\n\s*pass\b', r'\1', code)

        # 10. Normalize indentation and collapse blank lines
        return self.normalize_indentation(code)
