#!/usr/bin/env python3
"""Experiment 3.5: Inter-Process File Transfer via OS Pipe."""
import multiprocessing

def child_writer(read_conn, dst_path):
    with open(dst_path, "wb") as dst:
        while True:
            try:
                chunk = read_conn.recv_bytes()
                dst.write(chunk)
            except EOFError:
                break
    read_conn.close()

def pipe_copy(src_path, dst_path):
    r_conn, w_conn = multiprocessing.Pipe(duplex=False)
    proc = multiprocessing.Process(target=child_writer, args=(r_conn, dst_path))
    proc.start()
    r_conn.close()

    with open(src_path, "rb") as src:
        while True:
            chunk = src.read(512)
            if not chunk:
                break
            w_conn.send_bytes(chunk)
    w_conn.close()
    proc.join()
    print(f"Pipe file transfer complete: '{src_path}' -> '{dst_path}'")

if __name__ == "__main__":
    with open("ipc_in.txt", "w", encoding="utf-8") as f:
        f.write("Joydev Micro-OS IPC Pipe Streaming Payload (25BTRCL298).")
    pipe_copy("ipc_in.txt", "ipc_out.txt")
    with open("ipc_out.txt", "r", encoding="utf-8") as f:
        print("Verified destination content:", f.read())
