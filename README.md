# Grounded Local Coding Agent: Low-Token, Low-Context Hybrid Verification

A **low-token, low-context, model-agnostic hybrid local + web-search coding agent** that eliminates package and API hallucinations in **any local LLM** (Qwen, Llama, DeepSeek, Mistral, Phi, Gemma) running via Ollama—while keeping context windows small and fast on consumer GPUs.

Instead of stuffing massive documentation files or bloated multi-turn chat histories into your model, this pipeline feeds **only one micro-chunk, one <250-word API reference, and the latest error** into each forward pass—achieving high reliability inside a **4K–6K token context window** at near-zero API cost.

## Why Low-Context & Low-Token Hybrid?

- **Small Context Window at Every Step:** Each local generation call runs statelessly with a tight ~4K–6K token budget—no multi-file repo dumps or growing chat transcripts—keeping VRAM usage low and inference fast on 4B–8B models.
- **Minimal Cloud Token Footprint:** Only task decomposition and compact 2–3 line API/package lookups touch the external API, and outputs are cached locally (`.task_plan.json`, `.pkg_ref_chunk_*.md`) so retries cost **zero extra API tokens**.
- **Automated AST & Contract Validation:** Catches hallucinated imports and broken output schemas locally before advancing to the next chunk.
- **Model-Agnostic Plug & Play:**
  - *Local Code Generation:* Works with `qwen3:4b`, `qwen3:8b`, `qwen2.5-coder`, `deepseek-coder-v2`, `llama3.1`, `codellama`, `mistral`, or any model in `ollama list`.
  - *Web-Researched Planning & API Grounding:* Configured with `gemma-4-31b-it` and `gemma-4-26b-a4b-it` (with automatic fallback) and adaptable to any LLM or search backend.


Instead of asking a local model to generate an entire multi-file project in one shot—or relying on fragile hidden-layer steering—this pipeline breaks a task into **sequential micro-chunks**, grounds each chunk with **compact, up-to-date package references** via the Gemma/Gemini API, and enforces **automated syntax, import, and output-contract validation** before moving to the next step.

## How It Works

```text
[User Task (task.txt)]
         │
         ▼
1. Task Decomposer (Gemma 4) ──► Breaks task into sequential chunks with strict I/O contracts
         │
         ▼
┌──► 2. Package Grounding (Gemma 4) ──► Fetches minimal conda commands & 2–3 line API snippets
│            │
│            ▼
│    3. Local Code Gen (Ollama) ──────► Writes target script honoring I/O contracts & package docs
│            │
│            ▼
│    4. Dual Validation Gate ─────────► Checks AST imports, runs script, & executes assert tests
│            │
└──── [Fail] ┘ (Routes back to package refresh or code fix with error history)
         │
      [Pass]
         ▼
5. Master Entrypoint ─────────────────► Generates `run_pipeline.py` chaining all verified scripts
```

## Key Features

- **Sequential Micro-Chunking:** Decomposes complex workflows into single-file steps where each chunk's verified output contract becomes the strict input constraint for the next chunk.
- **Zero-Hallucination API Grounding:** Fetches concise package names, `conda install` commands, and current 2–3 line usage examples right before local code generation.
- **Dual-Layer Validation Gate:**
  - *Package & Syntax Gate:* Uses Python `ast` and `importlib.util.find_spec` to catch uninstalled or hallucinated imports before runtime.
  - *Contract Fulfillment Gate:* Executes standalone `assert` acceptance tests verifying output files, schemas, row counts, and `stdout` values.
- **Smart Retry & Error Memory:** Tracks past attempt errors so the local Ollama model fixes failures without repeating earlier mistakes, refreshing package docs automatically when API/attribute errors occur.
- **API & Plan Caching:** Caches `.task_plan.json` and `.pkg_ref_chunk_*.md` locally to avoid redundant API calls across runs.

## Prerequisites

1. **Python 3.10+** (Conda environment recommended)
2. **Ollama** installed and running locally with a coding model pulled:
   ```bash
   ollama pull qwen3:4b
   ```
3. **Google AI Studio API Key** (free tier works with `gemma-4-31b-it` and `gemma-4-26b-a4b-it`)

## Installation

1. Clone the repository and enter the directory:
   ```bash
   git clone https://github.com/Praneeth-Avasarala/grounded-local-coding-agent.git
   cd grounded-local-coder
   ```

2. Install the orchestrator dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set your API key:
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```

## Usage

1. Write your task specification in `task.txt` and include its file path in `src/config.py`.
2. Adjust the configuration constants at the top of `main.py` if needed (`OLLAMA_MODEL`, `PROJECT_DIR`, `MAX_CHUNK_RETRIES`).
3. Run the orchestrator:
   ```bash
   python -u -m src.main
   ```

<!-- 
Once all chunks pass validation, the orchestrator generates `my_project/run_pipeline.py` so you can run the entire verified pipeline end-to-end:
```bash
cd my_project
python run_pipeline.py
```
-->

## Recommended `.gitignore`

```gitignore
__pycache__/
*.py[cod]
.env
my_project/
.task_plan.json
.pkg_ref_chunk_*.md
_validate_chunk_*.py
```



