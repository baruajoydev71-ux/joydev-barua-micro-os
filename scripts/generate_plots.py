#!/usr/bin/env python3
"""
CA-6 High-Resolution Plot Generator
Renders graphical Gantt charts, queue migration diagrams, and performance metric
comparisons between Round Robin and MLFQ using Matplotlib.
Outputs:
  - results/scheduler_comparison.png
  - results/gantt_chart.png
"""

import os
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def parse_trace_timeline(filepath):
    timeline = []
    task_prio = {}
    with open(filepath, 'r') as f:
        for line in f:
            if 'TASK_EXEC' in line:
                m = re.search(r'\[(\d+)\]\s+TASK_EXEC\s+task_id=(\d+)\s+name="([^"]+)"\s+burst_rem=(\d+)\s+prio=(\d+)', line)
                if m:
                    tick = int(m.group(1))
                    tid = int(m.group(2))
                    name = m.group(3)
                    prio = int(m.group(5))
                    timeline.append((tick, tid, name, prio))
                    if tid not in task_prio:
                        task_prio[tid] = []
                    task_prio[tid].append((tick, prio))
    return timeline, task_prio

def generate_gantt_plot(rr_timeline, mlfq_timeline, output_path):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
    
    colors = {
        1: '#3498db', # Blue: CPU1
        2: '#2ecc71', # Green: IO
        3: '#e74c3c', # Red: CPU2
        4: '#f39c12', # Orange: Mixed
    }
    task_labels = {
        1: 'Task-1 (CPU1)',
        2: 'Task-2 (IO)',
        3: 'Task-3 (CPU2)',
        4: 'Task-4 (Mixed)'
    }

    # Plot Round Robin Gantt
    for tick, tid, name, prio in rr_timeline:
        ax1.broken_barh([(tick - 1, 1)], (tid - 0.4, 0.8), facecolors=colors.get(tid, '#95a5a6'), edgecolor='black', linewidth=0.5)
    
    ax1.set_yticks([1, 2, 3, 4])
    ax1.set_yticklabels([task_labels[i] for i in [1, 2, 3, 4]], fontsize=10)
    ax1.set_title('Round Robin Execution Timeline (Quantum = 2 ticks)', fontsize=12, fontweight='bold', pad=10)
    ax1.grid(True, linestyle='--', alpha=0.5, axis='x')
    ax1.set_ylabel('Tasks')

    # Plot MLFQ Gantt
    for tick, tid, name, prio in mlfq_timeline:
        ax2.broken_barh([(tick - 1, 1)], (tid - 0.4, 0.8), facecolors=colors.get(tid, '#95a5a6'), edgecolor='black', linewidth=0.5)
    
    ax2.set_yticks([1, 2, 3, 4])
    ax2.set_yticklabels([task_labels[i] for i in [1, 2, 3, 4]], fontsize=10)
    ax2.set_title('MLFQ Execution Timeline (Q0=2, Q1=4, Q2=8, Priority Boost=25)', fontsize=12, fontweight='bold', pad=10)
    ax2.grid(True, linestyle='--', alpha=0.5, axis='x')
    ax2.set_xlabel('Simulation Ticks (1 tick = 10 ms)', fontsize=11)
    ax2.set_ylabel('Tasks')

    # Highlight Priority Boost at Tick 25
    ax2.axvline(x=25, color='#8e44ad', linestyle='--', linewidth=2, label='Priority Boost (Tick 25)')
    ax2.legend(loc='upper right')

    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()
    print(f"[PLOT] Generated Gantt Chart plot at: {output_path}")

def generate_metrics_bar_chart(output_path):
    metrics = ['Avg Response Time', 'Avg Waiting Time', 'Avg Turnaround Time', 'Context Switches']
    rr_vals = [3.50, 20.50, 29.50, 14]
    mlfq_vals = [1.75, 19.00, 28.00, 11]

    x = np.arange(len(metrics))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 5))
    rects1 = ax.bar(x - width/2, rr_vals, width, label='Round Robin (Core)', color='#34495e', edgecolor='black')
    rects2 = ax.bar(x + width/2, mlfq_vals, width, label='MLFQ (Specialization)', color='#27ae60', edgecolor='black')

    ax.set_ylabel('Ticks / Count', fontsize=11)
    ax.set_title('Scheduler Performance Comparison: Round Robin vs. MLFQ', fontsize=13, fontweight='bold', pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(metrics, fontsize=10)
    ax.legend(fontsize=11)
    ax.grid(axis='y', linestyle='--', alpha=0.6)

    # Attach value labels
    for rect in rects1:
        height = rect.get_height()
        ax.annotate(f'{height:.2f}', xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9)
    for rect in rects2:
        height = rect.get_height()
        ax.annotate(f'{height:.2f}', xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()
    print(f"[PLOT] Generated Metrics Bar Chart plot at: {output_path}")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rr_trace = os.path.join(base_dir, "traces", "round_robin_trace.log")
    mlfq_trace = os.path.join(base_dir, "traces", "mlfq_trace.log")
    results_dir = os.path.join(base_dir, "results")

    os.makedirs(results_dir, exist_ok=True)
    gantt_png = os.path.join(results_dir, "gantt_chart.png")
    metrics_png = os.path.join(results_dir, "scheduler_comparison.png")

    rr_tl, _ = parse_trace_timeline(rr_trace)
    mlfq_tl, _ = parse_trace_timeline(mlfq_trace)

    generate_gantt_plot(rr_tl, mlfq_tl, gantt_png)
    generate_metrics_bar_chart(metrics_png)

if __name__ == "__main__":
    main()
