"""
JavaScript & TypeScript High-Density Boilerplate & Syntax Compressor for CaveCode.
"""

import re
from typing import Optional
from cavecode.compressors.base import BaseCompressor


class JavaScriptCompressor(BaseCompressor):
    """Syntax and boilerplate compressor for JavaScript and TypeScript."""

    def __init__(self, language: str = "javascript"):
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

        # 4. Condense multi-line import blocks: import { ... } from '...';
        def condense_imports(match):
            is_type = "type " if "type" in match.group(0).split('{')[0] else ""
            items_str = match.group(1)
            module_str = match.group(2)
            items = [x.strip() for x in items_str.split(',') if x.strip()]
            return f"import {is_type}{{ {', '.join(items)} }} from '{module_str}';"

        code = re.sub(
            r'import\s+(?:type\s+)?\{([\s\S]*?)\}\s*from\s*[\'"]([^\'"]+)[\'"]\s*;?',
            condense_imports,
            code,
        )

        # 5. Condense multi-line export blocks
        def condense_exports(match):
            items_str = match.group(1)
            items = [x.strip() for x in items_str.split(',') if x.strip()]
            return f"export {{ {', '.join(items)} }};"

        code = re.sub(r'export\s*\{([\s\S]*?)\}\s*;', condense_exports, code)

        # 6. TypeScript type simplifications
        if self.language in ("typescript", "ts"):
            code = re.sub(r'\b([a-zA-Z0-9_.]+)\s*\|\s*(?:undefined|null)\b', r'\1?', code)
            code = re.sub(r'\b(?:undefined|null)\s*\|\s*([a-zA-Z0-9_.]+)\b', r'\1?', code)
            code = re.sub(r'\breadonly\b', 'ro', code)
            code = re.sub(r':\s*string\b', ': str', code)
            code = re.sub(r':\s*number\b', ': num', code)
            code = re.sub(r'<string>', '<str>', code)
            code = re.sub(r'<number>', '<num>', code)
            code = re.sub(r'\bPromise<string>\b', 'Promise<str>', code)
            code = re.sub(r'\bPromise<boolean>\b', 'Promise<bool>', code)

            # Collapse small interfaces and type aliases
            def collapse_iface(m):
                header = m.group(1)
                body = m.group(2)
                lines = [l.strip().rstrip(';') for l in body.splitlines() if l.strip()]
                if len(lines) <= 6 and sum(len(l) for l in lines) <= 180 and not any(l.startswith('//') for l in lines):
                    return f"{header} {{ " + "; ".join(lines) + " }"
                return m.group(0)

            code = re.sub(r'((?:exp\s+)?(?:interface|type)\s+[^{]+?)\{\s*\n([^{}]+?)\n\s*\}', collapse_iface, code)

        # 7. Type & keyword abbreviations
        code = re.sub(r'\breturn\b', 'ret', code)
        code = re.sub(r'\bthis\.', '', code)
        code = re.sub(r'\bfunction\b', 'fn', code)
        code = re.sub(r'\bexport\s+default\s+function\b', 'exp def fn', code)
        code = re.sub(r'\bexport\s+default\b', 'exp def', code)
        code = re.sub(r'\bexport\b', 'exp', code)
        code = re.sub(r'\bpublic\b', 'pub', code)
        code = re.sub(r'\bprivate\b', 'priv', code)
        code = re.sub(r'\bprotected\b', 'prot', code)
        code = re.sub(r'\bboolean\b', 'bool', code)

        # 8. Multiline signatures collapse (anchored fallback)
        code = re.sub(
            r'^[ \t]*(?:static\s+|pub\s+|priv\s+|prot\s+|ro\s+|fn\s+|func\s+|async\s+)*[a-zA-Z0-9_*&<>, ]+\s+(?!(?:if|while|for|switch|catch|return|ret)\b)[a-zA-Z0-9_]+\s*\([^)]*?\)\s*(?::\s*[^;{]+)?\s*\{',
            lambda m: re.sub(r'\s*\n\s*', ' ', m.group(0)),
            code,
            flags=re.MULTILINE,
        )

        # 9. Semicolons
        code = self.strip_semicolons(code)

        # 10. Inline small statement blocks
        code = self.inline_small_blocks(code, mode=m)

        # 11. Group single-line imports
        def group_imports_js(m):
            lines = [l.strip().rstrip(';') for l in m.group(0).splitlines() if l.strip()]
            return '; '.join(lines) + ';\n'

        code = re.sub(r'(?:^[ \t]*import\s+[^;\n]+;?\s*\r?\n){2,}', group_imports_js, code, flags=re.MULTILINE)

        # 12. Normalize indentation and strip blank lines
        return self.normalize_indentation(code)
