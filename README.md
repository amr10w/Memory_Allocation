# Memory Allocation Simulator — Segmentation

A desktop application that simulates **memory allocation and deallocation** using segmentation, built with Python and PyQt6.

Implements both **First-Fit** and **Best-Fit** allocation algorithms with visual memory layout, segment tables, and hole merging on deallocation.

> **Course:** CSE 335s — Operating Systems  
> **Assignment:** Memory Management Project using Segmentation

---

## Features

- **First-Fit & Best-Fit** allocation algorithms
- **Dynamic deallocation** with automatic merging of adjacent holes
- **Visual memory map** showing free, allocated, and occupied regions
- **Segment tables** displayed for every active process
- **Add processes mid-simulation** — no need to define everything upfront
- **Rollback on failure** — if any segment doesn't fit, the entire process allocation is cancelled
- **Report generator** — creates a professional Word document template with screenshot placeholders

---

## Project Structure

```
memory_allocation/
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
├── README.md
├── core/
│   ├── __init__.py
│   ├── memory_models.py     # Hole, Segment, Process data classes
│   └── allocator.py         # MemoryManager (First-Fit, Best-Fit, Deallocation)
├── ui/
│   ├── __init__.py
│   ├── main_window.py       # PyQt6 GUI — input page + simulation page
│   ├── memory_canvas.py     # Visual memory map rendering
│   └── styles.py            # Global stylesheets
└── report/
    └── report.py            # Word report generator
```

---

## Setup & Run

### Prerequisites

- Python 3.10+

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run the Simulator

```bash
python main.py
```

### Generate Report Template

```bash
python report/report.py
```

This creates `Memory_Management_Report.docx` in the project root with screenshot placeholders.

---

## How to Use

### 1. Input Page

1. Enter **Total Memory Size** (in K)
2. Select **Allocation Algorithm** (First-Fit or Best-Fit)
3. *(Optional)* Add **Initial Holes** with starting address and size
4. *(Optional)* Add **Processes** with segments (name + size each)
5. Click **▶ Start Simulation**

### 2. Simulation Page

- **Allocate Next Process** — allocates the first process in the queue
- **➕ Add New Process** — define and add a new process mid-simulation
- **Deallocate** — select an active process and free its memory
- **Memory Layout** — visual bar showing all regions (green = free, colored = allocated, orange = occupied/reserved)
- **Tables** — free holes table, allocated partitions table, and per-process segment tables

---

## Test Case

The following scenario should be run with both First-Fit and Best-Fit:

| Step | Operation |
|------|-----------|
| Setup | Total Memory = 1000, Holes: H1(0,300), H2(400,250), H3(700,200) |
| 1 | Allocate P1: Code=100, Data=120, Stack=90 |
| 2 | Allocate P2: Code=200, Data=40 |
| 3 | Allocate P3: Code=120, Data=50 |
| 4 | Deallocate P1 |
| 5 | Allocate P4: Code=230, Data=40 |

**Expected difference:** First-Fit fails P3 but succeeds P4. Best-Fit succeeds P3 but fails P4.

---

## Data Structures

| Structure | Description |
|-----------|-------------|
| **Allocated Partitions Table** | List of `Segment` objects with name, size, and base address |
| **Free Partitions (Holes) Table** | List of `Hole` objects with starting address and size |
| **Active Processes** | Dictionary mapping process ID → `Process` object |

---

## Algorithms

### First-Fit
Sorts holes by **starting address** and picks the **first** hole large enough for each segment.

### Best-Fit
Filters holes ≥ segment size, sorts by **size ascending**, and picks the **smallest** fitting hole.

### Deallocation
Removes all segments of the process, converts them to holes, sorts by address, and **merges adjacent holes**.
