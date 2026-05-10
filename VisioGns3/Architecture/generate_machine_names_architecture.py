import math

class ArchitectureEngine:
    def __init__(self, floors, rooms, users, width, unit, building_type, firewall_enabled):
        self.floors = floors
        self.rooms = rooms
        self.users = users
        self.width = width
        self.unit = unit
        self.building_type = building_type
        self.firewall_enabled = firewall_enabled
        self.machines = []
        self.convert_width()

    # --------------------------------------------------
    # UNIT CONVERSION
    # --------------------------------------------------

    def convert_width(self):
        if self.unit == "Feet":
            self.width_m = self.width * 0.3048
        elif self.unit == "Meters":
            self.width_m = self.width
        elif self.unit == "Square Meters":
            self.width_m = math.sqrt(self.width)
        else:
            self.width_m = self.width

    # --------------------------------------------------
    # RULE 1
    # CORE NETWORK DEVICES
    # --------------------------------------------------

    def add_core_devices(self):
        """
        Every enterprise topology requires
        core connectivity + basic network services
        """
        self.machines.append("core_router_1")
        if self.floors >= 3:
            self.machines.append("backup_core_router")
        self.machines.append("dhcp_server")
        self.machines.append("dns_server")
        self.machines.append("internet_cloud")
        if self.firewall_enabled:
            self.machines.append("firewall_1")

    def add_servers(self):
        if not self.servers:
            return
        self.machines.append("server_switch")
        for server in self.servers:
            self.machines.append(server)

    # --------------------------------------------------
    # RULE 2
    # DISTRIBUTION SWITCH PER FLOOR
    # --------------------------------------------------

    def add_distribution_switches(self):
        """
        RULE:
        Each floor requires one distribution switch
        that aggregates traffic from access switches.
        """
        for floor in range(1, self.floors + 1):
            name = f"dist_switch_f{floor}"
            self.machines.append(name)

    # --------------------------------------------------
    # RULE 3
    # ACCESS SWITCH PER ROOM
    # --------------------------------------------------

    def add_access_switches(self):
        """
        RULE:
        Each room has one access switch.
        Naming Convention:
        access_switch_f{floor}_r{room}
        """
        for floor in range(1, self.floors + 1):
            for room in range(1, self.rooms + 1):
                name = f"access_switch_f{floor}_r{room}"
                self.machines.append(name)

    # --------------------------------------------------
    # RULE 4
    # PCS FOR USERS
    # --------------------------------------------------

    def get_user_device_type(self):
        if self.building_type == "Office":
            return "pc"
        elif self.building_type == "School / University":
            return "lab_pc"
        elif self.building_type == "Hotel":
            return "laptop"
        elif self.building_type == "Hospital":
            return "medical_pc"
        return "pc"

    def add_user_pcs(self):
        """
        RULE:
        Each user in a room gets one PC.
        Naming Convention:
        pc_f{floor}_r{room}_u{user}
        """
        device_type = self.get_user_device_type()

        for floor in range(1, self.floors + 1):
            for room in range(1, self.rooms + 1):
                for user in range(1, self.users + 1):
                    name = f"{device_type}_f{floor}_r{room}_u{user}"
                    self.machines.append(name)

    # --------------------------------------------------
    # RULE 5
    # ACCESS POINT CALCULATION
    # --------------------------------------------------

    def calculate_access_points(self):
        """
        WiFi AP estimation inspired by Ekahau coverage logic.
        Coverage radius depends on building type.
        """
        if self.building_type == "Office":
            radius = 12
            users_per_ap = 25
        elif self.building_type == "Hospital":
            radius = 10
            users_per_ap = 20
        elif self.building_type == "School / University":
            radius = 15
            users_per_ap = 30
        elif self.building_type == "Hotel":
            radius = 10
            users_per_ap = 20
        else:
            radius = 12
            users_per_ap = 25

        coverage_area = math.pi * radius * radius
        floor_area = self.width_m * self.width_m

        ap_by_area = math.ceil(floor_area / coverage_area)

        total_users_floor = self.rooms * self.users
        ap_by_users = math.ceil(total_users_floor / users_per_ap)

        aps_needed = max(ap_by_area, ap_by_users)

        if aps_needed < 1:
            aps_needed = 1

        for floor in range(1, self.floors + 1):
            for ap in range(1, aps_needed + 1):
                name = f"ap_f{floor}_{ap}"
                self.machines.append(name)

    # --------------------------------------------------
    # AP PLACEMENT — GRID COMPUTATION
    # --------------------------------------------------

    def _compute_ap_grid(self):
        """
        Compute cols x rows grid so every cell dimension <= AP diameter,
        guaranteeing full floor coverage with no dead zones.

        Also accounts for user capacity: if more APs are needed to serve
        all users than coverage requires, the grid is expanded.
        """
        if self.building_type == "Office":
            radius = 12
            users_per_ap = 25
        elif self.building_type == "Hospital":
            radius = 10
            users_per_ap = 20
        elif self.building_type == "School / University":
            radius = 15
            users_per_ap = 30
        elif self.building_type == "Hotel":
            radius = 10
            users_per_ap = 20
        else:
            radius = 12
            users_per_ap = 25

        diameter = 2 * radius

        # Minimum grid so every cell side <= diameter (guarantees full coverage)
        cols = max(1, math.ceil(self.width_m / diameter))
        rows = max(1, math.ceil(self.width_m / diameter))

        # Expand grid if user capacity demands more APs
        total_users_floor = self.rooms * self.users
        ap_by_users = math.ceil(total_users_floor / users_per_ap)
        while cols * rows < ap_by_users:
            if cols <= rows:
                cols += 1
            else:
                rows += 1

        return cols, rows, cols * rows, radius

    # --------------------------------------------------
    # AP PLACEMENT — HUMAN-READABLE REPORT
    # --------------------------------------------------

    def _format_original_input(self):
        """
        Return lines explaining what the user entered and how it converts
        to metres, so the report is self-explanatory regardless of unit.
        """
        w  = self.width
        u  = self.unit
        wm = self.width_m

        if u == "Square Meters":
            return [
                f"  Width entered    : {w} Square Meters",
                f"  Interpretation   : floor area = {w} sq m",
                f"  Side length      : sqrt({w}) = {wm:.4f} m",
            ]
        elif u == "Meters":
            return [
                f"  Width entered    : {w} Meters",
                f"  Interpretation   : building width (one side) = {w} m",
                f"  Side length      : {wm:.4f} m  (no conversion needed)",
            ]
        elif u == "Feet":
            return [
                f"  Width entered    : {w} Feet",
                f"  Interpretation   : building width (one side) = {w} ft",
                f"  Conversion       : {w} ft  x  0.3048  =  {wm:.4f} m",
            ]
        else:
            return [f"  Width entered    : {w} {u}  ->  {wm:.4f} m"]

    def generate_ap_placement_file(self, output_path):
        """
        Write a human-readable text file describing the exact X/Y placement
        of every access point on every floor.

        How the grid works
        ------------------
        The floor is treated as a square of side width_m x width_m.
        APs are arranged in a cols x rows grid where every cell side
        is <= the AP diameter, so the signal reaches every wall of
        each cell with no dead zones.
        Each AP sits at the centre of its cell:
            X = cell_width  * (column_index + 0.5)
            Y = cell_height * (row_index    + 0.5)
        Coordinates are measured from the bottom-left corner (0, 0).
        """
        cols, rows, aps_needed, radius = self._compute_ap_grid()
        diameter = radius * 2
        cell_w = self.width_m / cols
        cell_h = self.width_m / rows

        lines = []
        lines.append("=" * 68)
        lines.append("  ACCESS POINT PLACEMENT PLAN")
        lines.append("=" * 68)

        # ── User input block ──────────────────────────────────────────────
        lines.append("")
        lines.append("  USER INPUT")
        lines.append("  " + "-" * 54)
        lines.append(f"  Building type    : {self.building_type}")
        lines.extend(self._format_original_input())
        lines.append(f"  Floors           : {self.floors}")
        lines.append(f"  Rooms per floor  : {self.rooms}")
        lines.append(f"  Users per room   : {self.users}")

        # ── Converted floor dimensions ────────────────────────────────────
        lines.append("")
        lines.append("  CONVERTED FLOOR DIMENSIONS")
        lines.append("  " + "-" * 54)
        lines.append(f"  Floor side       : {self.width_m:.4f} m")
        lines.append(
            f"  Floor area       : {self.width_m:.4f} m  x  {self.width_m:.4f} m"
            f"  =  {self.width_m ** 2:.2f} sq m"
        )

        # ── AP specification ──────────────────────────────────────────────
        lines.append("")
        lines.append("  ACCESS POINT SPECIFICATION")
        lines.append("  " + "-" * 54)
        lines.append(f"  Coverage radius  : {radius} m")
        lines.append(
            f"  Coverage diam.   : {diameter} m"
            f"  (signal spans {diameter} m from wall to wall)"
        )
        lines.append(
            f"  Grid layout      : {cols} column(s)  x  {rows} row(s)"
            f"  =  {aps_needed} AP(s) per floor"
        )
        lines.append(
            f"  Cell width       : {self.width_m:.4f} / {cols} = {cell_w:.4f} m"
        )
        lines.append(
            f"  Cell height      : {self.width_m:.4f} / {rows} = {cell_h:.4f} m"
        )

        # ── Coverage proof ────────────────────────────────────────────────
        lines.append("")
        lines.append(
            "  COVERAGE PROOF"
            "  (cell side <= AP diameter guarantees full coverage)"
        )
        lines.append("  " + "-" * 54)
        w_ok = "OK  full coverage" if cell_w <= diameter else "FAIL  gap exists"
        h_ok = "OK  full coverage" if cell_h <= diameter else "FAIL  gap exists"
        lines.append(
            f"  Horizontal : {cell_w:.4f} m  <=  {diameter} m ?  {w_ok}"
        )
        lines.append(
            f"  Vertical   : {cell_h:.4f} m  <=  {diameter} m ?  {h_ok}"
        )

        # ── Coordinate key ────────────────────────────────────────────────
        lines.append("")
        lines.append("  COORDINATE SYSTEM")
        lines.append("  " + "-" * 54)
        lines.append("  Origin (0, 0) = bottom-left corner of the floor")
        lines.append("  X = horizontal distance from West wall  (metres)")
        lines.append("  Y = vertical   distance from South wall (metres)")
        lines.append(f"  Floor spans   X : 0  ->  {self.width_m:.2f} m")
        lines.append(f"                Y : 0  ->  {self.width_m:.2f} m")
        lines.append("")
        lines.append("=" * 68)

        # ── Per-floor AP tables ───────────────────────────────────────────
        for floor in range(1, self.floors + 1):
            lines.append(f"\n  FLOOR {floor}")
            lines.append("  " + "-" * 62)
            lines.append(
                f"  {'AP Name':<24}  {'Col':>4}  {'Row':>4}"
                f"  {'X (m)':>8}  {'Y (m)':>8}  {'Radius':>7}"
            )
            lines.append("  " + "-" * 62)

            ap_idx = 1
            for row in range(rows):
                for col in range(cols):
                    if ap_idx > aps_needed:
                        break
                    x = cell_w * (col + 0.5)
                    y = cell_h * (row + 0.5)
                    ap_name = f"ap_f{floor}_{ap_idx}"
                    lines.append(
                        f"  {ap_name:<24}  {col+1:>4}  {row+1:>4}"
                        f"  {x:>8.2f}  {y:>8.2f}  {radius:>5} m"
                    )
                    ap_idx += 1
            lines.append("")

        lines.append("=" * 68)
        lines.append("  END OF PLACEMENT PLAN")
        lines.append("=" * 68)

        with open(output_path, "w") as f:
            f.write("\n".join(lines))

        return output_path

    # --------------------------------------------------
    # ENGINE EXECUTION
    # --------------------------------------------------

    def run(self, output_path):
        self.add_core_devices()
        self.add_distribution_switches()
        self.add_access_switches()
        self.add_user_pcs()
        self.calculate_access_points()
        self.write_file(output_path)
        return self.machines

    # --------------------------------------------------
    # WRITE machines.txt
    # --------------------------------------------------

    def write_file(self, output_path):
        with open(output_path, "w") as f:
            for device in self.machines:
                f.write(device + "\n")