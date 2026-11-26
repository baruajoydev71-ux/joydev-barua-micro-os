#!/usr/bin/env python3
"""Experiment 1.3: UNIX 'cp' Simulation with Character & Space Analysis."""
import sys

def copy_and_count(src_path, dst_path):
    spaces = 0
    chars = 0
    with open(src_path, "r", encoding="utf-8") as src, open(dst_path, "w", encoding="utf-8") as dst:
        for line in src:
            dst.write(line)
            chars += len(line)
            spaces += line.count(" ")
    print(f"Copied '{src_path}' -> '{dst_path}' successfully.")
    print(f"Total characters processed : {chars}")
    print(f"Number of spaces counted   : {spaces}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <source> <destination>", file=sys.stderr)
        sys.exit(1)
    copy_and_count(sys.argv[1], sys.argv[2])
