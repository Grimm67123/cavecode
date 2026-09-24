"""
C & C++ High-Density Boilerplate & Syntax Compressor for CaveCode.
"""

import re
from typing import Optional
from cavecode.compressors.base import BaseCompressor


class CppCompressor(BaseCompressor):
    """Syntax and boilerplate compressor for C and C++."""

    def __init__(self, language: str = "cpp"):
        super().__init__(language)

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

        # 4. Header guards (#ifndef FOO_H \n #define FOO_H)
        code = re.sub(
            r'#ifndef\s+([A-Za-z0-9_]+)\s*\r?\n#define\s+\1',
            r'/* [guard \1] */ #pragma once',
            code,
        )

        # 5. Group angle and quote includes (including across empty lines)
        def group_includes(m):
            block = m.group(0)
            angle_headers = re.findall(r'#include\s+<([^>]+)>', block)
            quote_headers = re.findall(r'#include\s+"([^"]+)"', block)
            all_headers = angle_headers + quote_headers
            if len(all_headers) >= 2:
                return f"#include <{', '.join(all_headers)}>\n"
            return block

        code = re.sub(
            r'(?:^[ \t]*#include\s+[<"][^>"\n]+[>"]\s*\r?\n(?:[ \t]*\r?\n)?)+',
            group_includes,
            code,
            flags=re.MULTILINE,
        )

        # 6. Type & keyword abbreviations
        code = re.sub(r'\breturn\b', 'ret', code)
        code = re.sub(r'\bunsigned\s+int\b', 'u32', code)
        code = re.sub(r'\bunsigned\s+long\s+long\b', 'u64', code)
        code = re.sub(r'\bunsigned\s+long\b', 'u64', code)
        code = re.sub(r'\bunsigned\s+char\b', 'u8', code)
        code = re.sub(r'\buint32_t\b', 'u32', code)
        code = re.sub(r'\buint64_t\b', 'u64', code)
        code = re.sub(r'\buint8_t\b', 'u8', code)
        code = re.sub(r'\bint32_t\b', 'i32', code)
        code = re.sub(r'\bint64_t\b', 'i64', code)
        code = re.sub(r'\bsize_t\b', 'usize', code)
        code = re.sub(r'\bssize_t\b', 'isize', code)
        code = re.sub(r'\bNULL\b', '0', code)
        code = re.sub(r'\bnullptr\b', '0', code)
        code = re.sub(r'\bTRUE\b', '1', code)
        code = re.sub(r'\bFALSE\b', '0', code)
        code = re.sub(r'__attribute__\s*\(\([^)]*\)\)', '', code)
        code = re.sub(r'__declspec\s*\([^)]*\)', '', code)

        # 7. C++ specific
        if self.language == "cpp":
            std_types = [
                "vector", "string", "map", "unordered_map", "set", "unordered_set",
                "unique_ptr", "shared_ptr", "make_unique", "make_shared",
                "pair", "tuple", "optional", "variant", "cout", "cin", "cerr", "endl"
            ]
            pattern = r'\bstd::(' + '|'.join(std_types) + r')\b'
            code = re.sub(pattern, r'\1', code)
            code = re.sub(r'namespace\s+(\w+)\s*\{\s*\n\s*namespace\s+(\w+)\s*\{', r'namespace \1::\2 {', code)
            code = re.sub(r'\bconst\s+auto&', 'auto&', code)

        # 8. Multiline function signatures collapse (line-anchored fallback)
        code = re.sub(
            r'^[ \t]*(?:static\s+|inline\s+|virtual\s+|explicit\s+|constexpr\s+|friend\s+)*(?:[a-zA-Z0-9_*&<>,]+\s+)+(?!(?:if|while|for|switch|catch|return|ret)\b)[a-zA-Z0-9_:]+\s*\([^;{]*?\)\s*(?:const\s*)?(?:noexcept\s*)?\{',
            lambda m: re.sub(r'\s*\n\s*', ' ', m.group(0)),
            code,
            flags=re.MULTILINE,
        )

        # Redundant struct keyword
        code = re.sub(r'\bstruct\s+([A-Za-z0-9_]+)\b', r'\1', code)

        # 9. Inline small blocks
        code = self.inline_small_blocks(code, mode=m)

        # 10. Normalize indentation and collapse blank lines
        return self.normalize_indentation(code)
