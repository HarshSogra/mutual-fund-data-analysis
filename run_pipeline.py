"""Run the mutual fund analysis project workflow in order."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def run_python_script(script_name: str) -> bool:
    """Run an existing Python script if it is present."""
    script_path = BASE_DIR / script_name
    if not script_path.exists():
        print(f"Skipping {script_name}: file not found.")
        return False

    print("\n" + "=" * 70)
    print(f"Running {script_name}")
    print("=" * 70)

    try:
        subprocess.run([sys.executable, str(script_path)], cwd=BASE_DIR, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"Error: {script_name} failed with exit code {exc.returncode}.")
        return False

    print(f"Completed {script_name}.")
    return True


def run_notebook(notebook_name: str) -> bool:
    """Execute an existing notebook through Jupyter without rewriting it."""
    notebook_path = BASE_DIR / "notebooks" / notebook_name
    if not notebook_path.exists():
        print(f"Skipping {notebook_name}: notebook not found.")
        return False

    if shutil.which("jupyter") is None:
        print(f"Skipping {notebook_name}: Jupyter is not available on PATH.")
        return False

    print("\n" + "=" * 70)
    print(f"Running notebook {notebook_name}")
    print("=" * 70)

    command = [
        "jupyter",
        "nbconvert",
        "--to",
        "notebook",
        "--execute",
        "--stdout",
        str(notebook_path),
    ]

    try:
        subprocess.run(
            command,
            cwd=BASE_DIR,
            check=True,
            stdout=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError as exc:
        print(f"Error: {notebook_name} failed with exit code {exc.returncode}.")
        return False

    print(f"Completed notebook {notebook_name}.")
    return True


def main() -> None:
    """Run data cleaning, database loading, and available analytics notebooks."""
    print("=" * 70)
    print(" MUTUAL FUND ANALYSIS PIPELINE")
    print("=" * 70)

    run_python_script("clean_data.py")
    run_python_script("load_to_sqlite.py")

    notebooks = [
        "EDA_Analysis.ipynb",
        "Performance_Analytics.ipynb",
        "Advanced_Analytics.ipynb",
    ]
    for notebook in notebooks:
        run_notebook(notebook)

    run_python_script("test_queries.py")

    print("\n" + "=" * 70)
    print(" PIPELINE RUN COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
