#!/usr/bin/env python3
"""Experiment 7.3: Deadlock-Free Dining Philosophers via Asymmetric Ordering."""
import threading
import time

N = 5
forks = [threading.Lock() for _ in range(N)]

def philosopher(pid):
    left = pid
    right = (pid + 1) % N
    first, second = (left, right) if pid % 2 == 0 else (right, left)
    print(f"Philosopher {pid} is thinking.")
    with forks[first]:
        with forks[second]:
            print(f"  [Philosopher {pid}] Acquired forks ({first}, {second}) -> EATING.")
            time.sleep(0.03)
    print(f"Philosopher {pid} finished eating and released forks.")

if __name__ == "__main__":
    threads = [threading.Thread(target=philosopher, args=(i,)) for i in range(N)]
    for t in threads: t.start()
    for t in threads: t.join()
    print("All 5 philosophers completed dining with zero deadlock.")
