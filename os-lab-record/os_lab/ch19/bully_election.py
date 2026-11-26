#!/usr/bin/env python3
"""Experiment 19.3: Bully Distributed Leader Election Simulator."""

def run_bully_election(nodes, failed, initiator):
    alive = sorted(n for n in nodes if n not in failed)
    print(f"Cluster Nodes: {nodes} | Crashed: {sorted(failed)} | Initiator: Node-{initiator}\n")
    current = initiator
    while True:
        higher = [n for n in nodes if n > current]
        print(f"  [Node-{current}] Sends ELECTION -> {higher}")
        responders = [n for n in higher if n in alive]
        if not responders:
            print(f"  [Node-{current}] No higher node responded! Declaring victory.")
            for peer in [n for n in alive if n != current]:
                print(f"  [Node-{current}] Broadcast COORDINATOR -> Node-{peer}")
            print(f"\nNew Elected Cluster Coordinator: Node-{current}")
            return current
        for r in responders:
            print(f"  [Node-{r}] Replies OK -> Node-{current} (Taking over election)")
        current = responders[0]

if __name__ == "__main__":
    run_bully_election(nodes=[1, 2, 3, 4, 5, 6], failed={6}, initiator=3)
