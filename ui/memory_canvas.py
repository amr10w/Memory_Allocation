# ui/memory_canvas.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel
from PyQt6.QtCore import Qt


class MemoryMapCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.map_layout = QVBoxLayout(self)
        self.map_layout.setSpacing(0)
        self.map_layout.setContentsMargins(4, 4, 4, 4)

    def update_map(self, memory_manager):
        """Draws a vertical bar representing the ENTIRE memory address range."""
        # Clear old widgets
        while self.map_layout.count():
            child = self.map_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if memory_manager is None:
            return

        total = memory_manager.total_memory_size
        SCALE = 400  # total pixel height for entire memory

        # ── Build list of KNOWN blocks (allocated segments + holes) ────
        known_blocks = []

        for seg in memory_manager.allocated_table:
            owner = "?"
            for pid, proc in memory_manager.active_processes.items():
                if seg in proc.segments:
                    owner = f"P{pid}"
                    break
            known_blocks.append({
                "start": seg.allocated_address,
                "size":  seg.size,
                "label": f"{owner} · {seg.name}",
                "type":  "allocated",
                "owner": owner,
            })

        for h in memory_manager.hole_table:
            known_blocks.append({
                "start": h.starting_address,
                "size":  h.size,
                "label": "FREE",
                "type":  "hole",
                "owner": None,
            })

        known_blocks.sort(key=lambda b: b["start"])

        # ── Fill gaps with OCCUPIED (OS / Reserved) blocks ─────────────
        all_blocks = []
        cursor = 0
        for block in known_blocks:
            if block["start"] > cursor:
                # There is a gap → occupied / reserved region
                gap_size = block["start"] - cursor
                all_blocks.append({
                    "start": cursor,
                    "size":  gap_size,
                    "label": "OCCUPIED",
                    "type":  "occupied",
                    "owner": None,
                })
            all_blocks.append(block)
            cursor = block["start"] + block["size"]

        # Trailing gap at the end of memory
        if cursor < total:
            all_blocks.append({
                "start": cursor,
                "size":  total - cursor,
                "label": "OCCUPIED",
                "type":  "occupied",
                "owner": None,
            })

        # ── Per-process colour palette ─────────────────────────────────
        pid_colors = [
            "#3A7BD5", "#E74C3C", "#27AE60", "#F39C12",
            "#8E44AD", "#16A085", "#D35400", "#2980B9",
        ]
        pid_color_map = {}
        for i, pid in enumerate(memory_manager.active_processes):
            pid_color_map[f"P{pid}"] = pid_colors[i % len(pid_colors)]

        # ── Style helper ──────────────────────────────────────────────
        def _style(block):
            btype = block["type"]
            if btype == "hole":
                return "#E8F5E9", "#388E3C"          # light green bg, dark green text
            elif btype == "occupied":
                return "#FFE0B2", "#E65100"           # orange bg, dark orange text
            else:  # allocated
                owner = block.get("owner")
                bg = pid_color_map.get(owner, "#4A90D9")
                return bg, "#FFFFFF"

        # ── Draw the rectangles ───────────────────────────────────────
        for block in all_blocks:
            frac = block["size"] / total
            height = max(28, int(frac * SCALE))

            bg_color, text_color = _style(block)

            frame = QFrame()
            frame.setFixedHeight(height)
            frame.setStyleSheet(
                f"background-color: {bg_color};"
                f"border: 1px solid #bbb;"
                f"border-radius: 3px;"
            )

            frame_layout = QHBoxLayout(frame)
            frame_layout.setContentsMargins(8, 0, 8, 0)

            addr_label = QLabel(str(block["start"]))
            addr_label.setStyleSheet(
                f"color: {text_color}; font-size: 10px; font-weight: bold; border: none;"
            )
            addr_label.setFixedWidth(50)

            name_label = QLabel(f"{block['label']}  ({block['size']})")
            name_label.setStyleSheet(
                f"color: {text_color}; font-size: 11px; font-weight: bold; border: none;"
            )
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            end_addr = block["start"] + block["size"] - 1
            end_label = QLabel(str(end_addr))
            end_label.setStyleSheet(
                f"color: {text_color}; font-size: 10px; font-weight: bold; border: none;"
            )
            end_label.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            end_label.setFixedWidth(50)

            frame_layout.addWidget(addr_label)
            frame_layout.addWidget(name_label)
            frame_layout.addWidget(end_label)

            self.map_layout.addWidget(frame)

        self.map_layout.addStretch()