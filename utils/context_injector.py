# import os

import ast
import re
from pathlib import Path
from typing import Sequence, Union, List, Tuple
from pydantic import BaseModel, Field
import subprocess
import shutil
from pathlib import Path


#-----------------------------------------------
# Aider for RepoMap
#-------------------------------------------------


def find_aider_binary() -> str:
    # 1. Check standard PATH first
    aider_bin = shutil.which("aider")
    if aider_bin:
        return aider_bin
    
    # 2. Check pipx's default Ubuntu install directory
    pipx_bin = Path.home() / ".local" / "bin" / "aider"
    if pipx_bin.exists():
        return str(pipx_bin)
        
    raise FileNotFoundError("Could not find 'aider'. Run `pipx ensurepath` or check ~/.local/bin.")

def get_aider_repo_map(
    directory_path: str,
    target_file: str | None = None,
    map_tokens: int = 1024,
) -> str:
    """Generates Aider's RepoMap, boosting files connected to target_file."""
    repo_dir = Path(directory_path).resolve()

    # cmd = [
    #     find_aider_binary(),
    #     "aider",
    #     "--show-repo-map",
    #     "--map-tokens", str(map_tokens),
    #     "--no-git",
    #     "--no-auto-commits",
    # ]
    cmd = [
        find_aider_binary(),
        "--show-repo-map",
        "--map-tokens", str(map_tokens),
        "--yes-always",          # Auto-accepts .gitignore / file creation prompts
        "--no-analytics",        # Skips first-run telemetry prompt
        "--no-check-update",     # Prevents hanging on GitHub release checks
        "--no-git",              # Prevents git repo initialization prompts
        "--no-auto-commits",
        "--no-pretty",           # Disables rich terminal spinners/ANSI codes
        "--model", "ollama/qwen2.5-coder:7b",  # Prevents OpenAI API key check/hang
    ]


    # Passing target_file tells Aider to prioritize its imported dependencies in the map
    if target_file:
        full_target = (repo_dir / target_file).resolve()
        if full_target.exists():
            cmd.append(str(full_target))

    print('i am at aider subprocess')

    result = subprocess.run(
        cmd,
        cwd=str(repo_dir),
        capture_output=True,
        stdin=subprocess.DEVNULL,  # Immediately fails instead of hanging if stdin is requested
        text=True,
        timeout=30,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Aider RepoMap failed (code {result.returncode}):\n"
            f"STDERR: {result.stderr.strip()}\n"
            f"STDOUT: {result.stdout.strip()}"
        )

    return result.stdout.strip()

# --------------------------------------------
# Use existing code file, Make search-and-replace edits.
# --------------------------------------------
# class CodeEdit(BaseModel):
#     search: str = Field(
#         description=(
#             "Exact, verbatim lines from the existing file to anchor the edit."
#             " Include 2-3 surrounding lines for uniqueness."
#         )
#     )
#     replace: str = Field(
#         description=(
#             "The exact anchor lines from 'search' with the new code added or"
#             " updated."
#         )
#     )

# class FilePatch(BaseModel):
#     edits: List[CodeEdit]


# SYSTEM_PROMPT = """You are a precise code-editing assistant.
# Your job is to add new code to an existing file to fulfill the user's task.

# Rules:
# 1. Do NOT rewrite the whole file. Return only minimal search/replace blocks.
# 2. `search` MUST match existing lines in the file character-for-character (including indentation).
# 3. Include 2-3 unchanged context lines in `search` so the location is unambiguous.
# 4. Keep all existing functionality intact unless the task requires changing it.
# 5. If adding imports at the top and a function at the bottom, return two separate items in `edits`."""


# def apply_edits(original_code: str, edits: List[CodeEdit]) -> str:

#     updated_code = original_code

#     for i, edit in enumerate(edits):
#         # 1. Fast path: exact match
#         if edit.search in updated_code:
#             updated_code = updated_code.replace(edit.search, edit.replace, 1)
#             continue

#         # 2. Fallback: match ignoring trailing whitespace per line
#         orig_lines = updated_code.splitlines()
#         search_lines = [line.rstrip() for line in edit.search.splitlines()]

#         if not search_lines:
#             raise ValueError(f"Edit #{i+1} provided an empty search block.")

