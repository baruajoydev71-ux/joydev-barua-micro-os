#!/usr/bin/env python3
"""
CA-6 Visualizer Script
Renders ASCII Gantt charts, queue migration graphs, and timeline diagrams
from Micro-OS scheduler traces.
"""

import sys
import os
import re

def render_gantt_chart(filepath, max_ticks=60):
    if not os.path.exists(filepath):
        print(f"Warning: File {filepath} not found for visualization.")
        return

    timeline = []
    with open(filepath, 'r') as f:
        for line in f:
            if 'TASK_EXEC' in line:
                m = re.search(r'\[(\d+)\]\s+TASK_EXEC\s+task_id=(\d+)', line)
                if m:
                    tick = int(m.group(1))
                    tid = int(m.group(2))
                    while len(timeline) < tick:
                        timeline.append(' ')
                    timeline.append(str(tid))
            elif 'CPU_IDLE' in line:
                m = re.search(r'\[(\d+)\]\s+CPU_IDLE', line)
                if m:
                    tick = int(m.group(1))
                    while len(timeline) < tick:
                        timeline.append(' ')
                    timeline.append('.')

    print(f"\nTimeline Gantt Chart for: {os.path.basename(filepath)}")
    print("Legend: [1]=Task-1, [2]=Task-2, [3]=Task-3, [4]=Task-4, [.]=CPU Idle")
    print("-" * min(len(timeline) + 10, max_ticks + 10))

    chunk_size = 50
    for i in range(0, min(len(timeline), max_ticks), chunk_size):
        chunk = timeline[i:i+chunk_size]
        header = f"Tick {i:03d}-{i+len(chunk)-1:03d} | "
        bar = "".join([f"[{c}]" for c in chunk])
        print(header + bar)
    print("-" * min(len(timeline) + 10, max_ticks + 10))

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rr_trace = os.path.join(base_dir, "traces", "round_robin_trace.log")
    mlfq_trace = os.path.join(base_dir, "traces", "mlfq_trace.log")

    render_gantt_chart(rr_trace)
    render_gantt_chart(mlfq_trace)

if __name__ == "__main__":
    main()
