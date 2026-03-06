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
    
    def connect_pcs(self):
        device_type = self.get_user_device_type()
        
        for f in range(1, self.floors + 1):
            for r in range(1, self.rooms + 1):
                access = f"access_switch_f{f}_r{r}"

                for u in range(1, self.users + 1):
                    pc = f"{device_type}_f{f}_r{r}_u{u}"
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

        coverage_area = math.pi * radius * radius
        floor_area = self.width_m * self.width_m

        ap_by_area = math.ceil(floor_area / coverage_area)

        total_users_floor = self.rooms * self.users
        ap_by_users = math.ceil(total_users_floor / users_per_ap)

        aps_needed = max(ap_by_area, ap_by_users)

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
            if self.floors >= 3:
                self.connect(dist, "backup_core_router")

    # --------------------------------------------------
    # RULE 5
    # SERVERS → CORE
    # --------------------------------------------------

    def connect_servers(self):

        self.connect("dhcp_server", "core_router_1")
        self.connect("dns_server", "core_router_1")
        if self.floors >= 3:
            self.connect("dns_server", "backup_core_router")
        if self.floors >= 3:
            self.connect("dhcp_server", "backup_core_router")

    # --------------------------------------------------
    # RULE 6
    # CORE → INTERNET / FIREWALL
    # --------------------------------------------------

    def connect_internet(self):

        if self.firewall_enabled:

            self.connect("core_router_1", "firewall_1")
            self.connect("backup_core_router", "firewall_1")
            self.connect("firewall_1", "internet_cloud")

        else:

            self.connect("core_router_1", "internet_cloud")
            self.connect("backup_core_router", "internet_cloud")

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