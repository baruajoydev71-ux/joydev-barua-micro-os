#!/usr/bin/env python3
"""Experiment 3.8: Linear & Recursive DFS OS Task Tree Traversal."""

TASK_TREE = {
    1:   {"name": "systemd",      "children": [2, 120, 410]},
    2:   {"name": "kthreadd",     "children": [3, 4]},
    3:   {"name": "rcu_sched",    "children": []},
    4:   {"name": "ksoftirqd/0",  "children": []},
    120: {"name": "sshd",         "children": [125]},
    125: {"name": "joydev-sh",    "children": [128, 129]},
    128: {"name": "micro-os",     "children": []},
    129: {"name": "cargo_test",   "children": []},
    410: {"name": "cron",         "children": []},
}

def dfs_walk(pid, depth=0):
    node = TASK_TREE[pid]
    prefix = "  " * depth + ("|-- " if depth > 0 else "")
    print(f"{prefix}[PID {pid:>3}] {node['name']}")
    for child_pid in node["children"]:
        dfs_walk(child_pid, depth + 1)

if __name__ == "__main__":
    print("Linear Task Table:", [f"{k}:{v['name']}" for k, v in TASK_TREE.items()])
    print("\nRecursive DFS Process Tree Hierarchy:")
    dfs_walk(1)