#         match_index = -1
#         for idx in range(len(orig_lines) - len(search_lines) + 1):
#             window = [
#                 line.rstrip()
#                 for line in orig_lines[idx : idx + len(search_lines)]
#             ]
#             if window == search_lines:
#                 match_index = idx
#                 break

#         if match_index != -1:
#             replace_lines = edit.replace.splitlines()
#             orig_lines[match_index : match_index + len(search_lines)] = (
#                 replace_lines
#             )
#             updated_code = "\n".join(orig_lines) + (
#                 "\n" if original_code.endswith("\n") else ""
#             )
#         else:
#             raise ValueError(
#                 f"Edit #{i+1} failed: Could not locate search block:\n{edit.search}"
#             )

#     return updated_code




# def apply_edits(original_code: str, edits: List[CodeEdit]) -> Tuple[str, List[str]]:
#     updated_code = original_code
#     feedback: List[str] = []

#     for i, edit in enumerate(edits):
#         # Guard against empty search block before fast-path (since "" is always in any string)
#         if not edit.search or not edit.search.strip():
#             feedback.append(f"Edit #{i+1} failed: Provided an empty search block.")
#             continue

#         # 1. Fast path: exact match
#         if edit.search in updated_code:
#             updated_code = updated_code.replace(edit.search, edit.replace, 1)
#             continue

#         # 2. Fallback: match ignoring trailing whitespace per line
#         orig_lines = updated_code.splitlines()
#         search_lines = [line.rstrip() for line in edit.search.splitlines()]

#         match_index = -1
#         for idx in range(len(orig_lines) - len(search_lines) + 1):
#             window = [
#                 line.rstrip()
#                 for line in orig_lines[idx : idx + len(search_lines)]
#             ]
#             if window == search_lines:
#                 match_index = idx
#                 break

#         if match_index != -1:
#             replace_lines = edit.replace.splitlines()
#             orig_lines[match_index : match_index + len(search_lines)] = replace_lines
#             updated_code = "\n".join(orig_lines) + (
#                 "\n" if original_code.endswith("\n") else ""
#             )
#         else:
#             feedback.append(
#                 f"Edit #{i+1} failed: Could not locate search block:\n{edit.search}"
#             )

#     return updated_code, feedback




# -----------------------------------------------------------------------------------------------------------
# Validation Error should point the model towards which files upstream are the probable candidates to modify. 
# But due to limited max context, we need a smart strategy to choose files.  
# So first we need data lineage. System to track output producers and consumers. 
# ----------------------------------------------------------------------------------------------------
# 
# 1. Trace Data Lineage in a Folder

# def _extract_string_literals(node: ast.AST) -> list[str]:
#     """Extracts string literals from a call node (handles direct strings or Path('...'))."""
#     found = []
#     for sub in ast.walk(node):
#         if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
#             val = sub.value.strip()
#             # Filter for file-like strings (has extension or path separator)
#             if ("." in Path(val).name or "/" in val or "\\" in val) and len(val) < 200:
#                 found.append(val)
#     return found


# def build_data_lineage(scripts_dir: Union[str, Path]) -> dict:
#     """
#     Scans Python scripts in scripts_dir to map producers (writers) and consumers (readers)
#     of data artifacts, tracking exact line numbers for each operation.

#     Returns:
#         {
#             "artifacts": {
#                 "output1.csv": {
#                     "producers": [{"script": "script1.py", "line": 24}],
#                     "consumers": [{"script": "script3.py", "line": 10}],
#                 }
#             },
#             "scripts": {
#                 "script1.py": {"reads": [], "writes": [{"artifact": "output1.csv", "line": 24}]},
#                 "script3.py": {"reads": [{"artifact": "output1.csv", "line": 10}], "writes": []},
#             }
#         }
#     """
#     target_dir = Path(scripts_dir).resolve()
#     if not target_dir.is_dir():
#         raise FileNotFoundError(f"Scripts directory not found: {target_dir}")

#     write_indicators = ("to_csv", "to_parquet", "to_json", "to_excel", "to_sql", "dump", "save", "write_text", "write_bytes")
#     read_indicators = ("read_csv", "read_parquet", "read_json", "read_excel", "read_sql", "load", "read_text", "read_bytes")

#     lineage = {"artifacts": {}, "scripts": {}}

#     for py_file in sorted(target_dir.glob("*.py")):
#         script_name = py_file.name
#         lineage["scripts"][script_name] = {"reads": [], "writes": []}

