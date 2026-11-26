#!/usr/bin/env python3
"""Experiment 3.1: Child Execution Timing via OS Pipe IPC."""
import multiprocessing
import subprocess
import sys
import time

def timed_child(conn, cmd):
    start_ts = time.perf_counter()
    conn.send(start_ts)
    conn.close()
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

def measure_command(label, cmd):
    parent_conn, child_conn = multiprocessing.Pipe(duplex=False)
    proc = multiprocessing.Process(target=timed_child, args=(child_conn, cmd))
    proc.start()
    child_conn.close()
    start_ts = parent_conn.recv()
    parent_conn.close()
    proc.join()
    elapsed = time.perf_counter() - start_ts
    print(f"Command '{label}' completed in {elapsed:.6f} seconds (exit={proc.exitcode})")

if __name__ == "__main__":
    measure_command("python --version", [sys.executable, "--version"])
    measure_command("sleep 0.20s", [sys.executable, "-c", "import time; time.sleep(0.20)"])
