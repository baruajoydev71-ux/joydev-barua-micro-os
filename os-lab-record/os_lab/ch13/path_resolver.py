#!/usr/bin/env python3
"""Experiment 13.2: Hierarchical Directory Tree & Canonical Path Resolver."""

FS_TREE = {
    "home": {
        "joydev": {
            "os_lab": {
                "ch13": {"report.md": "FILE(2048B)", "inode_inspector.py": "FILE(780B)"},
                "notes.txt": "FILE(512B)",
            }
        }
    },
    "etc": {"hostname": "FILE(14B)"},
}

def resolve_path(raw_path):
    stack = []
    for part in raw_path.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if stack:
                stack.pop()
        else:
            stack.append(part)
    node = FS_TREE
    for comp in stack:
        if isinstance(node, dict) and comp in node:
            node = node[comp]
        else:
            return "/" + "/".join(stack), "ENOENT (Not Found)"
    kind = "DIRECTORY" if isinstance(node, dict) else node
    return "/" + "/".join(stack), f"RESOLVED -> {kind}"

if __name__ == "__main__":
    tests = [
        "/home/joydev/../joydev/os_lab/./ch13/report.md",
        "/home/joydev/os_lab/ch13/..",
        "/etc/./hostname",
        "/home/joydev/os_lab/missing.bin",
    ]
    for path in tests:
        canon, status = resolve_path(path)
        print(f"Input : {path}")
        print(f"Canon : {canon:<36} | {status}\n")
