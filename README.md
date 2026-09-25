# 🪨 CaveCode ⚡

> ***why input many code when few code do trick***

LLMs and AI coding agents consume massive amounts of tokens reading boilerplate, repetitive syntax, and verbose formatting. CaveCode compresses source code before passing it to AI agents, stripping unnecessary token overhead while preserving critical information. It reduces input token usage by up to **80%+** with three configurable compression tiers. This tool is mainly useful for large codebases, large multi-file agentic operations etc.

- 🌐 **[Web Playground](https://grimm67123.github.io/cavecode/)**: Try compression modes directly in your browser.
- 🤖 **Agent Protocol**: Includes an [AGENT.md](AGENT.md) documentation file for AI coding agents.

> **Compressed output is an information representation for agents, not executable source code.** Agents continue to (and must) read and edit the original source files.

---

## Installation

Install via pip:

```bash
pip install cavecode
```

Or install directly from Git:

```bash
pip install git+https://github.com/cavecode/cavecode.git
```

Or clone and install in editable development mode:

```bash
git clone https://github.com/cavecode/cavecode.git
cd cavecode
pip install -e .
```

Verify installation:

```bash
cavecode version
```

---

## Compression Modes

| Mode | Token Savings | What it keeps |
| :--- | :---: | :--- |
| **`lite`** | **~5% – ~10%** | Full function bodies & code logic |
| **`medium`** | **~15% – ~20%** | Function bodies with compressed syntax |
| **`ultra`** | **~80% – ~85%+** | AST structure, signatures & types |
### RECOMMENDED MODE: ULTRA
---
## Supported Languages

CaveCode supports 9 programming languages with dedicated AST parsers and syntax transformers:

- Python (`.py`)
- JavaScript (`.js`, `.jsx`, `.mjs`, `.cjs`)
- TypeScript (`.ts`, `.tsx`)
- Rust (`.rs`)
- Go (`.go`)
- Java (`.java`)
- C++ (`.cpp`, `.cc`, `.cxx`, `.hpp`)
- C# (`.cs`)
- C (`.c`, `.h`)

---

### AGENT.md

# CaveCode Agent Guide

Technical reference and operating protocol for AI coding agents using `cavecode`.

---

## Operating Protocol for AI Agents

To minimize context window usage, reduce token latency, and prevent token waste, agents follow this protocol:

1. **Read reference & dependency code via `cavecode read`**:
   When exploring the codebase, mapping architecture, or checking how external modules, classes, and functions are called, use `cavecode read` instead of reading large raw files:
   ```bash
   cavecode read path/to/file.py -m ultra    # Signatures, types, classes (~80% – ~85%+ token savings)
   cavecode read path/to/file.ts -m lite     # Full logic preserved for logic skims (~25% – ~30% token savings)
   cavecode read src/ -m ultra               # Scan all files in a directory directly to stdout
   ```
   *`cavecode read` streams compressed code directly to stdout with zero disk modifications.*

2. **Read raw files when actively editing or debugging**:
   `cavecode` is designed for gathering context on dependencies and interfaces. When you are **actively writing code, creating diffs/patches, or performing step-by-step logic debugging in a target file**, always use your standard native file read tool to inspect the raw file. This ensures exact indentation, byte-for-byte string matches, and authentic line numbers.

3. **Never use compressed text as a patch or diff target**:
   `cavecode` normalizes whitespace, formats syntax, and uses shorthand representations. These modified strings do not exist in the raw file. All edits, search-and-replace blocks, and unified diffs must target the original source files (`<filename>.<ext>`).

4. **Line numbers from `-n` are stream-relative**:
   The `-n` flag numbers the lines of the *compressed output stream*, not the physical lines in the source file. Do not pass line numbers from compressed output into automated file patchers or linters.

5. **Optional on-disk companion files (`cavecode compress`)**:
   If you need persistent `.cave` companion files on disk across multiple turns or sub-commands:
   ```bash
   cavecode compress . -m ultra      # Generate .cave companion files across directory
   cavecode compress file.py -m lite # Generate single file.cave.py
   ```
   Compressed representations are strictly read-only reference artifacts. Compilers, linters, test runners, and debuggers run exclusively on original source files. When finished, clean them up:
   ```bash
   cavecode revert .
   ```

---

## Compression Modes

Choose the compression tier using `--mode` or `-m` (default: `ultra`):

| Mode | Token Savings | Logic & Structure | Recommended Agent Use Case |
| :--- | :---: | :--- | :--- |
| **`ultra`** *(Default)* | **~80% – ~85%+** | **100% architectural and signature preservation.** Strips comments and docstrings; collapses function and method bodies to structural shells (`pass` / `{ ... }`). Keeps all class hierarchies, type annotations, and function definitions. | **Primary mode for agents.** Ideal for large repository scanning, architecture discovery, mapping dependencies, and checking API contracts/parameters of files you are not actively modifying. |
| **`lite`** | **~5% – ~10%** | **100% of function bodies & logic preserved.** Removes docstrings and license blocks, normalizes indentation to 2 spaces, and condenses imports. | Skimming algorithms or internal data flow inside an external module when you need to understand how it works under the hood without burning full token overhead. |
| **`medium`** | **~15% – ~20%** | **100% of function bodies preserved.** Uses compact keyword density (`fn`, `ret`, `pub`, `priv`, `const`), strips debug/info logging calls, and summarizes comments. | High-density reading across multiple interdependent files when you need a compact overview of logic. |

---

## CLI Command Reference

### `cavecode read` (Aliases: `cavecode view`, `cavecode cat`)
Reads source file(s) or directory on the fly with AST compression, printed directly to stdout. **Zero disk modifications.**

```bash
# Read a single file in ultra mode (default: ~80%+ savings)
cavecode read path/to/file.py

# Read a single file in lite mode (keeps full function implementations)
cavecode read path/to/file.ts -m lite

# Read a specific line range of compressed output
cavecode read path/to/file.py -l 1:50

# Read with line numbers (stream-relative)
cavecode read path/to/file.go -n

# Scan all supported files in a directory to stdout
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

### `cavecode estimate` (Alias: `cavecode stats`)
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

---

## Language Support & Scope

CaveCode provides dedicated AST parsers for 9 programming languages:
* Python (`.py`), JavaScript (`.js`, `.jsx`, `.mjs`, `.cjs`), TypeScript (`.ts`, `.tsx`)
* Rust (`.rs`), Go (`.go`), Java (`.java`), C++ (`.cpp`), C# (`.cs`), C (`.c`, `.h`)

*Note on Markup & Configs:* Markup and configuration formats (HTML, CSS, JSON, YAML, Markdown) do not have AST structures and are passed through untouched. Use standard file reading tools for these formats.

