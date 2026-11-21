import ast
import importlib.util
import json
import py_compile
import subprocess
import sys
from pathlib import Path


from utils.util_funcs import get_clean_subprocess_env
from utils.error_filter import check_syntax_fast, format_subprocess_stderr


def validate_chunk(
        code_str:str,
        tests_dir: Path,
        scripts_dir: Path,
        chunk: dict) -> tuple[bool, str, str]:
    """
    Validates syntax, installed packages, script execution, and chunk output contract.
    Returns: (passed, error_type, feedback_message)
    """


    # Step 1: Instant syntax check before touching disk or spawning subprocess
    target_file = chunk['target_file']
    syntax_err = check_syntax_fast(code_str, target_file)


    # root = Path(project_root).resolve()
    # target_path = (root / target_file).resolve()
    # target_path.write_text(code_str, encoding="utf-8")

   
    (scripts_dir / target_file).write_text(code_str, encoding="utf-8")

    target_path = scripts_dir / chunk["target_file"]
    if not target_path.exists() or target_path.stat().st_size == 0:
        return False, "code", f"`{chunk['target_file']}` was not created or is empty.", f"`{chunk['target_file']}` was not created or is empty." 

    # # 1. Syntax check
    # try:
    #     py_compile.compile(str(target_path), doraise=True)
    # except py_compile.PyCompileError as e:
    #     return False, "code", f"Syntax error:\n{e.msg}", f"Syntax error:\n{e.msg}"

    # 2. Package import check
    # tree = ast.parse(target_path.read_text(encoding="utf-8"))
    # missing = []
    # for node in ast.walk(tree):
    #     if isinstance(node, ast.Import):
    #         for alias in node.names:
    #             pkg = alias.name.split(".")[0]
    #             if importlib.util.find_spec(pkg) is None:
    #                 missing.append(pkg)
    #     elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
    #         pkg = node.module.split(".")[0]
    #         if importlib.util.find_spec(pkg) is None:
    #             missing.append(pkg)

    # if missing:
        # return (
        #     False,
        #     "package",
        #     f"Uninstalled or hallucinated packages imported: {', '.join(sorted(set(missing)))}. "
        #     "Use only installed packages from the reference or standard library.",
        # )
        # print("{', '.join(sorted(set(missing)))}")

    sub_env = get_clean_subprocess_env()

    val_code = chunk["validation_code"]
    val_runs_target = (
        "subprocess." in val_code and chunk["target_file"] in val_code
    )



    # 3. Run the generated chunk script
    captured_stdout = ""
    tfile_path = scripts_dir / chunk["target_file"]

    if not val_runs_target:
        print('running chunk code')
        run_proc = subprocess.run(
            [sys.executable, str(tfile_path.resolve())],
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

            err_clean, hint = format_subprocess_stderr(stderr_text=err, 
                                                 project_root=Path(scripts_dir).resolve(),
                                                  target_file=target_file)
            # err_type = "code"
            return False, err_type, err_clean, f"Execution failed:\n{err}", ""

    # 4. Run the chunk's output contract acceptance test
    val_env = {**sub_env, "CHUNK_STDOUT": captured_stdout}

    tests_dir.mkdir(parents=True, exist_ok=True)

  

    val_script = tests_dir / f"_validate_chunk_{chunk['chunk_id']}.py"

    if not val_script.exists():

        val_script.write_text(chunk["validation_code"], encoding="utf-8")


    print('running validation code')
    val_proc = subprocess.run(
        [sys.executable, str(val_script.resolve())],
        cwd=scripts_dir,
        env=val_env,
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

        err_clean, hint = format_subprocess_stderr(stderr_text=err, 
                                    project_root=Path(scripts_dir).resolve(),
                                    target_file=target_file)
        
        return False, err_type, err_clean, f"Output contract assertion failed:\n{err}", hint

    return True, "none", "none", "Chunk passed all package and output contract checks.", ""




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