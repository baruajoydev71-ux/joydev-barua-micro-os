#!/usr/bin/env python3
"""Experiment 15.2: Journaling File System (WAL) & Crash Recovery Engine."""

class JournalingFS:
    def __init__(self):
        self.disk_state = {"/home/joydev/grades.txt": "v1_initial"}
        self.journal = []

    def log_transaction(self, tx_id, path, new_val, commit=True):
        self.journal.append(("TX_BEGIN", tx_id, path, new_val))
        self.journal.append(("TX_WRITE", tx_id, path, new_val))
        if commit:
            self.journal.append(("TX_COMMIT", tx_id, path, new_val))
            print(f"[JOURNAL] {tx_id}: Logged & COMMITTED update to {path} = '{new_val}'")
        else:
            print(f"[JOURNAL] {tx_id}: Logged WRITE to {path} = '{new_val}' -> *** POWER LOSS! ***")

    def recover(self):
        print("\n=== Crash Recovery Replay ===")
        committed = {rec[1] for rec in self.journal if rec[0] == "TX_COMMIT"}
        seen = []
        for tag, tx_id, path, val in self.journal:
            if tag == "TX_WRITE" and tx_id not in seen:
                seen.append(tx_id)
                if tx_id in committed:
                    self.disk_state[path] = val
                    print(f"  [REDO]    {tx_id} committed -> Applied {path} = '{val}'")
                else:
                    print(f"  [DISCARD] {tx_id} uncommitted -> Rolled back partial write to {path}")
        self.journal.clear()

if __name__ == "__main__":
    jfs = JournalingFS()
    print(f"Pre-Crash Disk State : {jfs.disk_state}")
    jfs.log_transaction("TX-01", "/home/joydev/grades.txt", "v2_verified", commit=True)
    jfs.log_transaction("TX-02", "/home/joydev/grades.txt", "v3_corrupt_partial", commit=False)
    jfs.recover()
    print(f"Post-Recovery State  : {jfs.disk_state}")
