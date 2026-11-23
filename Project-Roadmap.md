## So far 
- working pipeline. git tracked. 
	- Web-research. 
		- input :
			- [x] system prompt, user-prompt about task 
		- output: 
			- [x] micro-task chunks. chunk goal, package and syntax info, strict input output contracts, validation scripts for each chunk.  
	- ollama generates one chunk code at a time. 
		- input
			- [x] chunk goal, package and syntax info, input-output contract
		- output: 
			- [x] chunk's code script
	- Testing, Validation, Feedback loop
		- input : 
			- [x] chunk's code script and chunk's validation script
		- output : 
			- [x] if validation failure, save error history, pass it along with the same task to local model again. 
				- [x] filter error to cut down noise. 
			- [x] If multiple attempt failure, do web-research again, get hints, pass hints and generate code again. 
			- [x] max attempts limit. success or failure
	- [x] combine chunks. master script for the full task pipeline.  


- Github repo.
	- [x] published working version
	- [x] Dev git branch for local development

## To do next

- Useful References
	- https://www.reddit.com/r/LocalLLM/s/Wppf7AVMfS

- Web research workflow improvemens 
	- freellmapi github
	- google ai studio models
	- project could have more than one sequences that can be done in parallel
		- Research : Community-Tested & Research-Backed strategies
			- Across multi-agent orchestration frameworks (like LangGraph, CrewAI, and academic architectures like [LLMCompiler](https://arxiv.org/abs/2312.04511)), the consensus is to **decouple dependency discovery from execution scheduling**.
			- 1. Explicit DAG (`task_id` + `depends_on`) — _The Gold Standard_
				- Instead of asking the LLM to assign `sequence_id` and `parallel_id`, ask it to output a **Directed Acyclic Graph (DAG)** where each task simply lists its direct prerequisites. [[1](https://arpitbhayani.me/blogs/ai-topological-sort/), [2](https://www.emergentmind.com/topics/llm-based-prompted-decomposition)]
				- **How it works:** Every task gets a `task_id` (e.g., `"T1"`, `"T2"`) and a `depends_on: ["T1"]` array.
				- **Why it's better:** LLMs are much more accurate at answering _"What exact inputs does this specific task need?"_ than calculating global sequence waves. Your Python orchestrator then runs a standard **Topological Sort** (or Kahn's algorithm) to dispatch any task the exact millisecond its specific `depends_on` list is satisfied—maximizing worker utilization. [[1](https://arpitbhayani.me/blogs/ai-topological-sort/)]
			- 2. Interface-First ("Contract-First") Decomposition
				- One of the biggest blockers to parallel coding or multi-worker pipelines is that Worker B cannot start until Worker A finishes writing a module, schema, or API.
				- **How it works:** Prompt the planner to make **Sequence 1 strictly about defining interfaces/contracts** (e.g., Pydantic models, OpenAPI specs, function signatures, database schemas, or file stubs) with empty/mock bodies.
				- **Why it's better:** Once the interfaces are locked in Step 1, all downstream implementation tasks _and_ test-writing tasks can run **100% in parallel** in Step 2 because every worker already knows the exact input/output shapes.
			- 3. Map-Reduce / Divide-and-Conquer (DaC) Prompting
				- For projects involving heavy data processing, refactoring, or multi-file analysis, research such as [Divide-and-Conquer Prompting](https://arxiv.org/abs/2402.05359) and [ParallelPrompt](https://arxiv.org/abs/2506.18728) highlights separating decomposition from aggregation. [[1](https://arxiv.org/html/2506.18728v1), [2](https://arxiv.org/html/2402.05359v1)]
				- **How it works:** Explicitly instruct the planner to group tasks into three distinct archetypes:
					- 1. **Fan-Out (Scatter):** Independent atomic tasks operating on isolated files/modules.
					- 2. **Barrier/Sync:** Lightweight validation or schema checks.
					- 3.**Fan-In (Reduce/Merge):** Integration tasks that wire the parallel outputs together (e.g., updating `main.py` or routing tables). [[1](https://docs.together.ai/docs/parallel-workflows), [2](https://arxiv.org/html/2402.05359v1)]
				- **Why it's better:** It prevents parallel workers from colliding on shared "glue" files (like `app.py` or `index.ts`), which is the #1 cause of merge conflicts in parallel LLM workflows.
		- Action plan :
			- If you want maximum parallel efficiency, switch to a **Contract-First DAG**:	
				- 1. **Rule 1 (Contracts First):** Always generate shared schemas, interfaces, and data contracts as the root nodes (`depends_on: []`).
				- 2. **Rule 2 (Dependency Declaration):** Output `task_id` and `depends_on: [...]` instead of sequence numbers.
				- 3. **Rule 3 (Single-Writer Ownership):** Guarantee that no two tasks without a dependency link between them ever write to the same target file; reserve shared entry-point files for final "Fan-In" integration tasks.
			- Your Python worker pool can then treat the JSON output as a dynamic queue—continuously feeding unblocked tasks to idle workers without waiting for entire waves to finish.

---


- Local Model workflow improvements - 
	- make model to be able to install needed packages.
	- choose best open weight/open source coding models that can run on available hardware.
		- Research :
			- The top open-weight coding models are ==Kimi K3 and GLM-5.2 / GLM-5.3 for frontier-scale repository and agentic coding, alongside Qwen3-Coder, Qwen3.8-27B, Devstral Small 2, and DeepSeek-V4 Flash== for practical local or cost-efficient setups. Most of these publish model weights rather than full training datasets and recipes, making them open-weight models. [1, 2, 3, 4, 5, 6]
			- Frontier & Large-Scale Agentic Coding
				- Kimi K3 (Moonshot AI): 
					- 2.8T total / 104B active MoE with a 1M context window; leads terminal and complex multi-step coding benchmarks, typically run via API or multi-GPU clusters. [1, 7, 8]
				- GLM-5.2 & GLM-5.3 (Z.ai): 
					- MIT-licensed MoE models (around 743B–753B total parameters; GLM-5.3-Flash is 320B / 18B active) with a 1M token context window, strong tool calling, and long-horizon repository editing. Most users on [r/LocalLLM](https://www.reddit.com/r/LocalLLM/comments/1ur0vdq/which_open_sourceopen_weight_local_llm_should_i/) agree that GLM-5.2 is a top pick for long agentic coding sessions on high-memory setups. [1, 8, 9, 10]
				- Qwen3-Coder 480B-A35B Instruct:
					- Apache-2.0 MoE (480B total / 35B active) with 262K native context (up to 1M with YaRN) built for large-repository coding and agentic harnesses. [1]
				- DeepSeek-V4 Pro & Flash: 
					- MIT-licensed 1M-context models widely used for algorithmic reasoning, CI/CD, and high-throughput coding workflows at low API cost (Flash is 284B total / 13B active). [8, 10]
			- Strong Local & Single-GPU / Mid-Memory Picks
				- Qwen3.8-27B: 
					- Dense 27B Apache-2.0 model (~15–18 GB at 4-bit) with a 262K context window and strong refactoring and multi-language code generation. [3, 4]
				- Devstral Small 2: 
					- Compact 24B Apache-2.0 model (~13–15 GB at 4-bit) with a 256K context window tuned for tool calling and multi-file agentic edits. [3, 4]
				- Qwen3-Coder-30B-A3B & Qwen3-Coder-Next (80B-A3B): 
					- Apache-2.0 MoE models with low active parameter counts per token for faster local inference on machines with sufficient memory (30B-A3B uses ~17 GB at 4-bit; 80B-A3B uses ~44 GB with offloading or unified memory). [3, 11]
				- Qwen3 8B: 
					- Lightweight option (~5 GB VRAM) for tight memory budgets (such as 6–8 GB VRAM) and quick local tasks. [4]
			- For detailed breakdowns of parameter sizes, licenses, and memory footprints, see the [VDF.AI local coding model guide](https://vdf.ai/blog/best-local-llm-for-coding/), the [Hugging Face local LLM overview](https://huggingface.co/blog/daya-shankar/open-source-llm-models-to-run-locally), and the [GPUWerk open-weight coding comparison](https://gpuwerk.com/blog/best-open-weight-coding-models/). [2, 3, 12]
		        [1] [https://kilo.ai](https://kilo.ai/open-source-models)
		
		        [2] [https://gpuwerk.com](https://gpuwerk.com/blog/best-open-weight-coding-models/)
		
				[3] [https://vdf.ai](https://vdf.ai/blog/best-local-llm-for-coding/)
		
				[4] [https://www.promptquorum.com](https://www.promptquorum.com/local-llms/best-local-llms-for-coding)
		
				[5] [https://www.gumloop.com](https://www.gumloop.com/blog/open-weight-ai-models)
		
				[6] [https://www.faros.ai](https://www.faros.ai/blog/open-weight-models)
		
				[7] [https://www.developersdigest.tech](https://www.developersdigest.tech/blog/glm-5-2-vs-deepseek-v4-vs-qwen3-open-weights-coding-showdown)
		
				[8] [https://www.youtube.com](https://www.youtube.com/watch?v=z605KVofJAY&t=187)
		
				[9] [https://www.reddit.com](https://www.reddit.com/r/LocalLLM/comments/1ur0vdq/which_open_sourceopen_weight_local_llm_should_i/)
		
				[10] [https://github.com](https://github.com/xigh/open-weight-models)
		
				[11] [https://www.youtube.com](https://www.youtube.com/watch?v=ozyazf9xKP4&t=145)
		
				[12] [https://huggingface.co](https://huggingface.co/blog/daya-shankar/open-source-llm-models-to-run-locally)
	- learn about existing tools. consider integrating their best parts
    - Research :
	    - aider, opencode, OpenClaw, copilot, 
	    - pstack, ponytail, 
	- Action plan :
		- [ ] integreate aider 
	- use assistant role : In local Ollama coding workflows, the `assistant` role shouldn't just store past chat replies—it can be used proactively in **three tested ways**:
		- Research
			- **Synthetic Few-Shot Formatting (Priming):** Instead of describing your desired output format in long system instructions, inject a fake `user` → `assistant` pair right after `system`. Show the model one tiny example of a edit and an `assistant` reply containing _only_ a clean ` ```python``` ` block. Local models mimic the structure of prior `assistant` turns far more reliably than prose rules.
			- **Assistant Prefill (Forcing Code Start):** In Ollama's `/api/chat` (or raw prompt templates), ending your `messages` list with `{"role": "assistant", "content": "```python\n"}` forces the model to immediately generate code. It eliminates conversational chatter ("Sure! Here is your updated file...") and guarantees a parseable code block. _(Note: Avoid prefilling if using a reasoning/thinking model like Qwen3 or DeepSeek-R1, as it skips their block)._
			- **Context Acknowledgment Turn (Used by Aider):** Aider often places the repo-map and read-only files in an initial `user` message followed by a synthetic `{"role": "assistant", "content": "Ok, I won't try to edit those files yet."}` before sending the actual edit request in the next `user` turn. This separates **background reference state** from **active edit instructions**.
	- [ ] Appending multi-turn messages vs all-in-one single message 
		- Research : Research on single-turn vs. multi-turn LLM performance (including recent 2025–2026 benchmarks) highlights a sharp trade-off:
			- Instruction adherence
			- File freshness
			- Ollama KV-cache speed
		 - Best practices for code editing
	- [ ] Error feedback loops
		- Research :
			- Research on automated code-repair loops (e.g., Reflexion, IaC feedback loops, and harness engineering) consistently shows that **naive retry loops plateau after 2–3 iterations** unless you structure the feedback carefully: [[1](https://arxiv.org/html/2411.19043v1), [2](https://www.reddit.com/r/LocalLLaMA/comments/1frz55h/patternsarchitecture_to_build_assistant_with_many/), [3](https://martinfowler.com/articles/harness-engineering.html)]
				1. **Cap Retries at 2–3 Turns:** Effectiveness drops exponentially after iteration 2. If a local model fails twice on the same error, appending more failed attempts pollutes the context window ("history poisoning"). At that point, reset the history and fall back to a stronger model or human review. [[1](https://medium.com/@addyosmani/my-llm-coding-workflow-going-into-2026-52fe1681325e), [2](https://arxiv.org/html/2411.19043v1), [3](https://medium.com/@chiwai.kiriba/the-anatomy-of-a-prompt-system-user-and-assistant-roles-d514cbc621ce)]
				2. **Prune Failed Intermediate Attempts:** When Turn 2 fails a linter or test, **do not keep Turn 1's broken code in the `messages` array** if you are doing a 3rd retry. Replace Turn 1's `assistant` message with the latest attempt so the model only sees _one_ broken draft + _one_ error trace, rather than 3 conflicting versions of the same file.
				3. **Send Structured, LLM-Optimized Error Signals:** Never dump a 200-line raw traceback. Extract and wrap only:
				    - The exact **error type and message** (e.g., `SyntaxError`, `AssertionError`, `ruff` lint rule).
				    - The **offending line number and 3 lines of surrounding code**.
				    - A concrete **fix hint** (e.g., _"Check for the exact signature of `normalize_columns`"_).
			    - **4. Separate Verification from Generation:** Run deterministic checks in Python _before_ calling Ollama again—specifically `ast.parse()` (instant syntax check), `ruff` or `flake8` (undefined variables/imports), and `pytest` (logic check)—and feed those back in a clean `user` message:
	- [x] generate and edit modes 
	- context injection  in utils
		- for context communication between local model calls: scan scripts from previous chunks, inject only necessary context into user prompt for current chunk. 
		- Research
			- The "Compressed Codebase Packer" Pattern
				- _Community Examples: **[Repomix](https://repomix.com/)** (formerly Repopack), **[Codebase-to-Text](https://medium.com/@qaisartanvir/codebase-to-text-give-your-whole-code-project-to-llms-046ffcea0926)**_ [[1](https://repomix.com/), [2](https://medium.com/@qaisartanvir/codebase-to-text-give-your-whole-code-project-to-llms-046ffcea0926)]
				- Rather than summarizing code into metadata, this approach packs the actual directory tree and raw files into a single structured XML or Markdown document—while aggressively stripping noise to save tokens. [[1](https://repomix.com/), [2](https://x.com/rohanpaul_ai/status/1896462798567395613)]
				- **How it works:**
					- Respects `.gitignore` and custom ignore rules so virtual environments and cache files never sneak in.
					- Uses Tree-sitter or regex to strip comments, blank lines, and docstrings ("code compression").
					- Tracks token counts per file and warns if the total payload exceeds your model's context budget. [[1](https://x.com/rohanpaul_ai/status/1896462798567395613), [2](https://repomix.com/), [3](https://repomix.com/guide), [4](https://github.com/r-dh/repopack)]
				- **Best for:** Small projects (under ~15–20 files) where your local model's context window can hold the compressed source directly.
			- The "AST Repo-Map + Graph Ranking" Pattern
				- _Community Examples: **[Aider's Repo Map](https://aider.chat/docs/repomap.html)**, **SigMap**, **Hermes Agent**_ [[1](https://github.com/NousResearch/hermes-agent/issues/535), [2](https://aider.chat/docs/repomap.html), [3](https://sigmap.io/guide/agents.html)]
				- This is the gold standard for local models running under tight VRAM constraints. Instead of sending file contents, it builds a **skeleton map** of the codebase and ranks what matters most. [[1](https://agentpatterns.ai/context-engineering/repository-map-pattern/), [2](https://deska.dev/blog/aider-repo-map-explained), [3](https://aider.chat/docs/repomap.html)]
				- **How it works:**
					- **Symbol Extraction:** Uses `ast` or `tree-sitter` to extract only definitions (classes, function signatures, global variables) and references (where those functions/variables are called).
					- **Dependency Ranking (PageRank):** Builds a graph where files are nodes and imports/calls are edges. If `pipeline.py` and `utils.py` are imported everywhere, they get a higher score and stay at the top of the context budget, while peripheral scripts get trimmed.
					- **Progressive Disclosure:** Gives the LLM the map first; if the LLM needs the full body of one specific file, it asks for (or fetches via tool call) just that file. [[1](https://aider.chat/docs/repomap.html), [2](https://deska.dev/blog/aider-repo-map-explained), [3](https://github.com/NousResearch/hermes-agent/issues/535), [4](https://agentpatterns.ai/context-engineering/repository-map-pattern/)]
				- **Best for:** Medium-to-large codebases where keeping context under ~2,000–4,000 tokens is critical for inference speed.
			- The "Data Lineage & Schema Graph" Pattern
				- _Community Examples: **Foundational's AST Lineage Engine**, **Multi-Agent ETL Lineage Extractors**_ [[1](https://hackernoon.com/beyond-sql-parsing-extracting-lineage-from-python-etl-by-splitting-the-job-across-three-llm-agents), [2](https://docs.foundational.io/en/articles/14640995-extracting-lineage-from-python)]
				- Standard repo-maps miss _data_ relationships (e.g., Script A writes `clean_sales.parquet` with 12 columns, and Script B reads it). Data engineering workflows solve this with a **Source-to-Sink AST pass**: [[1](https://docs.foundational.io/en/articles/14640995-extracting-lineage-from-python)]
				- **How it works:**
					- **I/O Tracking:** Scans AST call nodes for file/database readers (`read_csv`, `read_sql`, `open`) and writers (`to_parquet`, `to_csv`, `json.dump`) to link scripts together via the artifacts they produce.
					- **Ephemeral Node Collapsing:** Identifies intermediate/temporary files versus persistent outputs so the LLM sees the true end-to-end flow (`raw.csv -> clean.py -> clean.parquet -> train.py`).
					- **Schema Merging:** Peeks at data files (`.csv` headers, `.json` keys, `.parquet` metadata) and attaches those column schemas directly to the scripts that read/write them. [[1](https://docs.foundational.io/en/articles/14640995-extracting-lineage-from-python)]
				- **Best for:** Data science, ETL, and ML pipelines where variable names, column headers, and execution order matter more than OOP class hierarchies.
			- The "Local Pre-Processor / Refiner" Pattern
				- _Community Examples: **[Lean AI](https://github.com/shunobies/lean-ai)**, **AST-Aware Local RAG**_ [[1](https://github.com/shunobies/lean-ai), [2](https://dev.to/helain/building-a-local-code-search-system-with-ollama-and-ast-aware-rag-5d4a)]
				- Instead of a deterministic Python script building the context, a lightweight step (or a fast local model pass) filters the directory _specifically for the user's prompt_ before the main generation call. [[1](https://github.com/shunobies/lean-ai), [2](https://dev.to/helain/building-a-local-code-search-system-with-ollama-and-ast-aware-rag-5d4a)]
				- **How it works:**
					- **AST Chunking + Embeddings:** Splits code at function/class boundaries (rather than arbitrary line counts) so semantic search finds the exact relevant functions without breaking syntax.
					- **Prompt-Driven Pruning:** Matches keywords or embeddings from `user_prompt` against extracted symbols and file paths, injecting only the top-K relevant files plus their immediate upstream/downstream lineage neighbors. [[1](https://dev.to/helain/building-a-local-code-search-system-with-ollama-and-ast-aware-rag-5d4a)]
		- Action Plan
			- [ ] Try integrating Aider. only in context injection

- Validation stage improvements
	- [ ] make the validation stage optional or very low compute. 
	- [ ] write the final validated scripts in a separate project directory