#         try:
#             tree = ast.parse(py_file.read_text(encoding="utf-8", errors="ignore"), filename=script_name)
#         except SyntaxError:
#             continue

#         for node in ast.walk(tree):
#             if not isinstance(node, ast.Call):
#                 continue

#             # Determine function/method name being called
#             func_name = ""
#             if isinstance(node.func, ast.Attribute):
#                 func_name = node.func.attr
#             elif isinstance(node.func, ast.Name):
#                 func_name = node.func.id

#             direction = None
#             if any(w in func_name for w in write_indicators):
#                 direction = "writes"
#             elif any(r in func_name for r in read_indicators):
#                 direction = "reads"
#             elif func_name == "open":
#                 # Check mode argument in open(path, 'w') vs open(path, 'r')
#                 mode = "r"
#                 if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant) and isinstance(node.args[1].value, str):
#                     mode = node.args[1].value
#                 for kw in node.keywords:
#                     if kw.arg == "mode" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
#                         mode = kw.value.value
#                 direction = "writes" if any(m in mode for m in ("w", "a", "x")) else "reads"

#             if not direction:
#                 continue

#             # Extract artifact filenames referenced in this I/O call
#             raw_paths = _extract_string_literals(node)
#             for raw_p in raw_paths:
#                 # Normalize to filename (e.g., "data/output1.csv" -> "output1.csv") so path prefixes don't break matching
#                 artifact_key = Path(raw_p).name
#                 line_no = getattr(node, "lineno", 1)

#                 lineage["scripts"][script_name][direction].append({
#                     "artifact": artifact_key,
#                     "raw_path": raw_p,
#                     "line": line_no,
#                 })

#                 if artifact_key not in lineage["artifacts"]:
#                     lineage["artifacts"][artifact_key] = {"producers": [], "consumers": []}

#                 role = "producers" if direction == "writes" else "consumers"
#                 lineage["artifacts"][artifact_key][role].append({
#                     "script": script_name,
#                     "line": line_no,
#                 })

#     return lineage


##################################################################

# Token awareness to decide how much context to inject

# def estimate_tokens(text: str) -> int:
#     """Conservative token estimator for code/XML (approx. 3 chars per token)."""
#     return max(1, len(text) // 3)


# def _score_file_relevance(file_path: Path, prompt_keywords: set[str]) -> int:
#     """Scores a file based on keyword overlap with the user prompt."""
#     if not prompt_keywords:
#         return 1

#     # Filename matches carry higher weight than body matches
#     name_tokens = set(re.findall(r"[a-zA-Z0-9]+", file_path.stem.lower()))
#     score = len(prompt_keywords & name_tokens) * 5

#     # Quick lightweight text scan without full AST parsing
#     try:
#         snippet = file_path.read_text(encoding="utf-8", errors="ignore")[:4000].lower()
#         body_tokens = set(re.findall(r"[a-zA-Z0-9_]+", snippet))
#         score += len(prompt_keywords & body_tokens)
#     except OSError:
#         pass

#     return score


# def _extract_script_context(file_path: Path) -> str:
#     """Parses a Python file with AST to extract paths, column names, types, and signatures."""
#     source = file_path.read_text(encoding="utf-8", errors="ignore")
#     try:
#         tree = ast.parse(source, filename=str(file_path))
#     except SyntaxError:
#         return f"  <error>SyntaxError in {file_path.name}</error>"

#     imports, paths, string_keys, type_hints, signatures = set(), set(), set(), set(), []

#     for node in ast.walk(tree):
#         if isinstance(node, ast.Import):
#             for alias in node.names:
#                 imports.add(alias.name)
#         elif isinstance(node, ast.ImportFrom) and node.module:
#             imports.add(node.module)
#         elif isinstance(node, ast.FunctionDef):
#             args = [
#                 f"{arg.arg}: {ast.unparse(arg.annotation)}" if arg.annotation else arg.arg
#                 for arg in node.args.args
#             ]
#             ret = f" -> {ast.unparse(node.returns)}" if node.returns else ""
#             signatures.append(f"def {node.name}({', '.join(args)}){ret}")
#         elif isinstance(node, ast.AnnAssign) and node.annotation:
#             type_hints.add(ast.unparse(node.annotation))
#         elif isinstance(node, ast.Subscript):
#             if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
#                 string_keys.add(node.slice.value)
#         elif isinstance(node, ast.Constant) and isinstance(node.value, str):
#             val = node.value.strip()
#             if any(val.endswith(ext) for ext in (".csv", ".parquet", ".json", ".xlsx", ".db")) or "/" in val:
#                 if len(val) < 120 and "\n" not in val:
#                     paths.add(val)
#         elif isinstance(node, (ast.List, ast.Tuple)):
#             str_items = [
#                 elt.value for elt in node.elts
#                 if isinstance(elt, ast.Constant) and isinstance(elt.value, str) and len(elt.value) < 50
#             ]
#             if 1 < len(str_items) <= 20:
#                 string_keys.update(str_items)

