import json
import math

class ArchitectureConnections:

    def __init__(self, floors, rooms, users, width_m, building_type,
             firewall_enabled, servers=None,
             cost_priority="Medium",
             speed_priority="Medium",
             reliability_priority="Medium"):

            self.floors = floors
            self.rooms = rooms
            self.users = users
            self.width_m = width_m
            self.building_type = building_type
            self.firewall_enabled = firewall_enabled
            self.servers = servers or []

            self.cost_priority = cost_priority
            self.speed_priority = speed_priority
            self.reliability_priority = reliability_priority

            self.connections = []

            # determine topology once
            self.topology = self.choose_topology()

    def get_network_size(self):

        total_users = self.floors * self.rooms * self.users

        if total_users <= 50:
            return "small"

        elif total_users <= 200:
            return "medium"

        else:
            return "large"
    # --------------------------------------------------
    # Utility
    # --------------------------------------------------

    def connect(self, src, dst):
        self.connections.append({
            "from": src,
            "to": dst
        })
    def choose_topology(self):
        """
        Hybrid approach:
        - User priorities: cost, speed, reliability
        - Building type preferences
        - Network size preferences
        """
        network_size = self.get_network_size()
        score_map = {"Low": 1, "Medium": 2, "High": 3}

        # Convert user priorities to scores
        cost = score_map.get(self.cost_priority, 2)
        speed = score_map.get(self.speed_priority, 2)
        reliability = score_map.get(self.reliability_priority, 2)

        # Topology profiles
        profiles = {
            "bus": {"cost":3, "speed":1, "reliability":1},
            "star": {"cost":2, "speed":3, "reliability":2},
            "ring": {"cost":2, "speed":2, "reliability":2},
            "mesh": {"cost":1, "speed":3, "reliability":3},
            "hierarchical": {"cost":2, "speed":3, "reliability":3}
        }

        # Building type preferences
        # building_preferences = {
        #     "Hospital": ["mesh", "hierarchical"],
        #     "Office": ["star", "hierarchical"],
        #     "School / University": ["hierarchical", "star"],
        #     "Hotel": ["star", "ring"]
        # }

        # Network size preferences
        size_preferences = {
            "small": ["bus", "star", "ring", "hierarchical", "mesh"],
            "medium": ["star", "ring", "hierarchical", "mesh", "bus"],
            "large": ["hierarchical", "star", "ring", "bus"]
        }

        best_topology = None
        best_score = -999

        for topo, p in profiles.items():
            # 1. User priority match (higher is better)
            score = 10 - (abs(p["cost"] - cost) + abs(p["speed"] - speed) + abs(p["reliability"] - reliability))

            # 2. Building type preference bonus
            # if topo in building_preferences.get(self.building_type, []):
            #     score += 2

            # 3. Network size preference bonus
            if topo in size_preferences.get(network_size, []):
                score += 2

            # Choose the topology with the highest score
            if score >= best_score:
                best_score = score
                best_topology = topo

        return best_topology

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
        aps_needed = max(ap_by_area, ap_by_users, 1)

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

        if self.topology == "star" or self.topology == "hierarchical":

            for f in range(1, self.floors + 1):
                dist = f"dist_switch_f{f}"
                self.connect(dist, "core_router_1")

                if self.floors >= 3:
                    self.connect(dist, "backup_core_router")


        elif self.topology == "ring":

            prev = None
            first = None

            for f in range(1, self.floors + 1):
                dist = f"dist_switch_f{f}"

                # Ring connection
                if prev:
                    self.connect(prev, dist)

                if not first:
                    first = dist

                prev = dist

                # ALSO connect to core router
                self.connect(dist, "core_router_1")

                if self.floors >= 3:
                    self.connect(dist, "backup_core_router")

            if prev and first:
                self.connect(prev, first)


        elif self.topology == "mesh":

            switches = [f"dist_switch_f{f}" for f in range(1, self.floors + 1)]

            for i in range(len(switches)):
                for j in range(i+1, len(switches)):
                    self.connect(switches[i], switches[j])

            # ALSO connect each switch to core
            for sw in switches:
                self.connect(sw, "core_router_1")

                if self.floors >= 3:
                    self.connect(sw, "backup_core_router")


        elif self.topology == "bus":

            prev = None

            for f in range(1, self.floors + 1):
                dist = f"dist_switch_f{f}"

                # Bus connection
                if prev:
                    self.connect(prev, dist)

                prev = dist

                # ALSO connect to core router
                self.connect(dist, "core_router_1")

                if self.floors >= 3:
                    self.connect(dist, "backup_core_router")

    # --------------------------------------------------
    # RULE 5
    # SERVERS → SERVER SWITCH → CORE
    # --------------------------------------------------

    def connect_servers(self):
        if self.servers:
                # Always create server_switch if there are servers or DHCP/DNS
                self.connect("core_router_1", "server_switch")
                if self.floors >= 3:
                    self.connect("backup_core_router", "server_switch")

                # Connect additional servers if provided
                for s in self.servers:
                    self.connect("server_switch", s)

                # Always connect DHCP and DNS to server_switch
                self.connect("server_switch", "dhcp_server")
                self.connect("server_switch", "dns_server")

        else:
            # default DHCP/DNS
            self.connect("dhcp_server", "core_router_1")
            self.connect("dns_server", "core_router_1")
            if self.floors >= 3:
                self.connect("dns_server", "backup_core_router")
                self.connect("dhcp_server", "backup_core_router")

    # --------------------------------------------------
    # RULE 6
    # CORE → INTERNET / FIREWALL
    # --------------------------------------------------

    def connect_internet(self):
        if self.firewall_enabled:
            self.connect("core_router_1", "firewall_1")
            if self.floors >= 3:
                self.connect("backup_core_router", "firewall_1")
            self.connect("firewall_1", "internet_cloud")
        else:
            self.connect("core_router_1", "internet_cloud")
            if self.floors >= 3:
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

        print("Selected Topology:", self.topology)

        with open(output_path, "w") as f:
            json.dump(self.connections, f, indent=4)

        return self.connections