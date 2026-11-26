#!/usr/bin/env python3
"""Experiment 7.1: Thread-Safe Bounded-Buffer Producer-Consumer."""
import threading
import time

CAPACITY = 4
buffer = []
mutex = threading.Lock()
not_empty = threading.Condition(mutex)
not_full = threading.Condition(mutex)

def producer(pid):
    for seq in range(3):
        item = f"Job-P{pid}-{seq}"
        with not_full:
            while len(buffer) == CAPACITY:
                not_full.wait()
            buffer.append(item)
            print(f"[Producer {pid}] Produced {item:<10} | Buffer = {len(buffer)}/{CAPACITY}")
            not_empty.notify()
        time.sleep(0.02)

def consumer(cid):
    for _ in range(3):
        with not_empty:
            while not buffer:
                not_empty.wait()
            item = buffer.pop(0)
            print(f"  [Consumer {cid}] Consumed {item:<10} | Buffer = {len(buffer)}/{CAPACITY}")
            not_full.notify()
        time.sleep(0.03)

if __name__ == "__main__":
    threads = [threading.Thread(target=producer, args=(i,)) for i in range(2)]
    threads += [threading.Thread(target=consumer, args=(i,)) for i in range(2)]
    for t in threads: t.start()
    for t in threads: t.join()
    print("Bounded-buffer execution completed cleanly with zero overflow or deadlock.")
