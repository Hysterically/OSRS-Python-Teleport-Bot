#!/usr/bin/env python3
"""Cross-platform build script for EssayReview."""
from __future__ import annotations
import os
import shutil
import subprocess
import sys


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.check_call(cmd)


def main() -> None:
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)

    # Ensure PyInstaller is installed
    run([sys.executable, "-m", "pip", "install", "--upgrade", "pyinstaller"])

    sep = ";" if os.name == "nt" else ":"
    add_data = f"assets{sep}assets"

    # Clean previous builds
    for folder in ("build", "dist"):
        if os.path.isdir(folder):
            shutil.rmtree(folder)

    # Build the executable
    run([
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name",
        "EssayReview",
        "--add-data",
        add_data,
        os.path.join("src", "EssayReview.pyw"),
    ])

    print("\n✅ Build complete. Executable is in the dist folder.")


if __name__ == "__main__":
    main()
