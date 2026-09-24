"""
C# High-Density Boilerplate & Syntax Compressor for CaveCode.
"""

import re
from typing import Optional
from cavecode.compressors.base import BaseCompressor


class CSharpCompressor(BaseCompressor):
    """AST & pattern-guided high-density compressor for C#."""

    def __init__(self):
        super().__init__("csharp")

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

        # 4. Keywords & modifiers
        code = re.sub(r'\bpublic\s+static\s+readonly\b', 'const', code)
        code = re.sub(r'\bprivate\s+static\s+readonly\b', 'priv const', code)
        code = re.sub(r'\bpublic\s+static\b', 'pub static', code)
        code = re.sub(r'\bprivate\s+static\b', 'priv static', code)
        code = re.sub(r'\bpublic\b', 'pub', code)
        code = re.sub(r'\bprivate\b', 'priv', code)
        code = re.sub(r'\bprotected\b', 'prot', code)
        code = re.sub(r'\binternal\b', 'intnl', code)
        code = re.sub(r'\breadonly\b', 'ro', code)
        code = re.sub(r'\bboolean\b', 'bool', code)
        code = re.sub(r'\breturn\b', 'ret', code)
        code = re.sub(r'\bthis\.', '', code)

        # 5. Condense property getters/setters & expression bodies
        code = re.sub(
            r'\{\s*get\s*\{[^}]*?ret(?:urn)?\s+([^;]+?);\s*\}\s*set\s*\{[^}]*?\}\s*\}',
            r'{ get => \1; set; }',
            code,
        )
        code = re.sub(
            r'\{\s*get\s*\{[^}]*?ret(?:urn)?\s+([^;]+?);\s*\}\s*\}',
            r'{ get => \1; }',
            code,
        )
        code = re.sub(r'\{\s*get;\s*set;\s*\}', '{get;set;}', code)
        code = re.sub(r'=>\s*\n\s*', r'=> ', code)

        # 6. Multiline signatures collapse
        code = re.sub(
            r'(?:pub\s+|priv\s+|prot\s+|intnl\s+|static\s+|async\s+|virtual\s+|override\s+|sealed\s+)*[a-zA-Z0-9_*&<>, \[\]?]+\s+[a-zA-Z0-9_]+\s*\([^)]*?\)\s*\{',
            lambda m: re.sub(r'\s*\n\s*', ' ', m.group(0)),
            code,
        )

        # 7. Group using statements
        def group_using(m):
            ns = re.findall(r'using\s+([^;\n]+);', m.group(0))
            return f"using {'; '.join(ns)};\n" if len(ns) >= 2 else m.group(0)

        code = re.sub(r'(?:^[ \t]*using\s+[^;\n]+;\s*\r?\n(?:[ \t]*\r?\n)?)+', group_using, code, flags=re.MULTILINE)

        # 8. Semicolons
        code = self.strip_semicolons(code)

        # 9. Inline small blocks
        code = self.inline_small_blocks(code, mode=m)

        # 10. Normalize indentation and collapse blank lines
        return self.normalize_indentation(code)