#     sections = []
#     if imports:
#         sections.append(f"  <imports>{', '.join(sorted(imports))}</imports>")
#     if paths:
#         sections.append(f"  <paths>{', '.join(sorted(paths))}</paths>")
#     if string_keys:
#         sections.append(f"  <columns_keys>{', '.join(sorted(string_keys))}</columns_keys>")
#     if type_hints:
#         sections.append(f"  <types>{', '.join(sorted(type_hints))}</types>")
#     if signatures:
#         sections.append("  <functions>\n    " + "\n    ".join(signatures) + "\n  </functions>")

#     return "\n".join(sections) if sections else "  <info>No metadata</info>"


# def inject_budgeted_context(
#     folder_path: Union[str, Path],
#     user_prompt: str,
#     max_total_tokens: int = 2048,
#     response_reserve_tokens: int = 600,
#     recursive: bool = False,
# ) -> str:
#     """
#     Ranks Python files by prompt relevance and injects AST metadata
#     strictly within the remaining token budget.
#     """
#     target_dir = Path(folder_path)
#     if not target_dir.is_dir():
#         raise FileNotFoundError(f"Directory not found: {target_dir}")

#     # Calculate available budget for context
#     prompt_tokens = estimate_tokens(user_prompt)
#     available_budget = max_total_tokens - prompt_tokens - response_reserve_tokens

#     if available_budget <= 100:
#         return user_prompt

#     # Extract meaningful keywords from prompt (ignore short stop words)
#     stop_words = {"the", "and", "for", "with", "from", "that", "this", "write", "script", "code", "file"}
#     keywords = {
#         w for w in re.findall(r"[a-zA-Z0-9_]+", user_prompt.lower())
#         if len(w) > 2 and w not in stop_words
#     }

#     pattern = "**/*.py" if recursive else "*.py"
#     py_files = list(target_dir.glob(pattern))

#     # Rank files: highest relevance first, then most recently modified
#     ranked_files = sorted(
#         py_files,
#         key=lambda f: (_score_file_relevance(f, keywords), f.stat().st_mtime),
#         reverse=True,
#     )

#     included_blocks = []
#     used_tokens = 30  # Reserve overhead for outer XML wrapper
#     omitted_files = []

#     for file_path in ranked_files:
#         # Only parse AST when we are ready to evaluate this candidate
#         extracted = _extract_script_context(file_path)
#         block = f'<file name="{file_path.name}">\n{extracted}\n</file>'
#         block_tokens = estimate_tokens(block)

#         if used_tokens + block_tokens <= available_budget:
#             included_blocks.append(block)
#             used_tokens += block_tokens
#         else:
#             omitted_files.append(file_path.name)

#     if not included_blocks:
#         return user_prompt

#     if omitted_files:
#         included_blocks.append(
#             f'<omitted count="{len(omitted_files)}">Skipped due to token budget: {", ".join(omitted_files[:10])}</omitted>'
#         )

#     formatted_context = "<workspace_context>\n" + "\n".join(included_blocks) + "\n</workspace_context>"

#     return (
#         f"{user_prompt.strip()}\n\n"
#         f"Use the workspace metadata below:\n{formatted_context}"
#     )



# def extract_workspace_schemas(
#     user_prompt: str, workspace_dir: str = "."
# ) -> str:
#     """Scans the user prompt (and optionally the folder) for data files,

#     reads their columns/types, and formats them as plain text context.
#     """
#     workspace = Path(workspace_dir)

#     # 1. Find any data filenames mentioned in the prompt (e.g., sales.csv, data.parquet)
#     mentioned_files = re.findall(
#         r"[\w\-./]+\.(?:csv|xlsx|xls|parquet|json)", user_prompt, re.IGNORECASE
#     )

