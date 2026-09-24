# CaveCode Agent Guide

Technical reference and operating protocol for AI coding agents using `cavecode`.

---

## Operating Protocol for AI Agents

To minimize context window usage, reduce token latency, and prevent token waste, agents follow this protocol:

1. **Read compressed code on the fly via `cavecode read`**:
   When exploring, searching, reading functions, or gathering codebase context, use `cavecode read` instead of reading raw files directly:
   ```bash
   cavecode read path/to/file.py -m ultra    # Signatures, types, classes (70-80%+ token savings)
   cavecode read path/to/file.ts -m lite     # 100% full logic & body intact (20-30% token savings)
   cavecode read src/ -m ultra               # Scan all files in a directory directly to stdout
   ```
   *`cavecode read` streams compressed code directly to stdout with zero disk modifications.*

2. **Reading compressed code is optional**:
   If you only need to inspect a tiny configuration file, read 5 lines, or need byte-for-byte exact lines for an immediate diff/patch, you can read the raw file directly with your standard read tool. Use `cavecode read` whenever reading large files, exploring architecture, or mapping dependencies.

3. **Optional on-disk companion files (`cavecode compress`)**:
   If you want persistent `.cave` companion files on disk across multiple commands or turns:
   ```bash
   cavecode compress . -m ultra      # Generate .cave companion files across directory
   cavecode compress file.py -m lite # Generate single file.cave.py
   ```
   When finished, clean them up:
   ```bash
   cavecode revert .
   ```

4. **Never edit or execute `.cave.*` files**:
   Compressed representations are strictly read-only reference artifacts. Compilers, linters, test runners, and debuggers run exclusively on original source files.

5. **Apply all edits to original raw source files**:
   When modifying code, fixing bugs, or adding features, apply edits directly to the original raw files (`<filename>.<ext>`).

---

## Compression Modes

Choose the compression tier using `--mode` or `-m` (default: `ultra`):

| Mode | Token Savings | Logic & Structure | Recommended Agent Use Case |
| :--- | :--- | :--- | :--- |
| **`lite`** | **20%–30%** | **100% of function bodies & logic preserved.** Telegraphic comments, signature inlining, import cleanup, 2-space indentation. | Deep debugging, inspecting complex algorithms, reviewing mathematical or business calculations. |
| **`medium`** | **40%–60%** | **100% of function bodies & logic preserved.** Keyword density (`fn`, `ret`, `pub`, `priv`, `const`, `ro`, `any`, `bool`), debug log stripping, block inlining, telegraphic comments. | General code navigation, reading multiple related files, understanding component interactions. |
| **`ultra`** | **70%–80%+** | **100% architectural and signature preservation.** Strips all comments, docstrings, and compresses function bodies to structural signatures (`{ ... }` / `pass`). | Large repo scanning, architectural discovery, API surface analysis, cross-module dependency mapping. |

---

## CLI Command Reference

### `cavecode read` (Aliases: `cavecode view`, `cavecode cat`)
Reads source file(s) or directory on the fly with AST compression, printed directly to stdout. **Zero disk modifications.**

```bash
# Read a single file in ultra mode (default: 70-80%+ savings)
cavecode read path/to/file.py

# Read a single file in lite mode (100% logic intact)
cavecode read path/to/file.ts -m lite

# Read with line numbers
cavecode read path/to/file.go -n

# Read a specific line range
cavecode read path/to/file.py -l 1:50 -n

# Read all files in a directory to stdout
cavecode read ./src -m ultra
```

### `cavecode compress` (Optional on-disk generation)
Compresses a source file or an entire directory, creating `<name>.cave.<ext>` companion files alongside target files. Original files remain **100% untouched**.

```bash
# Generate .cave files across entire repository
cavecode compress . -m ultra

# Generate .cave files for a directory in lite mode
cavecode compress ./src -m lite

# Compress a single file to a .cave companion file
cavecode compress path/to/file.py -m ultra
```

### `cavecode revert`
Removes generated `.cave` companion files from a file or directory, restoring a clean raw codebase state.

```bash
# Clean up all .cave files in the project
cavecode revert .

# Clean up .cave files in a specific folder
cavecode revert ./src
```

### `cavecode estimate`
Calculates approximate token usage and potential savings without writing any files to disk.

```bash
cavecode estimate path/to/file.rs -m ultra
cavecode estimate ./src -m lite
```

### `cavecode verify`
Performs SHA-256 cryptographic verification proving target source files have not been modified.

```bash
cavecode verify .
```
