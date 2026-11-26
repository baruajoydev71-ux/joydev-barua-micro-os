#!/usr/bin/env python3
"""Experiment 1.5: UNIX 'grep' Pattern Search Utility."""
import sys

def grep_file(filepath, pattern):
    occurrences = 0
    with open(filepath, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            text = line.rstrip("\n")
            if pattern in text:
                print(f"{filepath}:{line_num}: {text}")
                occurrences += 1
    print(f"\nTotal occurrences of '{pattern}' found: {occurrences}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <filename> <pattern>", file=sys.stderr)
        sys.exit(1)
    grep_file(sys.argv[1], sys.argv[2])
