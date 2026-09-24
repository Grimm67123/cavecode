# 🪨 CaveCode ⚡

> **why input many code when few code do trick**
>
> LLMs and AI coding agents consume massive amounts of context tokens reading boilerplate, repetitive syntax, and verbose formatting. **CaveCode is an AST-aware source-code compressor that turns source code into a compact, AI-readable representation, reducing input token usage by up to ~80%+ while preserving critical structural, syntactic, and semantic information across three configurable compression tiers.**
>
> Compressed output is intended for **AI context and understanding**, not execution or editing. Agents continue to read and edit the original source files.

- 🌐 **[Web Playground](https://grimm67123.github.io/cavecode/)**: Try compression modes directly in your browser.
- 🤖 **Agent Protocol**: Includes an [AGENT.md](AGENT.md) documentation file for AI coding agents.

---

## Compression Modes & Token Savings

CaveCode provides three distinct compression tiers:

| Mode | Token Savings |
| :--- | :--- |
| **`lite`** | **~25% – ~30%** |
| **`medium`** | **~35% – ~50%** |
| **`ultra`** | **~80% – ~85%+** |

### Code Comparison

#### 1. Raw Source Code (~140 tokens)

```python
import os
import json
import logging
from typing import List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class UserProfile(BaseModel):
    user_id: str
    email: str
    roles: List[str] = []

class AuthService:
    """Service responsible for authenticating and authorizing user tokens."""

    def __init__(self, secret_key: str, expiration_secs: int = 3600):
        self.secret_key = secret_key
        self.expiration_secs = expiration_secs
        logger.info(f"AuthService initialized with TTL: {expiration_secs}s")

    def validate_token(self, token: str) -> Optional[UserProfile]:
        """Validate bearer token and return user profile if authentic."""
        logger.debug(f"Validating token: {token[:8]}...")
        if not token or len(token) < 16:
            logger.warning("Token rejected: invalid length")
            return None
        return UserProfile(user_id="u123", email="user@example.com")