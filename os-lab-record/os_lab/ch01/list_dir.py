#!/usr/bin/env python3
"""Experiment 1.1: Directory Traversal using OS directory stream APIs."""
import os
import sys

def list_directory(path):
    if not os.path.isdir(path):
        print(f"Error: '{path}' is not a valid directory.", file=sys.stderr)
        sys.exit(1)

    print(f"Directory listing for '{path}':")
    print(f"  {'TYPE':<6} {'INODE':<20} {'ENTRY NAME'}")
    print("  " + "-" * 46)
    with os.scandir(path) as stream:
        entries = sorted(stream, key=lambda e: e.name.lower())
        for entry in entries:
            kind = "DIR" if entry.is_dir() else "FILE"
            print(f"  {kind:<6} {entry.inode():<20} {entry.name}")
    print(f"\nTotal entries traversed: {len(entries)}")

if __name__ == "__main__":
    target = input("ENTER DIRECTORY NAME: ").strip() or "."
    if not sys.stdin.isatty():
        print(target)
    list_directory(target)
