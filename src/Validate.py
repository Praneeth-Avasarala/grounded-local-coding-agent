import ast
import importlib.util
import json
import py_compile
import subprocess
import sys
from pathlib import Path


from utils.util_funcs import get_clean_subprocess_env


def validate_chunk(scripts_dir: Path, chunk: dict) -> tuple[bool, str, str]:
    """
    Validates syntax, installed packages, script execution, and chunk output contract.
    Returns: (passed, error_type, feedback_message)
    """
    target_path = scripts_dir / chunk["target_file"]
    if not target_path.exists() or target_path.stat().st_size == 0:
        return False, "code", f"`{chunk['target_file']}` was not created or is empty."

    # 1. Syntax check
    try:
        py_compile.compile(str(target_path), doraise=True)
    except py_compile.PyCompileError as e:
        return False, "code", f"Syntax error:\n{e.msg}"

    # 2. Package import check
    tree = ast.parse(target_path.read_text(encoding="utf-8"))
    missing = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                pkg = alias.name.split(".")[0]
                if importlib.util.find_spec(pkg) is None:
                    missing.append(pkg)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            pkg = node.module.split(".")[0]
            if importlib.util.find_spec(pkg) is None:
                missing.append(pkg)

    if missing:
        return (
            False,
            "package",
            f"Uninstalled or hallucinated packages imported: {', '.join(sorted(set(missing)))}. "
            "Use only installed packages from the reference or standard library.",
        )

    sub_env = get_clean_subprocess_env()

    val_code = chunk["validation_code"]
    val_runs_target = (
        "subprocess." in val_code and chunk["target_file"] in val_code
    )

    # 3. Run the generated chunk script
    captured_stdout = ""
    if not val_runs_target:
        run_proc = subprocess.run(
            [sys.executable, chunk["target_file"]],
            cwd=scripts_dir,
            env=sub_env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if run_proc.returncode != 0:
            err = (run_proc.stderr or run_proc.stdout).strip()
            err_type = (
                "package"
                if ("AttributeError" in err or "TypeError" in err or "ImportError" in err)
                else "code"
            )
            return False, err_type, f"Execution failed:\n{err}"

    # 4. Run the chunk's output contract acceptance test
    val_env = {**sub_env, "CHUNK_STDOUT": captured_stdout}
    val_script = scripts_dir / f"_validate_chunk_{chunk['chunk_id']}.py"
    val_script.write_text(chunk["validation_code"], encoding="utf-8")
    val_proc = subprocess.run(
        [sys.executable, val_script.name],
        cwd=scripts_dir,
        env=sub_env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if val_proc.returncode != 0:
        err = (val_proc.stderr or val_proc.stdout).strip()
        err_type = (
            "package"
            if ("AttributeError" in err or "TypeError" in err or "ImportError" in err)
            else "code"
        )
        return False, "code", f"Output contract assertion failed:\n{err}"

    return True, "none", "Chunk passed all package and output contract checks."




def load_completed_chunks(cache_dir: Path) -> set[int]:
    """Loads IDs of chunks that have already passed validation."""
    state_file = cache_dir / ".completed_chunks.json"
    if state_file.exists():
        return set(json.loads(state_file.read_text(encoding="utf-8")))
    return set()


def save_completed_chunk(cache_dir: Path, chunk_id: int) -> None:
    """Marks a chunk ID as verified and saves state to disk."""
    completed = load_completed_chunks(cache_dir)
    completed.add(chunk_id)
    state_file = cache_dir / ".completed_chunks.json"
    state_file.write_text(json.dumps(sorted(completed), indent=2), encoding="utf-8")