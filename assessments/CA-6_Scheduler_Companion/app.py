#!/usr/bin/env python3
"""
Joydev Micro-OS - Round Robin Scheduler Simulator Companion
Developed by Joydev Barua
Course: Operating Systems (CA6)
Architecture: x86_64 | Specialization: Scheduler Engineering

NOTE: This companion application is an interactive educational scheduler simulator.
The production operating system runs as a bare-metal Rust kernel inside QEMU.
"""

import gradio as gr
import pandas as pd
import plotly.express as px
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional

@dataclass
class Task:
    id: int
    name: str
    burst_time: int
    priority: str
    is_io_bound: bool
    remaining_time: int = 0
    waiting_time: int = 0
    turnaround_time: int = 0
    context_switches: int = 0
    last_scheduled_tick: int = 0
    burst_history: List[int] = field(default_factory=list)
    completion_tick: int = 0

    def average_burst(self) -> int:
        if not self.burst_history:
            return 8
        recent = self.burst_history[-4:]
        return max(1, sum(recent) // len(recent))

def calculate_dynamic_quantum(task: Task, current_tick: int, base_quantum: int, enable_dynamic: bool) -> Tuple[int, str]:
    if not enable_dynamic:
        return base_quantum, "Static Baseline"

    if not task.burst_history:
        prio_map = {"Low": 6, "Normal": base_quantum, "High": base_quantum + 4, "Realtime": base_quantum + 8}
        return prio_map.get(task.priority, base_quantum), "Default Initial"

    avg_burst = task.average_burst()
    if task.is_io_bound:
        quantum = max(2, min(6, avg_burst // 2))
        reason = "Burst Adaptation (I/O-Bound)"
    else:
        quantum = max(2, min(18, avg_burst))
        reason = "Burst Adaptation (CPU-Bound)"

    # Anti-starvation check
    wait_time = current_tick - task.last_scheduled_tick
    if wait_time > 20:
        boost = min(6, (wait_time - 20) // 5)
        quantum += boost
        reason = "Starvation Prevention"

    # Priority weighting
    prio_multipliers = {"Low": 0.75, "Normal": 1.0, "High": 1.25, "Realtime": 1.5}
    quantum = int(quantum * prio_multipliers.get(task.priority, 1.0))
    quantum = max(2, min(24, quantum))

    return quantum, reason

def run_simulation(base_quantum: int, enable_dynamic: bool, cs_overhead: int,
                   t1_burst: int, t1_prio: str, t1_io: bool,
                   t2_burst: int, t2_prio: str, t2_io: bool,
                   t3_burst: int, t3_prio: str, t3_io: bool,
                   t4_burst: int, t4_prio: str, t4_io: bool):

    initial_tasks = [
        Task(1, "Task 1 (Alpha - Compute)", t1_burst, t1_prio, t1_io, remaining_time=t1_burst),
        Task(2, "Task 2 (Beta - Interactive)", t2_burst, t2_prio, t2_io, remaining_time=t2_burst),
        Task(3, "Task 3 (Gamma - Synchronized)", t3_burst, t3_prio, t3_io, remaining_time=t3_burst),
        Task(4, "Task 4 (Delta - Memory)", t4_burst, t4_prio, t4_io, remaining_time=t4_burst),
    ]

    ready_queue: List[int] = [t.id for t in initial_tasks]
    task_map: Dict[int, Task] = {t.id: t for t in initial_tasks}

    current_tick = 0
    intervals = []
    trace_logs = []
    total_context_switches = 0
    max_simulation_ticks = 300

    trace_logs.append(f"[SYSTEM] Joydev Micro-OS Scheduler Simulation Started. Dynamic Quantum = {enable_dynamic}")

    while ready_queue and current_tick < max_simulation_ticks:
        task_id = ready_queue.pop(0)
        task = task_map[task_id]

        # Calculate quantum
        quantum, reason = calculate_dynamic_quantum(task, current_tick, base_quantum, enable_dynamic)

        # Context switch overhead
        if cs_overhead > 0:
            current_tick += cs_overhead

        start_tick = current_tick
        exec_duration = min(task.remaining_time, quantum)
        current_tick += exec_duration
        task.remaining_time -= exec_duration
        task.context_switches += 1
        total_context_switches += 1

        # Record burst
        task.burst_history.append(exec_duration)

        # Record Gantt interval
        intervals.append({
            "Task": task.name,
            "Start": start_tick,
            "Finish": current_tick,
            "Quantum": quantum,
            "Reason": reason,
            "Duration": exec_duration
        })

        trace_logs.append(
            f"Tick {start_tick:03d}-{current_tick:03d} | Scheduled: {task.name:<28} | Q={quantum:02d} ({reason}) | Remaining={task.remaining_time:02d}"
        )

        # Update waiting times for tasks remaining in the ready queue
        for other_id in ready_queue:
            task_map[other_id].waiting_time += (current_tick - start_tick + cs_overhead)

        if task.remaining_time > 0:
            task.last_scheduled_tick = current_tick
            ready_queue.append(task.id)
        else:
            task.completion_tick = current_tick
            task.turnaround_time = task.completion_tick
            trace_logs.append(f"Tick {current_tick:03d} | [TERMINATED] {task.name} completed! Turnaround = {task.turnaround_time} ticks.")

    # Build Results Dataframe
    results_data = []
    for t in initial_tasks:
        results_data.append({
            "Task ID": t.id,
            "Task Name": t.name,
            "Priority": t.priority,
            "Type": "I/O-Bound" if t.is_io_bound else "CPU-Bound",
            "Burst Time": t.burst_time,
            "Waiting Time": t.waiting_time,
            "Turnaround Time": t.turnaround_time,
            "Context Switches": t.context_switches
        })
    df_results = pd.DataFrame(results_data)

    # Calculate Aggregate Metrics
    avg_turnaround = df_results["Turnaround Time"].mean()
    avg_waiting = df_results["Waiting Time"].mean()
    total_burst = sum(t.burst_time for t in initial_tasks)
    cpu_efficiency = (total_burst / max(1, current_tick)) * 100

    # Build Gantt Chart with Plotly
    df_intervals = pd.DataFrame(intervals)
    fig = px.timeline(
        df_intervals,
        x_start="Start",
        x_end="Finish",
        y="Task",
        color="Task",
        hover_data=["Quantum", "Reason", "Duration"],
        title=f"Joydev Micro-OS - Dynamic Round Robin Timeline (Total Ticks: {current_tick})"
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="#1e293b",
        paper_bgcolor="#0f172a",
        font_color="#f8fafc",
        title_font_color="#38bdf8",
        height=320,
        margin=dict(l=40, r=40, t=50, b=40)
    )

    metrics_text = (
        f"**Average Turnaround Time:** {avg_turnaround:.1f} ticks | "
        f"**Average Waiting Time:** {avg_waiting:.1f} ticks | "
        f"**Total Context Switches:** {total_context_switches} | "
        f"**CPU Efficiency:** {cpu_efficiency:.1f}% | "
        f"**Total Makespan:** {current_tick} ticks"
    )

    log_output = "\n".join(trace_logs)

    return fig, df_results, metrics_text, log_output

# Build Gradio UI
with gr.Blocks(theme=gr.themes.Soft(primary_hue="sky", neutral_hue="slate")) as demo:
    gr.Markdown("""
    # Joydev Micro-OS – Round Robin Scheduler
    ### Developed by **Joydev Barua** | Specialization: Scheduler Engineering
    **Course:** Operating Systems CA6 | **Architecture:** x86_64 Bare-Metal Micro-OS
    
    > **DISCLAIMER:** This companion web application is an interactive scheduler simulator designed for visualization, 
    > teaching, and parameter tuning. The core Joydev Micro-OS is implemented in bare-metal `no_std` Rust, booted via Limine, 
    > and executed under QEMU.
    """)

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### ⚙️ Scheduler Configuration")
            base_quantum = gr.Slider(minimum=2, maximum=20, value=8, step=1, label="Baseline Time Quantum (ticks)")
            enable_dynamic = gr.Checkbox(value=True, label="Enable Dynamic Quantum Adaptation (Specialization)")
            cs_overhead = gr.Slider(minimum=0, maximum=3, value=0, step=1, label="Context Switch Overhead (ticks)")

            gr.Markdown("### 📋 Controlled Task Workloads")
            with gr.Accordion("Task 1: Compute-Alpha", open=False):
                t1_burst = gr.Number(value=18, label="Burst Time (ticks)")
                t1_prio = gr.Radio(["Low", "Normal", "High", "Realtime"], value="Normal", label="Priority")
                t1_io = gr.Checkbox(value=False, label="I/O-Bound")

            with gr.Accordion("Task 2: Interactive-Beta", open=False):
                t2_burst = gr.Number(value=10, label="Burst Time (ticks)")
                t2_prio = gr.Radio(["Low", "Normal", "High", "Realtime"], value="High", label="Priority")
                t2_io = gr.Checkbox(value=True, label="I/O-Bound")

            with gr.Accordion("Task 3: Sync-Gamma", open=False):
                t3_burst = gr.Number(value=14, label="Burst Time (ticks)")
                t3_prio = gr.Radio(["Low", "Normal", "High", "Realtime"], value="Normal", label="Priority")
                t3_io = gr.Checkbox(value=False, label="I/O-Bound")

            with gr.Accordion("Task 4: Memory-Delta", open=False):
                t4_burst = gr.Number(value=12, label="Burst Time (ticks)")
                t4_prio = gr.Radio(["Low", "Normal", "High", "Realtime"], value="Low", label="Priority")
                t4_io = gr.Checkbox(value=False, label="I/O-Bound")

            simulate_btn = gr.Button("🚀 Run Scheduler Simulation", variant="primary")

        with gr.Column(scale=2):
            gr.Markdown("### 📊 Interactive Scheduling Timeline (Gantt Chart)")
            gantt_plot = gr.Plot()
            metrics_display = gr.Markdown()

            gr.Markdown("### 📈 Task Performance & Accounting Table")
            results_table = gr.Dataframe()

            with gr.Accordion("📜 Real-time Scheduler Trace Logs", open=True):
                logs_view = gr.Textbox(lines=10, label="Kernel Scheduler Log Mirror", interactive=False)

    simulate_btn.click(
        fn=run_simulation,
        inputs=[
            base_quantum, enable_dynamic, cs_overhead,
            t1_burst, t1_prio, t1_io,
            t2_burst, t2_prio, t2_io,
            t3_burst, t3_prio, t3_io,
            t4_burst, t4_prio, t4_io
        ],
        outputs=[gantt_plot, results_table, metrics_display, logs_view]
    )

    demo.load(
        fn=run_simulation,
        inputs=[
            base_quantum, enable_dynamic, cs_overhead,
            t1_burst, t1_prio, t1_io,
            t2_burst, t2_prio, t2_io,
            t3_burst, t3_prio, t3_io,
            t4_burst, t4_prio, t4_io
        ],
        outputs=[gantt_plot, results_table, metrics_display, logs_view]
    )

if __name__ == "__main__":
    demo.launch()
