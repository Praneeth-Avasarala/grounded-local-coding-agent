import ast
import traceback
import re
from pathlib import Path

# ------------------------------------------------------------------------------------------------------------
# Concise Error Filter to get High signal-to-noise error : Remove error noise and optimize it for LLM feedback
# -------------------------------------------------------------------------------------------------------------


def extract_code_window(file_path: str | Path, line_no: int, radius: int = 2) -> str:
    """Extracts a small snippet around the offending line with line numbers and an arrow."""
    path = Path(file_path)
    if not path.exists() or line_no <= 0:
        return ""

    lines = path.read_text(encoding="utf-8").splitlines()
    start = max(0, line_no - 1 - radius)
    end = min(len(lines), line_no + radius)

    snippet = []
    for idx in range(start, end):
        curr_line = idx + 1
        marker = "-->" if curr_line == line_no else "   "
        snippet.append(f"{marker} {curr_line:4d} | {lines[idx]}")
    return "\n".join(snippet)


def check_syntax_fast(code_str: str, target_file: str) -> str | None:
    """Runs instant AST syntax check before executing anything."""
    try:
        ast.parse(code_str)
        return None
    except SyntaxError as e:
        lines = code_str.splitlines()
        line_no = e.lineno or 1
        start = max(0, line_no - 3)
        end = min(len(lines), line_no + 2)
        snippet = "\n".join(
            f"{'-->' if i + 1 == line_no else '   '} {i + 1:4d} | {lines[i]}"
            for i in range(start, end)
        )
        return (
            f"<validation_error type=\"SyntaxError\">\n"
            f"  <file>{target_file}</file>\n"
            f"  <line>{line_no}</line>\n"
            f"  <message>{e.msg}</message>\n"
            f"  <code_context>\n{snippet}\n  </code_context>\n"
            f"</validation_error>"
        )


def format_runtime_exception(exc: BaseException, project_root: str) -> str:
    """Filters a live Python exception to show ONLY frames inside project_root."""
    root = Path(project_root).resolve()
    tb_frames = traceback.extract_tb(exc.__traceback__)

    # Keep only frames belonging to your project (drop site-packages / stdlib)
    project_frames = [
        f for f in tb_frames
        if root in Path(f.filename).resolve().parents or Path(f.filename).resolve() == root
    ]

    # Fallback to the final frame if no project frame matched
    relevant_frames = project_frames if project_frames else tb_frames[-1:]
    primary_frame = relevant_frames[-1]
    rel_file = (
        Path(primary_frame.filename).resolve().relative_to(root)
        if root in Path(primary_frame.filename).resolve().parents
        else primary_frame.filename
    )

    call_chain = " -> ".join(
        f"{Path(f.filename).name}:{f.lineno} ({f.name})" for f in relevant_frames
    )
    snippet = extract_code_window(primary_frame.filename, primary_frame.lineno)

    return (
        f"<validation_error type=\"{type(exc).__name__}\">\n"
        f"  <file>{rel_file}</file>\n"
        f"  <line>{primary_frame.lineno}</line>\n"
        f"  <message>{str(exc).strip()}</message>\n"
        f"  <call_chain>{call_chain}</call_chain>\n"
        f"  <code_context>\n{snippet}\n  </code_context>\n"
        f"</validation_error>"
    )


def format_subprocess_stderr(stderr_text: str, project_root: str, target_file: str) -> str:
    """Compresses raw stderr from subprocess/pytest runs into a clean XML error block."""
    root = Path(project_root).resolve()
    lines = [l.rstrip() for l in stderr_text.strip().splitlines() if l.strip()]

    # Extract final exception line (e.g., "KeyError: 'revenue'" or "AssertionError: ...")
    error_summary = lines[-1] if lines else "Unknown execution error"

    hint = ""
    if "AssertionError" in error_summary:
        hint = "Check output contract"

    # Find the last traceback reference pointing to a file inside project_root
    file_matches = re.findall(r'File "([^"]+)", line (\d+)', stderr_text)
    target_line = None
    matched_path = root / target_file

    for f_str, l_str in reversed(file_matches):
        p = Path(f_str).resolve()
        if root in p.parents and "venv" not in p.parts:
            matched_path = p
            target_line = int(l_str)
            break

    snippet = extract_code_window(matched_path, target_line) if target_line else ""
    rel_path = (
        matched_path.relative_to(root)
        if root in matched_path.parents
        else target_file
    )

    block = [
        "<validation_error>",
        f"  <file>{rel_path}</file>",
    ]
    if target_line:
        block.append(f"  <line>{target_line}</line>")
    block.append(f"  <message>{error_summary}</message>")
    if snippet:
        block.append(f"  <code_context>\n{snippet}\n  </code_context>")
    block.append("</validation_error>")

    return "\n".join(block), hint


# 3 High-Value Refinements You Can Add Next

# 1. Actionable Error Hints: Map common exceptions (KeyError, ImportError, TypeError) to a one-line <hint> tag—
    # for example, if KeyError occurs, inject <hint>Check the column names in <repo_map> or the input schema.</hint>.
# 2. Static Linter Integration (ruff): 
    # Running ruff check --select E,F --output-format json catches undefined variables (F821) and
    # bad imports (F401) in ~15ms without running slow data pipelines.
# 3. Output Truncation Guard: 
    # Cap <message> at 300 characters so massive ValueError dumps (like a full printed DataFrame) never blow out your context limit.

