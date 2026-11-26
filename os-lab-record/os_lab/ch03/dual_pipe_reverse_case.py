#!/usr/bin/env python3
"""Experiment 3.4: Full-Duplex IPC via Dual Unidirectional Pipes."""
import multiprocessing

def child_invert(p1_read, p2_write):
    msg = p1_read.recv()
    toggled = msg.swapcase()
    p2_write.send(toggled)
    p1_read.close()
    p2_write.close()

if __name__ == "__main__":
    p1_r, p1_w = multiprocessing.Pipe(duplex=False)
    p2_r, p2_w = multiprocessing.Pipe(duplex=False)

    child = multiprocessing.Process(target=child_invert, args=(p1_r, p2_w))
    child.start()
    p1_r.close()
    p2_w.close()

    original = "Joydev Barua - Operating Systems IPC 2026!"
    print(f"Parent sent     : {original}")
    p1_w.send(original)
    p1_w.close()

    reply = p2_r.recv()
    p2_r.close()
    child.join()
    print(f"Parent received : {reply}")
