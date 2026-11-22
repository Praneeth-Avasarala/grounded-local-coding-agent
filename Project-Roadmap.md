## So far 
- working pipeline. git tracked. 
    - web-search. 
		- input :
     		 - [x] task along with system prompt, user prompt,  
		- output:
      		- [x] micro-task chunks. chunk goal, package and syntax info, strict input output contracts, validation scripts for each chunk.  
	  - ollama generates one chunk code at a time. 
		- input :
	        - [x]  chunk goal, package and syntax info, input-output contract
	        - [x]  Context injection : Aider repomap
		- output:
	        - [x]  chunk's code script
	- [x] Testing, Validation, Feedback loop
		- input :
	        - [x] chunk's code script and chunk's validation script
		- output :
	        - [x] validation success of failure. if failure, error decides whether to do web-search again or generate code again. save error log and let next attempt see the error log.
		- max attempts limit. success or failure
	        - [x] error filtering to increase signal-to-noise in error before injecting it into prompt for next attempt 
	- [x] combine chunks. master script for the full task pipeline.  


- Github repo.
	- [x] published working version
	- [x] Dev git branch for local development

## To do next

- learn about existing tools. consider integrating their best parts
    - aider, opencode, OpenClaw, copilot, 
    - pstack, ponytail, 
- Web research workflow improvemens
- Local Model workflow improvements - https://www.reddit.com/r/LocalLLM/s/Wppf7AVMfS
	- [ ] choose best open weight/open source coding models that can run on available hardware. 
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
    
	        [1] [kilo.ai - Open Source Models](https://kilo.ai/open-source-models)
	
	        [2] [https://gpuwerk.com - Best open weight coding models](https://gpuwerk.com/blog/best-open-weight-coding-models/)
	
			[3] [https://vdf.ai - Best local LLM for coding](https://vdf.ai/blog/best-local-llm-for-coding/)
	
			[4] [https://www.promptquorum.com - Best local LLMs for coding](https://www.promptquorum.com/local-llms/best-local-llms-for-coding)
	
			[5] [https://www.gumloop.com - Open weight AI models](https://www.gumloop.com/blog/open-weight-ai-models)
	
			[6] [https://www.faros.ai -  Open weight models](https://www.faros.ai/blog/open-weight-models)
	
			[7] [https://www.developersdigest.tech - Open weight coding showdown](https://www.developersdigest.tech/blog/glm-5-2-vs-deepseek-v4-vs-qwen3-open-weights-coding-showdown)
	
			[8] (https://www.youtube.com/watch?v=z605KVofJAY&t=187)
	
			[9] (https://www.reddit.com/r/LocalLLM/comments/1ur0vdq/which_open_sourceopen_weight_local_llm_should_i/)
	
			[10] (https://github.com/xigh/open-weight-models)
	
			[11] (https://www.youtube.com/watch?v=ozyazf9xKP4&t=145)
	
			[12] (https://huggingface.co/blog/daya-shankar/open-source-llm-models-to-run-locally)
		
	- [ ] integreate aider 
	- [ ] use assistant role
	- [ ] use 



- Web search workflow improvements
	- 
- Local Model workflow improvement
	- [ ] assistant role : In local Ollama coding workflows, the `assistant` role shouldn't just store past chat replies—it can be used proactively in **three tested ways**:
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
		- Researching 
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





- Split web-search & local model calls+validation
- Web search improvements : Skeleton + Slot filling pipeline
    - Instead of asking the model to write the entire file at once, you split the task into structural planning, independent section generation, and programmatic assembly.
    - 1. The "Skeleton + Slot Filling" Architecture
	    - Step 1: Generate the Master Skeleton. Ask the LLM to create the main boilerplate.
	    - Step 2: Generate Each Section Independently. Loop through your placeholders and send a separate, focused prompt to the LLM for each one. Pass only the specific content requirements for that single section, instructing the model to output only the inner content without the skeleton
	    - Step 3: Assemble Programmatically. Use a simple script (in Python or Node.js) to replace the <!-- SLOT_... --> placeholders in your skeleton string with the generated HTML snippets and save the final output as index.html.
	- 2. Best Practices for Low-Context Reliability
		- Enforce a Shared CSS System. Use a utility-first framework like Tailwind CSS via CDN in the skeleton's <head>. This prevents the LLM from hallucinating conflicting custom CSS class names across different API calls.
		- Provide a Strict "Contract" in Every Prompt. Include a tiny 10-line style guide in every section prompt (e.g., "Use bg-slate-900 for dark backgrounds, text-indigo-500 for accents, and wrap the section in <section id='...'>").
		- Use HTML/JSON Output Stripping. Low-context models often wrap code in markdown fences (```html ... ```) or add conversational filler. Write a quick regex cleaner in your assembly script to strip markdown tags before injecting the snippet into your skeleton.
		- Keep Context Rolling (Optional). If a section needs to reference a previous section, pass only the previous section's headings or IDs or column names, never the full code, to save tokens.
	- Action Plan
		- [ ] Each task gets assigned a vector id. two parallel tasks emerging from input data get assigned (0,1) and (0,2). sequential chunked tasks in each one these parallel tasks get assigned (01,1); (01,2) and (02,1);(02,2). two tasks are independent if the coordinates before last are the same. 
		- [ ] When fetching package docs, give full tasks_json file as context. 
- Local model continuity improvements
	- Idea 
		- need to give context about previous chunk. for example,  guessing dataframe columns 
	- Possible action plans
		- [ ] maintain a text file that records models feedback from each chunk to help next chunk
		- [ ] or, add a "purely thinking" model query step after a validation failure with existing chunk code + existing errors as context, outputs compact instructions list about what to change in the existing code
	- Idea
		- "what-I-need" for each chunk loop
			- If a model keeps failing validation tests, collect data about "what I need to do this task" from the model. This could be more package information or more context about previous chunk. This step assumes the model can accurately identify what it needs. Validation error type can narrow down this requirement independent of model's answer. 
	- Idea 
		- use "existing code" part to make a standalone function that takes existing code as part of its prompt, and works to improve it to complete the task. 
- Validation stage improvements
	- [ ] make the validation stage optional or very low compute. 
	- [ ] write the final validated scripts in a separate task specific project directory
- Local AI stage improvements
	- install needed packages.
		- Idea
			- create a new conda env before running the script. let the script install needed packages in this new env.
			- don't need model to do this. model generated code can be parsed for packages used.
				- identify which packages used are missing in the env
				- install them using commands from chunk package docs info from web search
			- but in case validation fails and code is reattempted, modified code versions may have dropped previously installed packages. so the installed packages must be tracked across attempts. after validation success, if final chunk code version uses less packages than total installed packages, these packages must be uninstalled.
	- token-budget awareness 
		- Idea 
			- make the agent aware about the token usage and the system hardware limitations. give it the knowledge and the power to manage context accordingly and efficiently. but dont trust that it wont make mistakes. always have guard rails in place if the model wants to go beyond context limit
		- Action plan
			- [ ] first get max token limit and current token usage.
			- [ ] decide if model can take more context. don't distract model with additional token management. can use deterministic algorithms for this
		

## To do later
- [ ] project could have more than one sequences that can be computed in parallel 