#     # Fallback: if no specific file was named in the prompt, grab all CSV/Parquet files in the folder
#     if not mentioned_files:
#         target_files = list(workspace.glob("*.csv")) + list(
#             workspace.glob("*.parquet")
#         )
#     else:
#         target_files = [workspace / f for f in mentioned_files]

#     schema_blocks = []
#     for file_path in target_files:
#         if not file_path.exists():
#             continue

#         try:
#             # Read only the first 3 rows for speed and low memory usage
#             if file_path.suffix.lower() == ".csv":
#                 df = pd.read_csv(file_path, nrows=3)
#             elif file_path.suffix.lower() in [".xlsx", ".xls"]:
#                 df = pd.read_excel(file_path, nrows=3)
#             elif file_path.suffix.lower() == ".parquet":
#                 df = pd.read_parquet(file_path).head(3)
#             elif file_path.suffix.lower() == ".json":
#                 df = pd.read_json(file_path).head(3)
#             else:
#                 continue

#             cols = df.columns.tolist()
#             dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}
#             sample_row = (
#                 df.iloc[0].to_dict() if not df.empty else "No rows found"
#             )

#             schema_blocks.append(
#                 f"File: '{file_path.name}'\n"
#                 f"  - Exact Columns: {cols}\n"
#                 f"  - Data Types: {dtypes}\n"
#                 f"  - Sample Row 1: {sample_row}"
#             )
#         except Exception as e:
#             schema_blocks.append(f"File: '{file_path.name}' (Read error: {e})")

#     if not schema_blocks:
#         return ""

#     return (
#         "\n\n[VERIFIED DATASET SCHEMAS IN WORKSPACE]\n"
#         + "\n".join(schema_blocks)
#     )



# def build_code_context(file_paths: Sequence[str | Path]) -> str:
#     """
#     Reads multiple script/text files and formats them into an XML-wrapped
#     context string ready to be joined with a user prompt.
#     """
#     context_blocks: list[str] = []

#     for raw_path in file_paths:
#         path = Path(raw_path)

#         if not path.is_file():
#             context_blocks.append(f'<file path="{path}" error="File not found" />')
#             continue

#         try:
#             content = path.read_text(encoding="utf-8")
#             # context_blocks.append(f'<file path="{path}">\n{content}\n</file>')
#         except UnicodeDecodeError:
#             context_blocks.append(f'<file path="{path}" error="Skipped non-UTF8/binary file" />')

#     return "\n\n".join(context_blocks)


# def generate_script(
#     user_prompt: str, output_filename: str, workspace_dir: str = "."
# ):
#     """Injects verified schemas into the prompt, calls qwen3:4b, and saves the clean code."""
#     # 1. Silently gather column names before calling Ollama
#     schema_context = extract_workspace_schemas(user_prompt, workspace_dir)

#     system_prompt = (
#         "You are an expert Python developer. Write clean, standalone Python"
#         " scripts using standard libraries like pandas. When dataset schemas"
#         " are provided in the prompt, you MUST use the exact column names"
#         " (including exact capitalization and spaces). Do NOT invent helper"
#         " functions. Output ONLY a single ```python code block."
#     )

#     full_prompt = f"{user_prompt}{schema_context}"

#     # 2. Call qwen3:4b WITHOUT any `tools` parameter
#     response = ollama.chat(
#         model="qwen3:4b",
#         messages=[
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": full_prompt},
#         ],
#         options={
#             "temperature": 0,  # Prevents creative renaming of columns
#             "num_ctx": 8192,
#         },
#     )

#     raw_output = response["message"]["content"]

#     # 3. Parse the markdown code block and write the file
#     match = re.search(r"```python\s*(.*?)```", raw_output, re.DOTALL)
#     if not match:
#         raise ValueError("Model did not return a valid Python code block.")

#     clean_code = match.group(1).strip()

#     output_path = Path(workspace_dir) / output_filename
#     output_path.write_text(clean_code, encoding="utf-8")
#     print(f"Saved clean script to: {output_path}")


# # --- Example Usage ---
# if __name__ == "__main__":
#     task = (
#         "Write a script that loads sales_data.csv, drops rows with missing"
#         " totals, and prints average revenue by region."
#     )
#     generate_script(
#         user_prompt=task,
#         output_filename="analyze_sales.py",
#         workspace_dir="./my_scripts_folder",
#     )
