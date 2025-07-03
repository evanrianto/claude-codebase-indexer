# Claude Codebase Indexer

A semantic search system that enhances Claude Code with intelligent codebase understanding. Index your entire project and get relevant context automatically injected into Claude Code conversations.

## Features

-   🧠 **Semantic Search** - Find code by meaning, not just keywords
-   🤖 **Claude Code Integration** - Automatic context injection
-   📁 **Multi-language Support** - Python, JavaScript, TypeScript, and more
-   ⚡ **Fast Retrieval** - FAISS-powered vector search
-   🎯 **Smart Filtering** - Search by file type, relevance score
-   💬 **Interactive Mode** - Real-time search and exploration

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd claude-codebase-indexer

# Install dependencies
pip install -r requirements.txt

# Set OpenAI API key (required for embeddings)
export OPENAI_API_KEY="your-api-key-here"
```

### Basic Usage

```bash
# 1. Index your codebase
python -m src.cli.main index /path/to/your/project

# 2. Search your code
python -m src.cli.main search "authentication logic"

# 3. Run Claude Code with context
python -m src.cli.main claude "How does user login work?"
```

## Installation

### Prerequisites

-   Python 3.8+
-   OpenAI API key
-   Claude Code CLI installed

### Setup

1. **Install Python dependencies:**

    ```bash
    pip install llama-index==0.10.40 faiss-cpu tiktoken openai
    ```

2. **Set up API keys:**

    ```bash
    export OPENAI_API_KEY="sk-your-openai-key"
    ```

3. **Verify Claude Code is installed:**
    ```bash
    claude --version
    ```

## Usage

### Indexing

Index your codebase to create a searchable vector database:

```bash
# Index current directory
python -m src.cli.main index .

# Index specific project
python -m src.cli.main index /path/to/project

# Custom index location
python -m src.cli.main index /path/to/project --index-path ./my_index

# Force reindex
python -m src.cli.main index /path/to/project --force
```

### Searching

Search your indexed codebase:

```bash
# Basic search
python -m src.cli.main search "database connection"

# Filter by file types
python -m src.cli.main search "error handling" --file-types py js

# Get more results
python -m src.cli.main search "authentication" --top-k 10

# Interactive search mode
python -m src.cli.main search --interactive
```

### Claude Code Integration

Run Claude Code with automatic context injection:

```bash
# Basic usage
python -m src.cli.main claude "Add error handling to the login function"

# Specify context search
python -m src.cli.main claude "Refactor this code" --context-query "refactoring patterns"

# Filter context by file type
python -m src.cli.main claude "Fix the bug" --file-types py --top-k 5

# Pass additional Claude Code arguments
python -m src.cli.main claude "Optimize performance" --claude-args --model claude-3-opus

# Interactive mode
python -m src.cli.main claude "Help me understand this codebase" --interactive
```

### Other Commands

```bash
# Show index statistics
python -m src.cli.main stats

# Find similar files
python -m src.cli.main similar src/auth.py

# Update existing index
python -m src.cli.main update /path/to/project

# Quick search (standalone)
python -m src.cli.search "function definition"
```

## Configuration

### Supported File Types

By default, the indexer processes these file types:

-   **Code**: `.py`, `.js`, `.ts`, `.jsx`, `.tsx`, `.java`, `.cpp`, `.c`, `.h`, `.hpp`, `.cs`, `.php`, `.rb`, `.go`, `.rs`, `.swift`, `.kt`, `.scala`
-   **Scripts**: `.sh`, `.sql`
-   **Config**: `.yaml`, `.yml`, `.json`, `.toml`, `.cfg`, `.ini`
-   **Docs**: `.md`, `.txt`, `.rst`

### Excluded Directories

These directories are automatically skipped:

-   `node_modules`, `.git`, `__pycache__`, `.pytest_cache`
-   `venv`, `env`, `.venv`, `dist`, `build`, `.next`
-   `target`, `bin`, `obj`, `.mypy_cache`, `coverage`

### Customization

Edit `src/indexer/core.py` to:

-   Add new file extensions
-   Modify chunk sizes
-   Adjust skip patterns
-   Change embedding models

## Examples

### Find Authentication Code

```bash
$ python -m src.cli.main search "user authentication login"

# Results show relevant auth-related code across your project
```

### Debug with Context

```bash
$ python -m src.cli.main claude "Why is the login failing?" --file-types py js

# Claude gets relevant authentication code as context
```

### Explore Similar Files

```bash
$ python -m src.cli.main similar src/models/user.py

# Shows files with similar patterns/structure
```

### Interactive Exploration

```bash
$ python -m src.cli.main search --interactive

🔍 Claude Code Semantic Search
📁 Project: /path/to/your/project
📊 127 files, 1,439 chunks indexed

🤖 Search query > database migration
# Shows relevant database code

🤖 Search query > type:py class definition
# Shows Python classes

🤖 Search query > similar:src/auth.py
# Shows files similar to auth.py
```

## How It Works

1. **Indexing Phase:**

    - Scans your codebase for supported file types
    - Splits code into semantic chunks using code-aware parsing
    - Generates embeddings using OpenAI's text-embedding-ada-002
    - Stores vectors in FAISS index for fast retrieval

2. **Search Phase:**

    - Converts your query to an embedding
    - Finds most similar code chunks using vector similarity
    - Ranks results by relevance score
    - Formats output for Claude Code consumption

3. **Integration Phase:**
    - Automatically searches for relevant context
    - Injects context into Claude Code session
    - Maintains conversation flow with enhanced understanding

## Troubleshooting

### Common Issues

**Index not found:**

```bash
❌ Index not found at ./claude_index
# Solution: Run indexer first
python -m src.cli.main index /path/to/project
```

**No OpenAI API key:**

```bash
❌ OpenAI API key not found
# Solution: Set environment variable
export OPENAI_API_KEY="your-key-here"
```

**Poor search results:**

-   Try different search terms
-   Increase `--top-k` value
-   Check if files were indexed (`stats` command)
-   Use file type filters

**Claude Code not found:**

```bash
❌ claude-code command not found
# Solution: Install Claude Code CLI
pip install anthropic-claude-code
```

### Performance Tips

-   **Large codebases**: Index incrementally or use `--force` sparingly
-   **Better context**: Use specific search queries rather than generic terms
-   **Memory usage**: Reduce chunk sizes in `core.py` if needed
-   **Search speed**: Keep indexes on fast storage (SSD)

## Advanced Usage

### Custom Embedding Models

Edit `src/indexer/core.py` to use different embedding models:

```python
# Use different OpenAI model
embed_model = OpenAIEmbedding(model="text-embedding-3-large")

# Or use local embeddings (requires additional setup)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
```

### Shell Integration

Add to your `.bashrc` or `.zshrc`:

```bash
# Quick aliases
alias cindex='python -m src.cli.main index'
alias csearch='python -m src.cli.main search'
alias cclaude='python -m src.cli.main claude'

# Project-specific function
claude-enhanced() {
    python /path/to/claude-codebase-indexer/src/cli/main.py claude "$@"
}
```

### CI/CD Integration

Update indexes automatically:

```yaml
# .github/workflows/update-index.yml
name: Update Code Index
on:
    push:
        branches: [main]
jobs:
    update-index:
        runs-on: ubuntu-latest
        steps:
            - uses: actions/checkout@v2
            - name: Update index
              run: python -m src.cli.main update . --force
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details
