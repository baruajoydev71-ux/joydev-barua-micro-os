#!/usr/bin/env python3
"""
CA-6 Trace Analysis Script
Parses Micro-OS kernel log traces and computes quantitative operating system metrics:
- Task switch frequency and scheduling latency
- Per-task Response Time, Waiting Time, and Turnaround Time
- CPU Utilization and Idle ratios
- Jain's Fairness Index
- MLFQ Queue residence & demotion distribution
"""

import sys
import os
import re

def parse_trace(filepath):
    if not os.path.exists(filepath):
        print(f"Error: Trace file not found at {filepath}")
        return None

    events = []
    task_stats = {} # task_id -> {name, arrival, first_exec, completion, cpu_ticks, switches, queue_ticks: {0:0, 1:0, 2:0}}
    switch_reasons = {}
    total_ticks = 0
    idle_ticks = 0

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            match = re.match(r'\[(\d+)\]\s+(\w+)\s+(.*)', line)
            if not match:
                continue

            tick = int(match.group(1))
            event_type = match.group(2)
            payload = match.group(3)
            total_ticks = max(total_ticks, tick)

            if event_type == 'CPU_IDLE':
                idle_ticks += 1
            elif event_type == 'TASK_SWITCH':
                # prev=... next=... name=... prio=... reason=...
                p_match = re.search(r'next=(\d+)\s+name="([^"]+)"\s+prio=(\d+)\s+reason=(\w+)', payload)
                if p_match:
                    tid = int(p_match.group(1))
                    name = p_match.group(2)
                    prio = int(p_match.group(3))
                    reason = p_match.group(4)

                    switch_reasons[reason] = switch_reasons.get(reason, 0) + 1

                    if tid not in task_stats:
                        task_stats[tid] = {
                            'name': name,
                            'arrival': 0,
                            'first_exec': tick,
                            'completion': None,
                            'cpu_ticks': 0,
                            'switches': 0,
                            'queue_ticks': {0: 0, 1: 0, 2: 0}
                        }
                    else:
                        if task_stats[tid]['first_exec'] is None:
                            task_stats[tid]['first_exec'] = tick

                    task_stats[tid]['switches'] += 1

            elif event_type == 'TASK_EXEC':
                e_match = re.search(r'task_id=(\d+)\s+name="([^"]+)"\s+burst_rem=(\d+)\s+prio=(\d+)', payload)
                if e_match:
                    tid = int(e_match.group(1))
                    name = e_match.group(2)
                    rem = int(e_match.group(3))
                    prio = int(e_match.group(4))

                    if tid not in task_stats:
                        task_stats[tid] = {
                            'name': name,
                            'arrival': 0,
                            'first_exec': tick,
                            'completion': None,
                            'cpu_ticks': 0,
                            'switches': 1,
                            'queue_ticks': {0: 0, 1: 0, 2: 0}
                        }

                    task_stats[tid]['cpu_ticks'] += 1
                    task_stats[tid]['queue_ticks'][prio] = task_stats[tid]['queue_ticks'].get(prio, 0) + 1

                    if rem == 0:
                        task_stats[tid]['completion'] = tick

    # Finalize stats
    for tid, s in task_stats.items():
        if s['completion'] is None:
            s['completion'] = total_ticks
        s['turnaround'] = s['completion'] - s['arrival']
        s['waiting'] = s['turnaround'] - s['cpu_ticks']
        s['response'] = (s['first_exec'] - s['arrival']) if s['first_exec'] is not None else 0

    cpu_list = [s['cpu_ticks'] for s in task_stats.values()]
    n = len(cpu_list)
    if n > 0 and sum(x*x for x in cpu_list) > 0:
        fairness = (sum(cpu_list) ** 2) / (n * sum(x*x for x in cpu_list))
    else:
        fairness = 1.0

    return {
        'filepath': filepath,
        'total_ticks': total_ticks,
        'idle_ticks': idle_ticks,
        'task_stats': task_stats,
        'switch_reasons': switch_reasons,
        'fairness': fairness
    }

def print_summary(data, title):
    if not data:
        return
    print("\n" + "=" * 70)
    print(f" LOG TRACE ANALYSIS: {title}")
    print("=" * 70)
    print(f" Source Trace File  : {data['filepath']}")
    print(f" Total Simulation Ticks: {data['total_ticks']}")
    print(f" Idle Ticks         : {data['idle_ticks']} ({data['idle_ticks']/max(1, data['total_ticks'])*100:.2f}%)")
    print(f" Jain's Fairness    : {data['fairness']:.4f}")
    print("-" * 70)
    print(f"{'Task ID':<8} {'Name':<12} {'CPU':>6} {'Wait':>6} {'Resp':>6} {'Turn':>6} {'Switches':>9}")
    print("-" * 70)

    avg_wait = 0
    avg_turn = 0
    avg_resp = 0
    total_switches = 0
    tasks = data['task_stats']

    for tid in sorted(tasks.keys()):
        s = tasks[tid]
        print(f"{tid:<8} {s['name']:<12} {s['cpu_ticks']:>6} {s['waiting']:>6} {s['response']:>6} {s['turnaround']:>6} {s['switches']:>9}")
        avg_wait += s['waiting']
        avg_turn += s['turnaround']
        avg_resp += s['response']
        total_switches += s['switches']

    n = max(1, len(tasks))
    print("-" * 70)
    print(f"{'AVERAGE':<20} {sum(s['cpu_ticks'] for s in tasks.values())/n:>6.1f} {avg_wait/n:>6.1f} {avg_resp/n:>6.1f} {avg_turn/n:>6.1f} {total_switches:>9}")
    print("=" * 70)

    if data['switch_reasons']:
        print(" Context Switch Reason Breakdown:")
        for reason, count in data['switch_reasons'].items():
            print(f"   - {reason:<25} : {count} occurrences")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rr_trace = os.path.join(base_dir, "traces", "round_robin_trace.log")
    mlfq_trace = os.path.join(base_dir, "traces", "mlfq_trace.log")

    print("[ANALYSIS] Parsing Micro-OS kernel scheduler traces...")
    data_rr = parse_trace(rr_trace)
    data_mlfq = parse_trace(mlfq_trace)

    print_summary(data_rr, "Round Robin Core Scheduler")
    print_summary(data_mlfq, "Multi-Level Feedback Queue (MLFQ) Specialization")

if __name__ == "__main__":
    main()
