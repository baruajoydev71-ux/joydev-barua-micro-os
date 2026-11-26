#!/usr/bin/env python3
"""Experiment 3.3: Child Collatz Computation via OS Shared Memory."""
import multiprocessing
from multiprocessing import shared_memory
import os

def collatz_worker(start_val, shm_name):
    seq = [start_val]
    n = start_val
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        seq.append(n)
    payload = ", ".join(map(str, seq)).encode("utf-8")
    shm = shared_memory.SharedMemory(name=shm_name)
    shm.buf[:len(payload)] = payload
    shm.buf[len(payload)] = 0
    print(f"[Child PID {os.getpid()}] Wrote {len(seq)} Collatz terms for n={start_val} to shared memory.")
    shm.close()

def run_collatz(n):
    shm = shared_memory.SharedMemory(create=True, size=1024)
    try:
        proc = multiprocessing.Process(target=collatz_worker, args=(n, shm.name))
        proc.start()
        proc.join()
        raw = bytes(shm.buf).split(b"\x00", 1)[0].decode("utf-8")
        print(f"[Parent PID {os.getpid()}] Read from SHM: {raw}\n")
    finally:
        shm.close()
        shm.unlink()

if __name__ == "__main__":
    run_collatz(12)
    run_collatz(27)
