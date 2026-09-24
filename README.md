
# 🪨 CaveCode ⚡

> **why input many code when few code do trick**

LLMs and AI coding agents consume massive amounts of context tokens reading boilerplate, repetitive syntax, and verbose formatting. **CaveCode is an AST-aware source-code compressor that turns source code into compact, AI-readable representations, reducing input token usage by up to ~80%+ while preserving critical structural, syntactic, and semantic information across three configurable compression tiers.**

- 🌐 **[Web Playground](https://grimm67123.github.io/cavecode/)**: Try compression modes directly in your browser.
- 🤖 **Agent Protocol**: Includes an [AGENT.md](AGENT.md) documentation file for AI coding agents.

> **Compressed output is an information representation for AI context, not executable source code.** Agents continue to read and edit the original source files.

---

## Compression Modes

| Mode | Token Savings | What it keeps |
| :--- | :---: | :--- |
| **`lite`** | **~25% – ~30%** | Full function bodies & code logic |
| **`medium`** | **~35% – ~50%** | Function bodies with compressed syntax |
| **`ultra`** | **~80% – ~85%+** | AST structure, signatures & types |

### Code Comparison

#### Raw Source Code

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

lite — ~30% saved

Removes docstrings, legal headers, normalizes whitespace. ~100% of function bodies and code logic preserved.

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
  def __init__(self, secret_key: str, expiration_secs: int = 3600):
    self.secret_key = secret_key
    self.expiration_secs = expiration_secs
    logger.info(f"AuthService initialized with TTL: {expiration_secs}s")

  def validate_token(self, token: str) -> Optional[UserProfile]:
    logger.debug(f"Validating token: {token[:8]}...")
    if not token or len(token) < 16:
      logger.warning("Token rejected: invalid length")
      return None
    return UserProfile(user_id="u123", email="user@example.com")

medium — ~44% saved

Compresses keywords (def → fn, return → ret), strips noisy logging/debug calls, condenses comments.

from typing import List, Optional
from pydantic import BaseModel

class UserProfile(BaseModel):
  user_id: str
  email: str
  roles: List[str] = []

class AuthService:
  fn __init__(self, secret_key: str, expiration_secs: int = 3600):
    self.secret_key = secret_key
    self.expiration_secs = expiration_secs

  fn validate_token(self, token: str) -> Optional[UserProfile]:
    if not token or len(token) < 16:
      ret None
    ret UserProfile(user_id="u123", email="user@example.com")

ultra — ~83% saved

AST skeletonization. Retains all class structures, type hints, and function signatures while collapsing bodies to pass.

from typing import List, Optional
from pydantic import BaseModel

class UserProfile(BaseModel):
  user_id: str
  email: str
  roles: List[str] = []

class AuthService:
  fn __init__(self, secret_key: str, expiration_secs: int = 3600):
    pass
  fn validate_token(self, token: str) -> Optional[UserProfile]:
    pass


---

Installation

CaveCode is installed directly from the Git repository (it is not published to PyPI):

# Install directly via pip
pip install git+https://github.com/cavecode/cavecode.git

Or clone and install in editable development mode:

git clone https://github.com/cavecode/cavecode.git
cd cavecode
pip install -e .

Verify installation:

cavecode version


---

Supported Languages

CaveCode supports 9 programming languages with dedicated AST parsers and syntax transformers:

Python (.py)

JavaScript (.js, .jsx, .mjs, .cjs)

TypeScript (.ts, .tsx)

Rust (.rs)

Go (.go)

Java (.java)

C++ (.cpp, .cc, .cxx, .hpp)

C# (.cs)

C (.c, .h)



---

Command Reference

cavecode read

Reads file(s) or directories on the fly with AST compression and outputs directly to stdout. Leaves source files ~100% untouched.

# Read a single file in ultra mode (default)
cavecode read src/service.py

# Read in lite mode to keep all function implementations
cavecode read src/service.py -m lite

# Read with line numbers and a specific line slice
cavecode read src/service.py -n -l 10:45

# Read an entire directory
cavecode read src/ -m ultra

cavecode view / cavecode cat

Convenience aliases for cavecode read:

cavecode cat app/main.ts -m medium
cavecode view backend/service.go

cavecode compress

Compresses code files into companion .cave.<ext> files on disk. Original source files remain untouched.

# Compress a single file to <file>.cave.<ext>
cavecode compress src/main.py

# Compress all supported files across a directory
cavecode compress src/ -m ultra

# Custom output destination for a single file
cavecode compress src/main.py -o /tmp/main.compressed.py

cavecode revert

Removes generated .cave files across a file or directory tree:

cavecode revert .

cavecode estimate

Calculates and displays approximate token counts and savings without modifying or creating files:

# Analyze a single file
cavecode estimate src/main.py -m ultra

# Analyze an entire codebase
cavecode estimate src/

cavecode stats

Convenience alias for cavecode estimate:

cavecode stats src/ -m lite

cavecode verify

Verifies that target source files have not been modified:

cavecode verify src/

cavecode init

Creates a default .cavecode.yaml configuration file to configure custom inclusion patterns, exclusion lists, and compression modes:

cavecode init .

cavecode version

Displays the current CaveCode version:

cavecode version


---

Agent Documentation (AGENT.md)

Repositories using CaveCode include an AGENT.md file at their root. This file serves as documentation for AI coding agents (such as Claude Code, Cursor, Copilot, Codex, Gemini, etc.), informing the agent of how to use CaveCode effectively.

Replacing Native Read Commands to Save Input Tokens

When an AI agent explores, searches, or reads files across a project, reading verbose raw source code quickly saturates its context window. AGENT.md guides the agent to use cavecode read as a drop-in replacement for its native file-reading tool or command:

cavecode read path/to/file.py -m ultra    # Skeletons & signatures (~80% – ~85%+ token savings)
cavecode read path/to/file.py -m lite     # Full logic & bodies intact (~25% – ~30% token savings)

By reading compressed representations directly from stdout, the agent consumes significantly fewer input tokens and experiences lower response latency.

Not Mandatory

Using cavecode read is NOT AT ALL MANDATORY. If an agent only needs to inspect a tiny configuration file, read a small snippet, or requires exact byte-for-byte line matching to generate a diff or patch, it can continue reading raw files using its native tools at any time.

Compression Modes for Agents

lite (~25% – ~30% savings): ~100% of function bodies and algorithms are preserved. Ideal when the agent needs to analyze or debug implementation details.

medium (~35% – ~50% savings): ~100% of function bodies preserved with compact keyword replacements (fn, ret, pub, priv) and stripped debug logs. Ideal for navigating multiple interdependent files.

ultra (~80% – ~85%+ savings): Collapses function bodies to structural signatures (pass / { ... }). Ideal for high-level repository mapping and finding API interfaces.


Preserving Raw Files

Agents write all edits directly to the original raw source files. The generated .cave files (if created on disk with cavecode compress) are strictly read-only references and should never be edited or committed.
