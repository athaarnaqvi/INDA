import json
import math


class ArchitectureConnections:

    def __init__(self, floors, rooms, users, width_m, building_type, firewall_enabled):
        self.floors = floors
        self.rooms = rooms
        self.users = users
        self.width_m = width_m
        self.building_type = building_type
        self.firewall_enabled = firewall_enabled

        self.connections = []

    # --------------------------------------------------
    # Utility
    # --------------------------------------------------

    def connect(self, src, dst):
        self.connections.append({
            "from": src,
            "to": dst
        })

    # --------------------------------------------------
    # RULE 1
    # PC → ACCESS SWITCH
    # --------------------------------------------------

    def connect_pcs(self):

        for f in range(1, self.floors + 1):
            for r in range(1, self.rooms + 1):
                access = f"access_switch_f{f}_r{r}"

                for u in range(1, self.users + 1):
                    pc = f"pc_f{f}_r{r}_u{u}"
                    self.connect(pc, access)

    # --------------------------------------------------
    # RULE 2
    # ACCESS SWITCH → DISTRIBUTION SWITCH
    # --------------------------------------------------

    def connect_access_switches(self):

        for f in range(1, self.floors + 1):
            dist = f"dist_switch_f{f}"

            for r in range(1, self.rooms + 1):
                access = f"access_switch_f{f}_r{r}"
                self.connect(access, dist)

    # --------------------------------------------------
    # RULE 3
    # ACCESS POINTS → DISTRIBUTION SWITCH
    # --------------------------------------------------

    def connect_access_points(self):

        if self.building_type == "Office":
            radius = 12
        elif self.building_type == "Hospital":
            radius = 10
        elif self.building_type == "School / University":
            radius = 15
        elif self.building_type == "Hotel":
            radius = 10
        else:
            radius = 12

        coverage_area = math.pi * radius * radius
        floor_area = self.width_m * self.width_m

        aps_needed = math.ceil(floor_area / coverage_area)
        if aps_needed < 1:
            aps_needed = 1

        for f in range(1, self.floors + 1):
            dist = f"dist_switch_f{f}"

            for ap in range(1, aps_needed + 1):
                ap_name = f"ap_f{f}_{ap}"
                self.connect(ap_name, dist)

    # --------------------------------------------------
    # RULE 4
    # DISTRIBUTION → CORE
    # --------------------------------------------------

    def connect_distribution_to_core(self):

        for f in range(1, self.floors + 1):
            dist = f"dist_switch_f{f}"
            self.connect(dist, "core_router_1")

    # --------------------------------------------------
    # RULE 5
    # SERVERS → CORE
    # --------------------------------------------------

    def connect_servers(self):

        self.connect("dhcp_server", "core_router_1")
        self.connect("dns_server", "core_router_1")

    # --------------------------------------------------
    # RULE 6
    # CORE → INTERNET / FIREWALL
    # --------------------------------------------------

    def connect_internet(self):

        if self.firewall_enabled:

            self.connect("core_router_1", "firewall_1")
            self.connect("firewall_1", "internet_cloud")

        else:

            self.connect("core_router_1", "internet_cloud")

    # --------------------------------------------------
    # RUN ENGINE
    # --------------------------------------------------

    def run(self, output_path):

        self.connect_pcs()
        self.connect_access_switches()
        self.connect_access_points()
        self.connect_distribution_to_core()
        self.connect_servers()
        self.connect_internet()

        with open(output_path, "w") as f:
            json.dump(self.connections, f, indent=4)

        return self.connections