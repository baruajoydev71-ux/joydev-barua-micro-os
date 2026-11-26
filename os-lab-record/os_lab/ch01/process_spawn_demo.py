#!/usr/bin/env python3
"""Experiment 1.2: Child Process Creation, PID/PPID Inspection & Reaping."""
import multiprocessing
import os
import sys

def child_worker(student_name):
    print(f"[Child Process]  PID = {os.getpid()} | Parent PPID = {os.getppid()} | Owner = {student_name}")
    print("[Child Process]  Executing isolated workload and exiting with code 0.")
    sys.exit(0)

if __name__ == "__main__":
    print(f"[Parent Process] PID = {os.getpid()} | Spawning child process...")
    child = multiprocessing.Process(target=child_worker, args=("Joydev Barua",))
    child.start()
    print(f"[Parent Process] Created Child PID = {child.pid}. Waiting for termination...")
    child.join()
    print(f"[Parent Process] Reaped Child PID = {child.pid} (exitcode = {child.exitcode}).")
