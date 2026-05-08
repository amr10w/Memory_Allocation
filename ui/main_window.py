# ui/main_window.py
import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QLineEdit,
    QComboBox, QGroupBox, QFormLayout, QScrollArea,
    QMessageBox, QListWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# Core imports
from core.memory_models import Hole, Segment, Process
from core.allocator import MemoryManager

# UI imports
from ui.styles import GLOBAL_STYLE, HOVER_ONLY_BUTTON_STYLE
from ui.memory_canvas import MemoryMapCanvas


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Memory Allocation Simulator")
        self.setMinimumSize(1050, 720)
        self.setStyleSheet(GLOBAL_STYLE)

        # ── runtime state ──────────────────────────────────────────────
        self.memory_manager: MemoryManager | None = None
        self.pending_holes: list[tuple[int, int]] = []   # (start, size)
        self.pending_processes: list[Process] = []
        self.next_process_id = 1
        self.simulation_started = False          # NEW: track if sim is live

        # ── central stacked widget ─────────────────────────────────────
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self._setup_input_page()       # index 0
        self._setup_simulation_page()  # index 1

        self.stacked_widget.setCurrentIndex(0)

    # ══════════════════════════════════════════════════════════════════
    #  PAGE 0 – INPUT PAGE
    # ══════════════════════════════════════════════════════════════════

    def _setup_input_page(self):
        self.input_page = QWidget()
        main_layout = QVBoxLayout(self.input_page)
        main_layout.setSpacing(14)
        main_layout.setContentsMargins(30, 20, 30, 20)

        # Title
        title = QLabel("⚙  Memory Allocation Simulator")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        main_layout.addWidget(title)

        # ── SECTION 1: Basic Configuration ────────────────────────────
        setup_group = QGroupBox("1. Basic Configuration")
        setup_layout = QFormLayout()
        setup_layout.setSpacing(8)

        self.total_mem_input = QLineEdit()
        self.total_mem_input.setPlaceholderText("e.g. 1024")

        self.algo_dropdown = QComboBox()
        self.algo_dropdown.addItems(["First-Fit", "Best-Fit"])

        setup_layout.addRow("Total Memory Size (K):", self.total_mem_input)
        setup_layout.addRow("Allocation Algorithm:", self.algo_dropdown)
        setup_group.setLayout(setup_layout)
        main_layout.addWidget(setup_group)

        # ── SECTION 2: Initial Holes ───────────────────────────────────
        holes_group = QGroupBox("2. Initial Holes  (optional – leave blank to start with one big free block)")
        holes_v = QVBoxLayout()

        holes_input_row = QHBoxLayout()
        self.hole_start_input = QLineEdit()
        self.hole_start_input.setPlaceholderText("Start Address")
        self.hole_size_input = QLineEdit()
        self.hole_size_input.setPlaceholderText("Size")
        add_hole_btn = QPushButton("＋ Add Hole")
        add_hole_btn.clicked.connect(self._save_hole_input)

        holes_input_row.addWidget(QLabel("Start:"))
        holes_input_row.addWidget(self.hole_start_input)
        holes_input_row.addWidget(QLabel("Size:"))
        holes_input_row.addWidget(self.hole_size_input)
        holes_input_row.addWidget(add_hole_btn)

        self.holes_list_widget = QListWidget()
        self.holes_list_widget.setMaximumHeight(100)

        remove_hole_btn = QPushButton("✕ Remove Selected Hole")
        remove_hole_btn.clicked.connect(self._remove_selected_hole)

        holes_v.addLayout(holes_input_row)
        holes_v.addWidget(self.holes_list_widget)
        holes_v.addWidget(remove_hole_btn)
        holes_group.setLayout(holes_v)
        main_layout.addWidget(holes_group)

        # ── SECTION 3: Processes ──────────────────────────────────────
        proc_group = QGroupBox("3. Processes  (optional – you can also add during simulation)")
        proc_v = QVBoxLayout()

        # Process id label (auto-incremented)
        pid_row = QHBoxLayout()
        self.pid_label = QLabel(f"Process ID: P{self.next_process_id}")
        self.pid_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        pid_row.addWidget(self.pid_label)
        pid_row.addStretch()
        proc_v.addLayout(pid_row)

        # Segment input row
        seg_row = QHBoxLayout()
        self.seg_name_input = QLineEdit()
        self.seg_name_input.setPlaceholderText("Segment name (e.g. Code)")
        self.seg_size_input = QLineEdit()
        self.seg_size_input.setPlaceholderText("Size")
        add_seg_btn = QPushButton("＋ Add Segment")
        add_seg_btn.clicked.connect(self._add_segment_to_current_process)

        seg_row.addWidget(QLabel("Name:"))
        seg_row.addWidget(self.seg_name_input)
        seg_row.addWidget(QLabel("Size:"))
        seg_row.addWidget(self.seg_size_input)
        seg_row.addWidget(add_seg_btn)
        proc_v.addLayout(seg_row)

        # List of segments for current process being built
        self.current_segments_list = QListWidget()
        self.current_segments_list.setMaximumHeight(90)
        proc_v.addWidget(QLabel("Segments for current process:"))
        proc_v.addWidget(self.current_segments_list)

        # Confirm / discard current process
        proc_btn_row = QHBoxLayout()
        confirm_proc_btn = QPushButton("✔ Confirm Process")
        confirm_proc_btn.clicked.connect(self._confirm_process)
        discard_proc_btn = QPushButton("✕ Discard Process")
        discard_proc_btn.clicked.connect(self._discard_current_process)
        proc_btn_row.addWidget(confirm_proc_btn)
        proc_btn_row.addWidget(discard_proc_btn)
        proc_v.addLayout(proc_btn_row)

        # List of confirmed processes + remove button
        proc_v.addWidget(QLabel("Confirmed processes:"))
        self.confirmed_processes_list = QListWidget()
        self.confirmed_processes_list.setMaximumHeight(90)
        proc_v.addWidget(self.confirmed_processes_list)

        remove_proc_btn = QPushButton("✕ Remove Selected Process")
        remove_proc_btn.clicked.connect(self._remove_selected_process)
        proc_v.addWidget(remove_proc_btn)

        proc_group.setLayout(proc_v)
        main_layout.addWidget(proc_group)

        # ── Navigation ─────────────────────────────────────────────────
        main_layout.addStretch()

        nav_row = QHBoxLayout()

        self.start_btn = QPushButton("▶  Start Simulation")
        self.start_btn.setMinimumHeight(38)
        self.start_btn.clicked.connect(self._start_simulation)
        nav_row.addWidget(self.start_btn)

        self.resume_btn = QPushButton("↩  Return to Simulation")
        self.resume_btn.setMinimumHeight(38)
        self.resume_btn.clicked.connect(self._resume_simulation)
        self.resume_btn.setVisible(False)        # hidden until sim starts
        nav_row.addWidget(self.resume_btn)

        self.reset_btn = QPushButton("🔄 Reset")
        self.reset_btn.setMinimumHeight(38)
        self.reset_btn.setStyleSheet(
            "QPushButton { background-color: #E74C3C; }"
            "QPushButton:hover { background-color: #C0392B; }"
        )
        self.reset_btn.clicked.connect(self._reset_simulation)
        self.reset_btn.setVisible(False)
        nav_row.addWidget(self.reset_btn)

        main_layout.addLayout(nav_row)

        # Temp storage for the process currently being built
        self._current_process_segments: list[Segment] = []

        self.stacked_widget.addWidget(self.input_page)

    # ── Slot helpers for input page ────────────────────────────────────

    def _save_hole_input(self):
        start_text = self.hole_start_input.text().strip()
        size_text  = self.hole_size_input.text().strip()

        if not start_text or not size_text:
            QMessageBox.warning(self, "Input Error", "Please fill both Start Address and Size for the hole.")
            return
        try:
            start = int(start_text)
            size  = int(size_text)
            if size <= 0 or start < 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Start Address and Size must be positive integers.")
            return

        self.pending_holes.append((start, size))
        self.holes_list_widget.addItem(f"Hole → start={start}, size={size}")
        self.hole_start_input.clear()
        self.hole_size_input.clear()

    def _remove_selected_hole(self):
        row = self.holes_list_widget.currentRow()
        if row >= 0:
            self.holes_list_widget.takeItem(row)
            self.pending_holes.pop(row)

    def _add_segment_to_current_process(self):
        name = self.seg_name_input.text().strip()
        size_text = self.seg_size_input.text().strip()

        if not name or not size_text:
            QMessageBox.warning(self, "Input Error", "Please enter both a segment name and size.")
            return
        try:
            size = int(size_text)
            if size <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Segment size must be a positive integer.")
            return

        seg = Segment(name=name, size=size)
        self._current_process_segments.append(seg)
        self.current_segments_list.addItem(f"  {name}: {size}")
        self.seg_name_input.clear()
        self.seg_size_input.clear()

    def _confirm_process(self):
        if not self._current_process_segments:
            QMessageBox.warning(self, "Input Error", "Add at least one segment before confirming a process.")
            return

        process = Process(process_id=str(self.next_process_id))
        process.segments = list(self._current_process_segments)
        self.pending_processes.append(process)

        seg_summary = ", ".join(f"{s.name}({s.size})" for s in process.segments)
        self.confirmed_processes_list.addItem(f"P{process.process_id}: {seg_summary}")

        # Reset for next process
        self.next_process_id += 1
        self.pid_label.setText(f"Process ID: P{self.next_process_id}")
        self._current_process_segments = []
        self.current_segments_list.clear()

    def _discard_current_process(self):
        self._current_process_segments = []
        self.current_segments_list.clear()

    def _remove_selected_process(self):
        """Remove a confirmed process from the pending list."""
        row = self.confirmed_processes_list.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Selection Error", "Please select a process to remove.")
            return
        self.confirmed_processes_list.takeItem(row)
        self.pending_processes.pop(row)

    def _start_simulation(self):
        """Initialize memory manager and switch to simulation page."""
        if self.simulation_started:
            # Simulation already running — don't reinitialize
            self.stacked_widget.setCurrentIndex(1)
            self._refresh_simulation_page()
            return

        mem_text = self.total_mem_input.text().strip()
        if not mem_text:
            QMessageBox.warning(self, "Input Error", "Please enter total memory size.")
            return
        try:
            total_mem = int(mem_text)
            if total_mem <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Total memory size must be a positive integer.")
            return

        self.memory_manager = MemoryManager(total_memory_size=total_mem)

        if self.pending_holes:
            self.memory_manager.hole_table = [
                Hole(starting_address=s, size=z) for s, z in self.pending_holes
            ]

        self.selected_algo = self.algo_dropdown.currentText()
        self.simulation_started = True

        # Disable setup fields so they can't be changed mid-sim
        self.total_mem_input.setEnabled(False)
        self.algo_dropdown.setEnabled(False)
        self.hole_start_input.setEnabled(False)
        self.hole_size_input.setEnabled(False)

        # Show resume / reset buttons, hide start
        self.start_btn.setVisible(False)
        self.resume_btn.setVisible(True)
        self.reset_btn.setVisible(True)

        self.stacked_widget.setCurrentIndex(1)
        self._refresh_simulation_page()

    def _resume_simulation(self):
        """Return to simulation page without reinitializing."""
        self.stacked_widget.setCurrentIndex(1)
        self._refresh_simulation_page()

    def _reset_simulation(self):
        """Fully reset the simulation so the user can start over."""
        reply = QMessageBox.question(
            self, "Reset Simulation",
            "This will discard the current simulation. Are you sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.memory_manager = None
        self.simulation_started = False

        # Re-enable setup fields
        self.total_mem_input.setEnabled(True)
        self.algo_dropdown.setEnabled(True)
        self.hole_start_input.setEnabled(True)
        self.hole_size_input.setEnabled(True)

        # Show start, hide resume/reset
        self.start_btn.setVisible(True)
        self.resume_btn.setVisible(False)
        self.reset_btn.setVisible(False)

    # ══════════════════════════════════════════════════════════════════
    #  PAGE 1 – SIMULATION PAGE
    # ══════════════════════════════════════════════════════════════════

    def _setup_simulation_page(self):
        self.sim_page = QWidget()
        sim_layout = QVBoxLayout(self.sim_page)
        sim_layout.setSpacing(10)
        sim_layout.setContentsMargins(20, 16, 20, 16)

        # Title row
        title_row = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.setStyleSheet(HOVER_ONLY_BUTTON_STYLE)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        title_row.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        self.sim_title = QLabel("Memory Map")
        self.sim_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_row.addWidget(self.sim_title, alignment=Qt.AlignmentFlag.AlignCenter)
        title_row.addStretch()

        sim_layout.addLayout(title_row)

        content_row = QHBoxLayout()

        # ── Left panel (scroll) ───────────────────────────────────────
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setMaximumWidth(340)
        left_scroll.setStyleSheet("QScrollArea { border: none; }")

        left_container = QWidget()
        left_panel = QVBoxLayout(left_container)
        left_panel.setSpacing(8)

        # ── Process Queue ─────────────────────────────────────────────
        queue_group = QGroupBox("Process Queue")
        queue_v = QVBoxLayout()
        self.process_queue_list = QListWidget()
        self.process_queue_list.setMaximumHeight(120)
        allocate_btn = QPushButton("▶ Allocate Next Process")
        allocate_btn.clicked.connect(self._allocate_next_process)
        queue_v.addWidget(self.process_queue_list)
        queue_v.addWidget(allocate_btn)
        queue_group.setLayout(queue_v)
        left_panel.addWidget(queue_group)

        # ── Add Process Mid-Simulation ────────────────────────────────
        add_proc_group = QGroupBox("➕ Add New Process")
        add_proc_v = QVBoxLayout()
        add_proc_v.setSpacing(6)

        self.sim_pid_label = QLabel("Next ID: —")
        self.sim_pid_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        add_proc_v.addWidget(self.sim_pid_label)

        sim_seg_row = QHBoxLayout()
        self.sim_seg_name_input = QLineEdit()
        self.sim_seg_name_input.setPlaceholderText("Seg name")
        self.sim_seg_size_input = QLineEdit()
        self.sim_seg_size_input.setPlaceholderText("Size")
        sim_add_seg_btn = QPushButton("＋")
        sim_add_seg_btn.setFixedWidth(36)
        sim_add_seg_btn.clicked.connect(self._sim_add_segment)
        sim_seg_row.addWidget(self.sim_seg_name_input)
        sim_seg_row.addWidget(self.sim_seg_size_input)
        sim_seg_row.addWidget(sim_add_seg_btn)
        add_proc_v.addLayout(sim_seg_row)

        self.sim_current_segs_list = QListWidget()
        self.sim_current_segs_list.setMaximumHeight(70)
        add_proc_v.addWidget(self.sim_current_segs_list)

        sim_proc_btns = QHBoxLayout()
        sim_confirm_btn = QPushButton("✔ Add to Queue")
        sim_confirm_btn.clicked.connect(self._sim_confirm_process)
        sim_discard_btn = QPushButton("✕ Clear")
        sim_discard_btn.clicked.connect(self._sim_discard_process)
        sim_proc_btns.addWidget(sim_confirm_btn)
        sim_proc_btns.addWidget(sim_discard_btn)
        add_proc_v.addLayout(sim_proc_btns)

        add_proc_group.setLayout(add_proc_v)
        left_panel.addWidget(add_proc_group)

        # temp storage for segments being built in simulation page
        self._sim_current_segments: list[Segment] = []

        # ── Deallocation ──────────────────────────────────────────────
        dealloc_group = QGroupBox("Deallocate Process")
        dealloc_v = QVBoxLayout()
        self.dealloc_combo = QComboBox()
        dealloc_btn = QPushButton("✕ Deallocate")
        dealloc_btn.clicked.connect(self._deallocate_process)
        dealloc_v.addWidget(self.dealloc_combo)
        dealloc_v.addWidget(dealloc_btn)
        dealloc_group.setLayout(dealloc_v)
        left_panel.addWidget(dealloc_group)

        # ── Segment Tables ────────────────────────────────────────────
        seg_table_group = QGroupBox("Segment Tables")
        seg_table_v = QVBoxLayout()
        self.seg_table_list = QListWidget()
        seg_table_v.addWidget(self.seg_table_list)
        seg_table_group.setLayout(seg_table_v)
        left_panel.addWidget(seg_table_group)

        left_panel.addStretch()
        left_scroll.setWidget(left_container)
        content_row.addWidget(left_scroll)

        # ── Right panel – memory canvas (visual map) ──────────────────
        right_panel = QVBoxLayout()
        map_group = QGroupBox("Memory Layout")
        map_v = QVBoxLayout()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        self.memory_canvas = MemoryMapCanvas()
        scroll.setWidget(self.memory_canvas)

        map_v.addWidget(scroll)
        map_group.setLayout(map_v)
        right_panel.addWidget(map_group)

        # Holes / allocated tables below map
        tables_row = QHBoxLayout()

        holes_tbl_group = QGroupBox("Free Holes Table")
        holes_tbl_v = QVBoxLayout()
        self.holes_table_list = QListWidget()
        holes_tbl_v.addWidget(self.holes_table_list)
        holes_tbl_group.setLayout(holes_tbl_v)

        alloc_tbl_group = QGroupBox("Allocated Partitions Table")
        alloc_tbl_v = QVBoxLayout()
        self.alloc_table_list = QListWidget()
        alloc_tbl_v.addWidget(self.alloc_table_list)
        alloc_tbl_group.setLayout(alloc_tbl_v)

        tables_row.addWidget(holes_tbl_group)
        tables_row.addWidget(alloc_tbl_group)
        right_panel.addLayout(tables_row)

        content_row.addLayout(right_panel)
        sim_layout.addLayout(content_row)

        # Status bar
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sim_layout.addWidget(self.status_label)

        self.stacked_widget.addWidget(self.sim_page)

    # ── Mid-simulation process creation helpers ───────────────────────

    def _sim_add_segment(self):
        name = self.sim_seg_name_input.text().strip()
        size_text = self.sim_seg_size_input.text().strip()

        if not name or not size_text:
            QMessageBox.warning(self, "Input Error", "Enter both segment name and size.")
            return
        try:
            size = int(size_text)
            if size <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Segment size must be a positive integer.")
            return

        seg = Segment(name=name, size=size)
        self._sim_current_segments.append(seg)
        self.sim_current_segs_list.addItem(f"  {name}: {size}")
        self.sim_seg_name_input.clear()
        self.sim_seg_size_input.clear()

    def _sim_confirm_process(self):
        if not self._sim_current_segments:
            QMessageBox.warning(self, "Input Error", "Add at least one segment first.")
            return

        process = Process(process_id=str(self.next_process_id))
        process.segments = list(self._sim_current_segments)
        self.pending_processes.append(process)

        # Also update the input-page list so it stays in sync
        seg_summary = ", ".join(f"{s.name}({s.size})" for s in process.segments)
        self.confirmed_processes_list.addItem(f"P{process.process_id}: {seg_summary}")

        self.next_process_id += 1
        self.pid_label.setText(f"Process ID: P{self.next_process_id}")
        self._sim_current_segments = []
        self.sim_current_segs_list.clear()

        self.status_label.setStyleSheet("color: #2D8CFF;")
        self.status_label.setText(f"✚ P{process.process_id} added to queue.")
        self._refresh_simulation_page()

    def _sim_discard_process(self):
        self._sim_current_segments = []
        self.sim_current_segs_list.clear()

    # ── Slot helpers for simulation page ──────────────────────────────

    def _refresh_simulation_page(self):
        if self.memory_manager is None:
            return

        self.sim_title.setText(
            f"Memory Map  —  {self.memory_manager.total_memory_size} K  [{self.selected_algo}]"
        )

        # Update the "Next ID" label on the sim add-process panel
        self.sim_pid_label.setText(f"Next ID: P{self.next_process_id}")

        self.process_queue_list.clear()
        for proc in self.pending_processes:
            seg_summary = ", ".join(f"{s.name}({s.size})" for s in proc.segments)
            self.process_queue_list.addItem(f"P{proc.process_id}: {seg_summary}")

        self.dealloc_combo.clear()
        for pid in self.memory_manager.active_processes:
            self.dealloc_combo.addItem(f"P{pid}", pid)

        self.holes_table_list.clear()
        for h in self.memory_manager.hole_table:
            self.holes_table_list.addItem(
                f"  start={h.starting_address}  size={h.size}  "
                f"end={h.starting_address + h.size - 1}"
            )

        self.alloc_table_list.clear()
        for seg in self.memory_manager.allocated_table:
            owner = "?"
            for pid, proc in self.memory_manager.active_processes.items():
                if seg in proc.segments:
                    owner = f"P{pid}"
                    break
            self.alloc_table_list.addItem(
                f"  [{owner}] {seg.name}  base={seg.allocated_address}  limit={seg.size}"
            )

        self.seg_table_list.clear()
        for pid, proc in self.memory_manager.active_processes.items():
            self.seg_table_list.addItem(f"── P{pid} ──────────────────")
            for i, seg in enumerate(proc.segments):
                self.seg_table_list.addItem(
                    f"  [{i}] {seg.name}  base={seg.allocated_address}  limit={seg.size}"
                )

        # Update the visual canvas
        self.memory_canvas.update_map(self.memory_manager)

    def _allocate_next_process(self):
        if not self.pending_processes:
            QMessageBox.information(self, "Done", "No more processes in the queue.")
            return

        process = self.pending_processes[0]

        if self.selected_algo == "First-Fit":
            success = self.memory_manager.allocate_first_fit(process)
        else:
            success = self.memory_manager.allocate_best_fit(process)

        if success:
            self.pending_processes.pop(0)
            self.status_label.setStyleSheet("color: green;")
            self.status_label.setText(f"✔ P{process.process_id} allocated successfully.")
        else:
            self.pending_processes.pop(0)
            self.status_label.setStyleSheet("color: red;")
            self.status_label.setText(
                f"✘ P{process.process_id} could NOT be allocated — "
                f"one or more segments don't fit in any available hole."
            )

        self._refresh_simulation_page()

    def _deallocate_process(self):
        if self.dealloc_combo.count() == 0:
            QMessageBox.information(self, "Info", "No active processes to deallocate.")
            return

        pid = self.dealloc_combo.currentData()
        success = self.memory_manager.deallocate_process(pid)

        if success:
            self.status_label.setStyleSheet("color: green;")
            self.status_label.setText(f"✔ P{pid} deallocated. Memory holes merged where possible.")
        else:
            self.status_label.setStyleSheet("color: red;")
            self.status_label.setText(f"✘ Could not deallocate P{pid}.")

        self._refresh_simulation_page()