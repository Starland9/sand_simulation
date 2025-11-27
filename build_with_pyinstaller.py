#!/usr/bin/env python3
"""Helper script to build the Sand Simulation application with PyInstaller."""

from pathlib import Path
import PyInstaller.__main__


def main() -> None:
    repo_root = Path(__file__).resolve().parent
    spec_file = repo_root / "sand_simulation.spec"

    if not spec_file.exists():
        raise FileNotFoundError(f"Spec file not found: {spec_file}")

    PyInstaller.__main__.run([
        str(spec_file),
        "--noconfirm",
        "--clean",
    ])


if __name__ == "__main__":
    main()
