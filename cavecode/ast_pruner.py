"""
AST-Aware Pruning and Syntax Transformation Engine for CaveCode.
Powered by Tree-Sitter for all 9 supported languages.

Performs AST-guided pruning of:
1. Multi-line parameter lists and function signatures.
2. Non-functional debug logging statements.
3. Single-statement control flow inlining.
4. Byte-exact comment extraction and telegraphic condensation.
"""

import re
from typing import Optional, List, Tuple

try:
    import tree_sitter
    import tree_sitter_python
    import tree_sitter_javascript
    import tree_sitter_typescript
    import tree_sitter_go
    import tree_sitter_c
    import tree_sitter_cpp
    import tree_sitter_rust
    import tree_sitter_java
    import tree_sitter_c_sharp
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False


class ASTPruner:
    """Tree-sitter AST guided pruner for high-density source compression."""

    _PARSERS = {}

    @classmethod
    def get_parser(cls, language: str) -> Optional['tree_sitter.Parser']:
        if not TREE_SITTER_AVAILABLE:
            return None
        lang_key = language.lower()
        if lang_key in cls._PARSERS:
            return cls._PARSERS[lang_key]

        try:
            if lang_key == 'python':
                ts_lang = tree_sitter.Language(tree_sitter_python.language())
            elif lang_key in ('javascript', 'js'):
                ts_lang = tree_sitter.Language(tree_sitter_javascript.language())
            elif lang_key in ('typescript', 'ts'):
                ts_lang = tree_sitter.Language(tree_sitter_typescript.language_typescript())
            elif lang_key == 'go':
                ts_lang = tree_sitter.Language(tree_sitter_go.language())
            elif lang_key == 'c':
                ts_lang = tree_sitter.Language(tree_sitter_c.language())
            elif lang_key == 'cpp':
                ts_lang = tree_sitter.Language(tree_sitter_cpp.language())
            elif lang_key == 'rust':
                ts_lang = tree_sitter.Language(tree_sitter_rust.language())
            elif lang_key == 'java':
                ts_lang = tree_sitter.Language(tree_sitter_java.language())
            elif lang_key in ('csharp', 'cs'):
                ts_lang = tree_sitter.Language(tree_sitter_c_sharp.language())
            else:
                return None

            parser = tree_sitter.Parser(ts_lang)
            cls._PARSERS[lang_key] = parser
            return parser
        except Exception:
            return None

    @classmethod
    def prune_ast(cls, source_code: str, language: str, mode: str = "medium") -> str:
        """Apply AST-level pruning to source code based on compression mode."""
        parser = cls.get_parser(language)
        if parser is None or not source_code.strip():
            return source_code

        mode_clean = "lite" if mode.lower().strip() in ("lite", "light") else mode.lower().strip()

        try:
            raw_bytes = source_code.encode('utf-8')
            tree = parser.parse(raw_bytes)
            root = tree.root_node

            replacements: List[Tuple[int, int, bytes]] = []

            def walk(node):
                # Ultra mode: strip comments
                if mode_clean == "ultra" and node.type in ('comment', 'line_comment', 'block_comment'):
                    replacements.append((node.start_byte, node.end_byte, b''))
                    return

                # Ultra mode: strip Python docstrings
                if mode_clean == "ultra" and language == 'python' and node.type == 'expression_statement':
                    if len(node.children) == 1 and node.children[0].type == 'string':
                        replacements.append((node.start_byte, node.end_byte, b''))
                        return

                # Ultra mode: compact function/method bodies
                if mode_clean == "ultra" and node.type in (
                    'function_definition',
                    'function_declaration',
                    'method_declaration',
                    'method_definition',
                    'function_item',
                    'arrow_function',
                    'function_expression',
                    'constructor_declaration',
                ):
                    body = node.child_by_field_name('body')
                    if body:
                        if language == 'python':
                            replacements.append((body.start_byte, body.end_byte, b'\n  pass'))
                        else:
                            replacements.append((body.start_byte, body.end_byte, b'{ ... }'))
                        # Still inline signature before body if multiline
                        sig = raw_bytes[node.start_byte:body.start_byte]
                        if b'\n' in sig:
                            collapsed = re.sub(rb'\s*\n\s*', b' ', sig)
                            collapsed = re.sub(rb'\s*,\s*', b', ', collapsed)
                            collapsed = re.sub(rb'\(\s+', b'(', collapsed)
                            collapsed = re.sub(rb'\s+\)', b')', collapsed)
                            collapsed = re.sub(rb',\s*\)', b')', collapsed).strip() + b' '
                            replacements.append((node.start_byte, body.start_byte, collapsed))
                        return

                # Medium / Lite mode: collapse multiline function & method signatures (brace languages)
                if mode_clean in ("lite", "medium"):
                    if node.type in (
                        'function_definition',
                        'function_declaration',
                        'method_declaration',
                        'method_definition',
                        'function_item',
                        'constructor_declaration',
                        'local_function_statement',
                    ) and language != 'python':
                        body = node.child_by_field_name('body')
                        if body:
                            sig = raw_bytes[node.start_byte:body.start_byte]
                            if b'\n' in sig:
                                collapsed = re.sub(rb'\s*\n\s*', b' ', sig)
                                collapsed = re.sub(rb'\s*,\s*', b', ', collapsed)
                                collapsed = re.sub(rb'\(\s+', b'(', collapsed)
                                collapsed = re.sub(rb'\s+\)', b')', collapsed)
                                collapsed = re.sub(rb',\s*\)', b')', collapsed).strip() + b' '
                                replacements.append((node.start_byte, body.start_byte, collapsed))
                                walk(body)
                                return

                # All modes: collapse multiline parameter lists: (\n a, \n b) -> (a, b)
                if node.type in ('parameter_list', 'parameters', 'formal_parameters'):
                    node_text = raw_bytes[node.start_byte:node.end_byte]
                    if b'\n' in node_text:
                        collapsed = re.sub(rb'\s*\n\s*', b' ', node_text)
                        collapsed = re.sub(rb'\s*,\s*', b', ', collapsed)
                        collapsed = re.sub(rb'\(\s+', b'(', collapsed)
                        collapsed = re.sub(rb'\s+\)', b')', collapsed)
                        collapsed = re.sub(rb',\s*\)', b')', collapsed)
                        replacements.append((node.start_byte, node.end_byte, collapsed))
                        return

                # Medium / Ultra: collapse multiline call argument lists
                elif mode_clean in ("medium", "ultra") and node.type in ('argument_list', 'arguments'):
                    node_text = raw_bytes[node.start_byte:node.end_byte]
                    if b'\n' in node_text and len(node_text) < 220:
                        has_blocks = any(
                            c.type in (
                                'arrow_function', 'function', 'function_expression', 'lambda',
                                'statement_block', 'compound_statement', 'block'
                            )
                            for c in node.children
                        )
                        if not has_blocks:
                            collapsed = re.sub(rb'\s*\n\s*', b' ', node_text)
                            collapsed = re.sub(rb'\s*,\s*', b', ', collapsed)
                            collapsed = re.sub(rb'\(\s+', b'(', collapsed)
                            collapsed = re.sub(rb'\s+\)', b')', collapsed)
                            collapsed = re.sub(rb',\s*\)', b')', collapsed)
                            replacements.append((node.start_byte, node.end_byte, collapsed))
                            return

                # Medium / Ultra: prune verbose debug logging & assertions
                elif mode_clean in ("medium", "ultra") and node.type in ('expression_statement', 'statement'):
                    node_text = raw_bytes[node.start_byte:node.end_byte].strip()
                    if re.match(
                        rb'^[ \t]*(?:DEBUGASSERT|serverAssert|assert|CURL_TRC|DEBUGF|'
                        rb'logger\.(?:V\(\d+\)\.|debug|trace)|'
                        rb'klog\.(?:V\(\d+\)\.|debug|trace)|'
                        rb'debugLogger|'
                        rb'console\.(?:debug|trace)|'
                        rb'_?logger\.Log(?:Debug|Trace)|'
                        rb'serverLog\(LL_DEBUG)\b',
                        node_text
                    ) or re.match(rb'^[ \t]*(?:debug!|trace!)', node_text):
                        replacements.append((node.start_byte, node.end_byte, b''))
                        return

                # Medium / Ultra: collapse 1-statement if blocks onto single line
                elif mode_clean in ("medium", "ultra") and node.type in ('if_statement',):
                    consequence = node.child_by_field_name('consequence')
                    alt = node.child_by_field_name('alternative')
                    if consequence and not alt:
                        node_text = raw_bytes[node.start_byte:node.end_byte]
                        if b'\n' in node_text and len(node_text) < 140:
                            lines = [l.strip() for l in node_text.splitlines() if l.strip()]
                            if language == 'python':
                                if len(lines) == 2 and not lines[1].startswith(b'#'):
                                    collapsed = lines[0] + b' ' + lines[1]
                                    replacements.append((node.start_byte, node.end_byte, collapsed))
                                    return
                            else:
                                if 2 <= len(lines) <= 3 and not any(l.startswith(b'//') or l.startswith(b'#') or l.startswith(b'/*') for l in lines):
                                    collapsed = re.sub(rb'\s*\n\s*', b' ', node_text)
                                    collapsed = re.sub(rb'\s*;\s*', b'; ', collapsed)
                                    replacements.append((node.start_byte, node.end_byte, collapsed))
                                    return

                # Medium / Ultra: inline small struct/object literals
                elif mode_clean in ("medium", "ultra") and node.type in ('composite_literal', 'object', 'initializer_list'):
                    node_text = raw_bytes[node.start_byte:node.end_byte]
                    if b'\n' in node_text and len(node_text) < 140:
                        has_blocks = any(
                            c.type in (
                                'arrow_function', 'function', 'function_expression', 'lambda',
                                'statement_block', 'compound_statement', 'block'
                            )
                            for c in node.children
                        )
                        if not has_blocks:
                            collapsed = re.sub(rb'\s*\n\s*', b' ', node_text)
                            collapsed = re.sub(rb'\s*,\s*', b', ', collapsed)
                            replacements.append((node.start_byte, node.end_byte, collapsed))
                            return

                for child in node.children:
                    walk(child)

            walk(root)

            # Apply replacements in reverse order of start_byte to maintain valid offsets
            replacements.sort(key=lambda x: x[0], reverse=True)
            result = bytearray(raw_bytes)
            for start, end, repl in replacements:
                result[start:end] = repl

            return result.decode('utf-8', errors='ignore')
        except Exception:
            return source_code
