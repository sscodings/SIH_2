#!/usr/bin/env python3
"""
Cross-platform development orchestrator for ChainNetra (stdlib only).
Supports: setup, seed, dev, test, lint, docker-up, docker-down, check
"""

import sys
import os
import subprocess
import signal
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
FRONTEND_DIR = REPO_ROOT / "frontend"

def get_python_exe() -> str:
    """Finds the python executable from .venv, backend/venv, or active environment."""
    candidates = [
        REPO_ROOT / ".venv" / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python"),
        BACKEND_DIR / "venv" / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python"),
    ]
    for cand in candidates:
        if cand.exists():
            return str(cand)
    return sys.executable

def get_pytest_exe() -> str:
    py_dir = Path(get_python_exe()).parent
    exe = py_dir / ("pytest.exe" if os.name == "nt" else "pytest")
    if exe.exists():
        return str(exe)
    return "pytest"

def get_uvicorn_exe() -> str:
    py_dir = Path(get_python_exe()).parent
    exe = py_dir / ("uvicorn.exe" if os.name == "nt" else "uvicorn")
    if exe.exists():
        return str(exe)
    return "uvicorn"

def run_cmd(cmd, cwd=None, env=None) -> int:
    display_cmd = " ".join(cmd) if isinstance(cmd, list) else cmd
    print(f"\n[dev.py] Running: {display_cmd} (in {cwd or '.'})")
    res = subprocess.run(cmd, cwd=cwd, env=env)
    return res.returncode

def cmd_setup():
    print("[dev.py] Setting up virtual environment and dependencies...")
    venv_dir = REPO_ROOT / ".venv"
    if not venv_dir.exists() and not (BACKEND_DIR / "venv").exists():
        subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])
        print(f"Created virtualenv at {venv_dir}")

    py_exe = get_python_exe()
    pip_cmd = [py_exe, "-m", "pip", "install", "--upgrade", "pip"]
    run_cmd(pip_cmd)

    req_file = BACKEND_DIR / "requirements.txt"
    if req_file.exists():
        run_cmd([py_exe, "-m", "pip", "install", "-r", str(req_file)])

    npm_path = shutil.which("npm") or shutil.which("npm.cmd")
    if npm_path and FRONTEND_DIR.exists():
        run_cmd([npm_path, "install"], cwd=str(FRONTEND_DIR))

    print("[dev.py] Setup completed successfully.")

def cmd_seed():
    py_exe = get_python_exe()
    print("[dev.py] Seeding database...")
    code = run_cmd([py_exe, "-m", "app.db.seed"], cwd=str(BACKEND_DIR))
    if code != 0:
        sys.exit(code)

def cmd_test():
    py_exe = get_python_exe()
    print("[dev.py] Running pytest suite...")
    code = run_cmd([py_exe, "-m", "pytest", "-q"], cwd=str(BACKEND_DIR))
    if code != 0:
        sys.exit(code)

def cmd_lint():
    py_exe = get_python_exe()
    print("[dev.py] Checking legal provisions guard...")
    code1 = run_cmd([py_exe, "scripts/check_legal_strings.py"], cwd=str(REPO_ROOT))
    if code1 != 0:
        sys.exit(code1)

    print("[dev.py] Checking frontend hardcoded hosts guard...")
    code2 = run_cmd([py_exe, "scripts/check_no_hardcoded_hosts.py"], cwd=str(REPO_ROOT))
    if code2 != 0:
        sys.exit(code2)

    npm_path = shutil.which("npm") or shutil.which("npm.cmd")
    if npm_path and FRONTEND_DIR.exists():
        print("[dev.py] Running frontend linter...")
        code3 = run_cmd([npm_path, "run", "lint"], cwd=str(FRONTEND_DIR))
        if code3 != 0:
            sys.exit(code3)

def cmd_check():
    cmd_lint()
    cmd_test()

def cmd_docker_up():
    print("[dev.py] Starting Docker compose services...")
    code = run_cmd(["docker", "compose", "up", "-d"], cwd=str(REPO_ROOT))
    if code != 0:
        sys.exit(code)

def cmd_docker_down():
    print("[dev.py] Stopping Docker compose services...")
    code = run_cmd(["docker", "compose", "down"], cwd=str(REPO_ROOT))
    if code != 0:
        sys.exit(code)

def cmd_dev():
    py_exe = get_python_exe()
    uvicorn_exe = get_uvicorn_exe()
    npm_path = shutil.which("npm") or shutil.which("npm.cmd")

    backend_cmd = [uvicorn_exe, "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    frontend_cmd = [npm_path, "run", "dev"] if npm_path else None

    print("[dev.py] Launching backend dev server and frontend dev server together...")
    procs = []

    try:
        p_back = subprocess.Popen(backend_cmd, cwd=str(BACKEND_DIR))
        procs.append(p_back)

        if frontend_cmd and FRONTEND_DIR.exists():
            p_front = subprocess.Popen(frontend_cmd, cwd=str(FRONTEND_DIR))
            procs.append(p_front)

        # Wait on any process exit
        while True:
            for p in procs:
                if p.poll() is not None:
                    raise KeyboardInterrupt
            import time
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n[dev.py] Caught interrupt. Terminating child processes...")
        for p in procs:
            try:
                p.terminate()
            except Exception:
                pass
        for p in procs:
            try:
                p.wait(timeout=3)
            except Exception:
                p.kill()
        print("[dev.py] Shutdown complete.")

def main():
    if len(sys.argv) < 2:
        print("Usage: dev.py <setup|seed|dev|test|lint|check|docker-up|docker-down>")
        sys.exit(1)

    action = sys.argv[1].lower()
    actions = {
        "setup": cmd_setup,
        "seed": cmd_seed,
        "dev": cmd_dev,
        "test": cmd_test,
        "lint": cmd_lint,
        "check": cmd_check,
        "docker-up": cmd_docker_up,
        "docker-down": cmd_docker_down,
    }

    if action not in actions:
        print(f"Unknown action: {action}. Available: {list(actions.keys())}")
        sys.exit(1)

    actions[action]()

if __name__ == "__main__":
    main()
