# CA-6 AI Usage Disclosure Statement (Section 25)

## 1. Scope of Artificial Intelligence Assistance

In accordance with Section 25 of the CA-6 Course Specification, this document explicitly discloses the scope, purpose, and student verification of Generative AI assistance utilized during the design, implementation, and documentation of **Micro-OS**.

---

## 2. Permitted Assistance Categories Utilized

| Category | AI Assistance Utilized | Student Verification & Engineering Ownership |
|---|---|---|
| **Architecture Brainstorming** | Evaluated modular layout patterns for educational microkernels and reviewed Mermaid diagram notation. | Team finalized the 10-layer conceptual hierarchy and data/control flow boundaries. |
| **Rust Syntax & Type System** | Scaffolding idiomatic Rust patterns (e.g., `Deref`/`DerefMut` on RAII guards, `Layout::from_size_align`). | Every line of memory management and atomic ordering was audited for correctness and safety invariants. |
| **Test Case Scaffolding** | Structured boilerplate assertions for the formal test suite (`tests/tc1_minimum_config.rs` through `tc6_repeatability.rs`). | Workload parameters (burst times, quanta, I/O sleep patterns) and pass/fail thresholds were designed and verified by the team. |
| **Python Trace Analysis** | Authored initial regex parsing routines in `scripts/analyze_traces.py` and Matplotlib plotting logic in `scripts/generate_plots.py`. | Formulations for Jain's Fairness Index, Turnaround Time, and External Fragmentation were validated mathematically against OS theory. |
| **Documentation Structuring** | Drafted Markdown outlines for the 20-section Final Technical Report and formatting templates. | Technical explanations, debugging narratives, and Viva defense answers reflect the team's hands-on implementation experience. |

---

## 3. Strict Student Engineering Responsibility

Every member of the team has reviewed, understood, and defended every line of code submitted:
- **Ownership & Borrowing**: All kernel structures obey Rust's compile-time borrowing rules; mutable references (`&mut`) are strictly non-overlapping.
- **`unsafe` Rust Policy**: No `unsafe` block was accepted without an explicit stated invariant, documented bounds check, and clear justification (audited in `docs/design.md`).
- **Low-Level Systems Understanding**: The team can explain the exact CPU execution path during context switches, atomic test-and-set instructions on the memory bus, and intrusive block header manipulation during coalescing.
