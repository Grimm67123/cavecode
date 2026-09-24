"""
Approximate Token Estimator for CaveCode.

Provides realistic, approximate token counts and savings estimates across
different standard LLM tokenizer architectures (BPE, SentencePiece, WordPiece).
"""

from dataclasses import dataclass
from typing import Dict

try:
    import tiktoken
    HAS_TIKTOKEN = True
except ImportError:
    HAS_TIKTOKEN = False


@dataclass
class TokenEstimate:
    raw_approx_tokens: int
    compressed_approx_tokens: int
    saved_approx_tokens: int
    percent_saved: float
    model_estimates: Dict[str, Dict[str, int]]


class TokenEstimator:
    """Estimates approximate tokens across modern LLM tokenizer families."""

    def __init__(self):
        self._cl100k = None
        self._o200k = None
        if HAS_TIKTOKEN:
            try:
                self._cl100k = tiktoken.get_encoding("cl100k_base")
            except Exception:
                pass
            try:
                self._o200k = tiktoken.get_encoding("o200k_base")
            except Exception:
                pass

    def count_approx(self, text: str) -> int:
        """Estimate approximate tokens for source code text."""
        if not text:
            return 0
        if self._o200k:
            try:
                return len(self._o200k.encode(text))
            except Exception:
                pass
        if self._cl100k:
            try:
                return len(self._cl100k.encode(text))
            except Exception:
                pass

        # Code-tuned fallback: ~3.6 chars/token
        return max(1, int(len(text) / 3.6))

    def estimate(self, raw_text: str, compressed_text: str) -> TokenEstimate:
        """Calculate approximate token delta and architecture-specific estimates."""
        base_raw = self.count_approx(raw_text)
        base_comp = self.count_approx(compressed_text)

        architectures = {
            "BPE Standard (Byte-Pair)": {
                "raw": base_raw,
                "compressed": base_comp,
            },
            "BPE Code-Tuned": {
                "raw": int(base_raw * 1.02),
                "compressed": int(base_comp * 1.02),
            },
            "SentencePiece / Unigram": {
                "raw": int(base_raw * 0.98),
                "compressed": int(base_comp * 0.98),
            },
            "WordPiece Subword": {
                "raw": int(base_raw * 1.03),
                "compressed": int(base_comp * 1.03),
            },
        }

        saved = max(0, base_raw - base_comp)
        pct = (saved / base_raw * 100) if base_raw > 0 else 0.0

        return TokenEstimate(
            raw_approx_tokens=base_raw,
            compressed_approx_tokens=base_comp,
            saved_approx_tokens=saved,
            percent_saved=round(pct, 1),
            model_estimates=architectures,
        )
