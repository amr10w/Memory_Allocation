from core.memory_models import Hole, Segment, Process
from copy import deepcopy


class MemoryManager():
    def __init__(self, total_memory_size: int):
        self.total_memory_size = total_memory_size

        self.hole_table = [Hole(0, self.total_memory_size)]
        self.allocated_table = []
        self.active_processes = {}

    def allocate_first_fit(self, process: Process) -> bool:
        # Only deepcopy holes (they get mutated in-place).
        # For allocated_table we just track how many entries existed
        # so we can truncate on rollback — this preserves the original
        # segment object references that active_processes also holds.
        backup_hole = deepcopy(self.hole_table)
        alloc_snapshot_len = len(self.allocated_table)

        success = True
        for segment in process.segments:
            sorted_holes = sorted(self.hole_table, key=lambda h: h.starting_address)
            placed = False
            for hole in sorted_holes:
                if segment.size <= hole.size:
                    segment.allocated_address = hole.starting_address
                    if segment.size == hole.size:
                        self.hole_table.remove(hole)
                    else:
                        hole.starting_address += segment.size
                        hole.size -= segment.size
                    self.allocated_table.append(segment)
                    placed = True
                    break
            if not placed:
                success = False
                break

        if not success:
            # Rollback: truncate allocated_table, restore holes, clear addresses
            self.allocated_table = self.allocated_table[:alloc_snapshot_len]
            self.hole_table = backup_hole
            for segment in process.segments:
                segment.allocated_address = None
            return False
        else:
            self.active_processes[process.process_id] = process
            return True

    def allocate_best_fit(self, process: Process) -> bool:
        backup_hole = deepcopy(self.hole_table)
        alloc_snapshot_len = len(self.allocated_table)

        success = True
        for segment in process.segments:
            suitable_holes = sorted(
                [h for h in self.hole_table if h.size >= segment.size],
                key=lambda h: h.size,
            )
            if len(suitable_holes) == 0:
                success = False
                break
            best_hole = suitable_holes[0]
            segment.allocated_address = best_hole.starting_address

            if segment.size == best_hole.size:
                self.hole_table.remove(best_hole)
            else:
                best_hole.starting_address += segment.size
                best_hole.size -= segment.size
            self.allocated_table.append(segment)

        if not success:
            self.allocated_table = self.allocated_table[:alloc_snapshot_len]
            self.hole_table = backup_hole
            for segment in process.segments:
                segment.allocated_address = None
            return False
        else:
            self.active_processes[process.process_id] = process
            return True

    def deallocate_process(self, process_id: int) -> bool:

        if process_id not in self.active_processes:
            return False

        process = self.active_processes[process_id]

        for segment in process.segments:
            if segment in self.allocated_table:
                self.allocated_table.remove(segment)

            new_hole = Hole(starting_address=segment.allocated_address, size=segment.size)
            self.hole_table.append(new_hole)
            segment.allocated_address = None

        self.hole_table.sort(key=lambda h: h.starting_address)

        merged_holes = []
        for current_hole in self.hole_table:
            if len(merged_holes) == 0:
                merged_holes.append(current_hole)
            else:
                last_hole = merged_holes[-1]
                if last_hole.starting_address + last_hole.size == current_hole.starting_address:
                    last_hole.size += current_hole.size
                else:
                    merged_holes.append(current_hole)

        self.hole_table = merged_holes
        del self.active_processes[process_id]
        return True