"""
Rust High-Density Boilerplate & Syntax Compressor for CaveCode.
"""

import re
from typing import Optional
from cavecode.compressors.base import BaseCompressor


class RustCompressor(BaseCompressor):
    """AST & pattern-guided high-density compressor for Rust."""

    def __init__(self):
        super().__init__("rust")

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

        # 4. Strip internal compiler codegen & stability attributes
        code = re.sub(r'#\[inline[^\]]*\]\s*', '', code)
        code = re.sub(r'#\[doc\(hidden[^\]]*\)\]\s*', '', code)
        code = re.sub(r'#\[must_use[^\]]*\]\s*', '', code)
        code = re.sub(r'#\[rustc_[^\]]*\]\s*', '', code)

        # 5. Condense derives
        code = re.sub(r'#\[derive\(([^)]+)\)\]', lambda m: '#[derive(' + ','.join(x.strip() for x in m.group(1).split(',')) + ')]', code)

        # 6. Simplify verbose match Ok/Err return:
        match_err_pattern = re.compile(
            r'match\s+([a-zA-Z0-9_\.]+)\s*\{\s*Ok\((\w+)\)\s*=>\s*\2,\s*Err\(\w+\)\s*=>\s*return\s+Err\([^)]+\),?\s*\}'
        )
        code = match_err_pattern.sub(r'\1?', code)

        # 7. Keywords
        code = re.sub(r'\bpub\(crate\)\b', 'pub', code)
        code = re.sub(r'\breturn\b', 'ret', code)

        # 9. Inline small blocks
        code = self.inline_small_blocks(code, mode=m)

        # 10. Normalize indentation and collapse blank lines
        return self.normalize_indentation(code)
