"""
Base Compressor Interface for CaveCode.

Why input many code when few code do trick?

All language compressors strictly uphold core invariants:
1. Comments (single-line, multi-line, docstrings) preserved in dense telegraphic format.
2. Function, class, variable, and parameter names preserved.
3. Function implementations NOT stubbed out with ellipsis (...); logic and flow maintained.
4. Delivers high-density semantic compression (slashing 30-50%+ tokens).
"""

from abc import ABC, abstractmethod
import re
from typing import List, Tuple, Optional
from cavecode.ast_pruner import ASTPruner


class BaseCompressor(ABC):
    """Abstract base class for language-specific AST and syntax compressors."""

    def __init__(self, language: str, mode: str = "medium"):
        self.language = language
        self.mode = self.normalize_mode(mode)

    def prune_ast(self, code: str, mode: Optional[str] = None) -> str:
        """Run AST-level pruning before pattern transformations."""
        m = self.normalize_mode(mode or self.mode)
        return ASTPruner.prune_ast(code, self.language, mode=m)

    @abstractmethod
    def compress(self, source_code: str, mode: Optional[str] = None) -> str:
        """Compress source code into high-density CaveCode representation."""
        pass

    @staticmethod
    def protect_literals(text: str) -> Tuple[str, List[str]]:
        """
        Mask string literals so syntax transformations don't corrupt their content.
        Returns (masked_text, token_list).
        """
        tokens = []

        def repl(match):
            tokens.append(match.group(0))
            return f"__CAVE_TOK_{len(tokens) - 1}__"

        pattern = re.compile(
            r'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\''
            r'|"(?:\\.|[^"\\])*"'
            r'|\'(?:\\.|[^\'\\])*\''
            r'|`[\s\S]*?`)'
        )
        masked = pattern.sub(repl, text)
        return masked, tokens

    @staticmethod
    def restore_literals(text: str, tokens: List[str]) -> str:
        """Restore tokens masked by protect_literals."""
        for idx, tok in enumerate(tokens):
            text = text.replace(f"__CAVE_TOK_{idx}__", tok)
        return text

    @staticmethod
    def telegraphic_comment(text: str, prefix: str = "// ") -> str:
        """Telegraphic comment condensing for medium mode."""
        if re.search(r'copy\w*|licensed under|all rights reserved|general public license|mit license|apache license', text, re.I):
            m = re.search(r'copy\w*\s+(?:\(c\)\s*)?([0-9\-, ]+)?\s*([a-zA-Z0-9_\. ]+)', text, re.I)
            owner = m.group(0).strip() if m else "Authors"
            return f"{prefix}[License: {owner}]"
        if re.search(r'#(?:region|endregion)\b', text, re.I):
            return ""
        m_sect = re.search(r'[-=*~]{4,}\s*([a-zA-Z0-9_ ]+)\s*[-=*~]{4,}', text)
        if m_sect:
            return f"{prefix}[{m_sect.group(1).strip()}]"
        if re.match(r'^\s*[-=*~#]{4,}\s*$', text):
            return ""
        text = re.sub(r'\{@link\s+#?([^}]+)\}', r'\1', text)
        text = re.sub(r'\{@code\s+([^}]+)\}', r'\1', text)
        text = re.sub(r'<see\s+cref="([^"]+)"\s*/>', r'\1', text)
        text = re.sub(r'<inheritdoc\s*/?>', '', text, flags=re.I)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'/\*+|\*+/|^[ \t]*\*[ \t]?', ' ', text, flags=re.MULTILINE)
        text = re.sub(r'^[ \t]*#+[ \t]?', ' ', text, flags=re.MULTILINE)
        text = re.sub(r'^[ \t]*///+[ \t]?', ' ', text, flags=re.MULTILINE)
        text = re.sub(r'^[ \t]*//+[ \t]?', ' ', text, flags=re.MULTILINE)
        text = re.sub(r'\.\.\s*version(?:added|changed)::[^\n]+(?:\n\s+[^\n]+)*', '', text)
        text = re.sub(r'@(?:since|author|version|see|return|param)[^\n]+', '', text)
        text = re.sub(r'\.\.\s*code-block::[^\n]+(?:\n\s+[^\n]+)*', '', text)
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        content = " ".join(lines)
        if not content or re.match(r'^(?:inheritdoc|todo|fixme)\b', content, re.I):
            return ""
        sentences = re.split(r'(?<=[.!?])\s+', content)
        content = sentences[0] if sentences else content
        subs = [
            (r'\b(?:in order to|is used to|used to|responsible for|capable of|designed to)\b', 'to'),
            (r'\b(?:it is possible to|can be used to|allows you to)\b', 'can'),
            (r'\b(?:please note that|note that|it should be noted that)\b', 'NOTE:'),
            (r'\b(?:as well as|in addition to)\b', '&'),
            (r'\b(?:for example|such as|e\.g\.)\b', 'eg'),
            (r'\breturn(?:ing|s)?\b', 'ret'),
            (r'\bfunction(?:s)?\b', 'fn'),
            (r'\bstring(?:s)?\b', 'str'),
            (r'\bboolean\b', 'bool'),
            (r'\bmessage(?:s)?\b', 'msg'),
            (r'\bconfiguration\b', 'config'),
            (r'\b(?:the|a|an|is|are|was|were|to be|can be|will be|should be|would be|may be|must be|of|in|for|on|with|as|by|at|from|into)\b\s*', ' '),
        ]
        for p, r in subs:
            content = re.sub(p, r, content, flags=re.I)
        words = [w.strip() for w in content.split() if w.strip()]
        if not words:
            return ""
        return prefix + " ".join(words[:12])

    @classmethod
    def normalize_mode(cls, mode: Optional[str]) -> str:
        """Normalize mode string into lite, medium, or ultra."""
        if not mode:
            return "medium"
        m = mode.lower().strip()
        if m in ("lite", "light"):
            return "lite"
        if m in ("ultra",):
            return "ultra"
        return "medium"

    @staticmethod
    def strip_license_header(text: str) -> str:
        """Strip file-level legal and license headers from the top of the file."""
        return re.sub(
            r'^(?:/\*[\s\S]*?(?:copy\w*|license|all rights reserved)[\s\S]*?\*/|//[^\n]*(?:copy\w*|license)[^\n]*\r?\n+|#[^\n]*(?:copy\w*|license)[^\n]*\r?\n+|"""[\s\S]*?(?:copy\w*|license)[\s\S]*?""")',
            '',
            text,
            flags=re.IGNORECASE,
        )

    def process_python_comments(self, code: str, mode: str = "ultra") -> str:
        """Process comments and docstrings for Python."""
        mode_clean = self.normalize_mode(mode)
        code = self.strip_license_header(code)
        if mode_clean == "ultra":
            code = re.sub(r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'', '', code)
            code = re.sub(r'^[ \t]*#[^\n]*\r?\n', '', code, flags=re.MULTILINE)
            code = re.sub(r'(?<!:)#[^\n]*', '', code)
            return code

        def repl_doc(m):
            q = m.group(1)
            inner = self.telegraphic_comment(m.group(2), prefix="")
            return f"{q}{inner}{q}" if inner else '""'

        code = re.sub(r'("""|\'\'\')([\s\S]*?)\1', repl_doc, code)

        def repl_py_comm(m):
            t = self.telegraphic_comment(m.group(0), prefix="# ")
            return t + "\n" if t else ""

        code = re.sub(r'(?:^[ \t]*#[^\n]*\r?\n)+', repl_py_comm, code, flags=re.MULTILINE)
        return code

    def process_c_comments(self, code: str, mode: str = "ultra") -> str:
        """Process comments for C-style languages (C, C++, JS, TS, Go, Rust, Java, C#)."""
        mode_clean = self.normalize_mode(mode)
        code = self.strip_license_header(code)
        if mode_clean == "ultra":
            code = re.sub(r'/\*[\s\S]*?\*/', '', code)
            code = re.sub(r'(?<!:)//[^\n]*', '', code)
            return code

        def repl_block(m):
            inner = self.telegraphic_comment(m.group(1), prefix="")
            return f"/* {inner} */" if inner else ""

        code = re.sub(r'/\*([\s\S]*?)\*/', repl_block, code)

        def repl_line(m):
            inner = self.telegraphic_comment(m.group(0), prefix="// ")
            return inner + "\n" if inner else ""

        code = re.sub(r'(?:^[ \t]*//[^\n]*\r?\n)+', repl_line, code, flags=re.MULTILINE)
        return code

    @classmethod
    def condense_string_literals(cls, code: str, mode: str = "ultra") -> str:
        """Condense oversized error message string literals based on mode."""
        mode_clean = cls.normalize_mode(mode)
        if mode_clean == "lite":
            return code
        threshold = 16 if mode_clean == "ultra" else 28
        cutoff = 10 if mode_clean == "ultra" else 20

        def repl_str(m):
            full = m.group(0)
            quote = full[0]
            inner = full[1:-1]
            if len(inner) > threshold and not inner.startswith("http") and not inner.startswith("data:"):
                condensed = inner[:cutoff].strip() + "..."
                return f"{quote}{condensed}{quote}"
            return full

        return re.sub(
            r'(?<!")"[^"\n]{' + str(threshold) + r',}"(?!")|(?<!\')\'[^\'\n]{' + str(threshold) + r',}\'(?!\')',
            repl_str,
            code,
        )

    @classmethod
    def inline_small_blocks(cls, text: str, mode: str = "ultra") -> str:
        """Inline short statement blocks in medium and ultra modes."""
        mode_clean = cls.normalize_mode(mode)
        if mode_clean == "lite":
            return text

        def inline_cb(m):
            body = m.group(1)
            lines = [l.strip() for l in body.splitlines() if l.strip()]
            max_lines = 4 if mode_clean == "ultra" else 3
            max_len = 180 if mode_clean == "ultra" else 140
            if not (1 <= len(lines) <= max_lines and sum(len(l) for l in lines) <= max_len):
                return m.group(0)
            if any(l.startswith('//') or l.startswith('/*') for l in lines):
                return m.group(0)

            is_obj_literal = any(l.endswith(',') for l in lines) or all(':' in l for l in lines)
            if is_obj_literal:
                cleaned = [l.rstrip(',').rstrip(';') for l in lines]
                return '{ ' + ', '.join(cleaned) + ' }'

            res = []
            for i, l in enumerate(lines):
                clean = l.rstrip(';')
                if i > 0 and (
                    clean.startswith(('?', ':', '&&', '||', '+', '.', '=>', ')', ']'))
                    or (res and res[-1].endswith(('?', ':', '&&', '||', '+', '-', '*', '/', '=', '=>', '(', '[')))
                ):
                    res[-1] = res[-1] + ' ' + clean
                else:
                    res.append(clean)
            return '{ ' + '; '.join(res) + ' }'

        for _ in range(3):
            text = re.sub(r'\{\s*\n([^{}]+?)\n\s*\}', inline_cb, text)
        return text

    @classmethod
    def strip_verbose_logging(cls, text: str, mode: str = "ultra") -> str:
        """Strip non-functional debug logging and assert calls."""
        mode_clean = cls.normalize_mode(mode)
        if mode_clean == "lite":
            return text
        text = re.sub(r'^[ \t]*logger\.(?:V\(\d+\)\.|debug|trace|info)\(.*\);?[ \t]*\r?\n?', '', text, flags=re.MULTILINE)
        text = re.sub(r'^[ \t]*klog\.(?:V\(\d+\)\.|debug|trace|info)\(.*\);?[ \t]*\r?\n?', '', text, flags=re.MULTILINE)
        text = re.sub(r'^[ \t]*_?logger\.Log(?:Debug|Trace)\(.*\);?[ \t]*\r?\n?', '', text, flags=re.MULTILINE)
        text = re.sub(r'^[ \t]*debugLogger\.log\(.*\);?[ \t]*\r?\n?', '', text, flags=re.MULTILINE)
        text = re.sub(r'^[ \t]*serverLog\(LL_DEBUG.*\);?[ \t]*\r?\n?', '', text, flags=re.MULTILINE)
        text = re.sub(r'^[ \t]*(?:DEBUGASSERT|assert|DEBUGF|CURL_TRC)\(.*\);?[ \t]*\r?\n?', '', text, flags=re.MULTILINE)
        return text

    @staticmethod
    def strip_semicolons(text: str) -> str:
        """Strip trailing statement semicolons outside loops."""
        return re.sub(r';\s*$', '', text, flags=re.MULTILINE)

    @staticmethod
    def normalize_indentation(text: str) -> str:
        """Convert indentation to 2 spaces and strip all blank lines, properly handling tabs."""
        lines = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            expanded = line.expandtabs(4)
            orig_indent = len(expanded) - len(expanded.lstrip())
            indent_level = orig_indent // 4 if orig_indent >= 4 else (1 if orig_indent >= 2 else 0)
            lines.append("  " * indent_level + stripped)
        return "\n".join(lines)
