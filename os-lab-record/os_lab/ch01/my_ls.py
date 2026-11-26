#!/usr/bin/env python3
"""Experiment 1.4: UNIX 'ls' Utility with CLI Directory Argument."""
import os
import sys

def run_ls(dir_path):
    if not os.path.isdir(dir_path):
        print(f"my_ls: cannot access '{dir_path}': No such directory", file=sys.stderr)
        sys.exit(1)

    print(f"Contents of directory '{dir_path}':")
    for name in sorted(os.listdir(dir_path)):
        full = os.path.join(dir_path, name)
        size = os.path.getsize(full) if os.path.isfile(full) else 0
        tag = "[DIR] " if os.path.isdir(full) else "[FILE]"
        print(f"  {tag}  {size:>8} bytes   {name}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <directory_path>", file=sys.stderr)
        sys.exit(1)
    run_ls(sys.argv[1])
