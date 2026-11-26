#!/usr/bin/env python3
"""Experiment 3.6: Custom Command Shell (Joydev-Shell v1.0) with !! & Redirection."""
import shlex
import sys

def run_shell():
    print("Joydev-Shell v1.0 initialized (Student: Joydev Barua | 25BTRCL298).")
    history = []
    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue
        print(f"joydev-sh> {line}")
        if line == "exit":
            print("Exiting Joydev-Shell cleanly.")
            break
        if line == "!!":
            if not history:
                print("No commands in history.")
                continue
            line = history[-1]
            print(f"[History Recall] Re-executing: {line}")
        history.append(line)

        out_file = None
        if ">" in line:
            cmd_part, out_file = [p.strip() for p in line.split(">", 1)]
            tokens = shlex.split(cmd_part)
        else:
            tokens = shlex.split(line)

        if tokens[0] == "echo":
            output = " ".join(tokens[1:])
        elif tokens[0] == "whoami":
            output = "Joydev Barua (25BTRCL298)"
        else:
            output = f"Executed external binary: {tokens[0]}"

        if out_file:
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(output + "\n")
            print(f"[Redirection] Wrote stdout to '{out_file}': {output}")
        else:
            print(output)

if __name__ == "__main__":
    run_shell()
