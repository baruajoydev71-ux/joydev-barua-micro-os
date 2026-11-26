#!/usr/bin/env python3
"""Experiment 7.2: First Readers-Writers Synchronization Protocol."""
import threading
import time

shared_record = 100
reader_count = 0
count_lock = threading.Lock()
rw_lock = threading.Lock()

def reader(rid):
    global reader_count
    with count_lock:
        reader_count += 1
        if reader_count == 1:
            rw_lock.acquire()
    print(f"[Reader {rid}] Reading shared_record = {shared_record} (Active readers: {reader_count})")
    time.sleep(0.03)
    with count_lock:
        reader_count -= 1
        if reader_count == 0:
            rw_lock.release()

def writer(wid, new_val):
    global shared_record
    with rw_lock:
        print(f"  [Writer {wid}] EXCLUSIVE LOCK acquired. Updating {shared_record} -> {new_val}")
        shared_record = new_val
        time.sleep(0.04)
        print(f"  [Writer {wid}] Update committed. Releasing exclusive lock.")

if __name__ == "__main__":
    threads = [
        threading.Thread(target=reader, args=(1,)),
        threading.Thread(target=reader, args=(2,)),
        threading.Thread(target=writer, args=(1, 298)),
        threading.Thread(target=reader, args=(3,)),
    ]
    for t in threads: t.start()
    for t in threads: t.join()
    print(f"Final verified shared_record = {shared_record}")
