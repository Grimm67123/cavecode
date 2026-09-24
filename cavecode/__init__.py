"""
CaveCode: AST-Aware High-Density Source-Code Compressor for AI Coding Agents.

Why input many code when few code do trick?

Slashes prompt tokens by 30-50%+ (up to 80-90%) across 9 programming languages while keeping
100% meaning, logic, function names, and comments completely intact.
Original target files are NEVER touched.
"""

__version__ = "1.0.0"

from cavecode.engine import CaveCodeEngine
from cavecode.tokenizer import TokenEstimator
from cavecode.safety import SafetyGuard
from cavecode.reconstructor import CodeReconstructor

__all__ = [
    "CaveCodeEngine",
    "TokenEstimator",
    "SafetyGuard",
    "CodeReconstructor",
    "__version__",
]
