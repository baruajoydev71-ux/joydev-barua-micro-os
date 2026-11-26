#!/usr/bin/env python3
"""Experiment 8.2: Wait-For Graph (WFG) Cycle Detection for Deadlocks."""

def detect_cycle(wfg):
    visited, stack = set(), set()
    back_edges = []

    def dfs(node):
        visited.add(node)
        stack.add(node)
        for nxt in wfg.get(node, []):
            if nxt not in visited:
                if dfs(nxt):
                    return True
            elif nxt in stack:
                back_edges.append((node, nxt))
                return True
        stack.remove(node)
        return False

    for proc in wfg:
        if proc not in visited and dfs(proc):
            return True, back_edges
    return False, []

if __name__ == "__main__":
    wait_for_graph = {"P1": ["P2"], "P2": ["P3"], "P3": ["P1"], "P4": []}
    found, edges = detect_cycle(wait_for_graph)
    print("Wait-For Graph    :", wait_for_graph)
    print("Deadlock Detected :", found)
    if edges:
        print(f"Cycle Back-Edge   : {edges[0][0]} -> {edges[0][1]}")
