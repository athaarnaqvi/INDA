import json
import math

# ---------------------------------------------------------------------------
# Topology pros / cons — shown to the user in the selection dialog
# ---------------------------------------------------------------------------
TOPOLOGY_PROS_CONS = {
    "bus": {
        "display_name": "Bus",
        "description": "All devices share a single backbone cable",
        "pros": [
            "Lowest hardware cost — no extra switches needed",
            "Simple to install and extend",
            "Works well for small, temporary networks",
        ],
        "cons": [
            "A single cable fault brings the entire network down",
            "Performance degrades as more devices are added",
            "Difficult to troubleshoot; no redundancy",
        ],
        "best_for": "Small offices, labs, low-budget setups",
        "icon": "🚌",
    },
    "star": {
        "display_name": "Star",
        "description": "All devices connect to a central switch/hub",
        "pros": [
            "Easy to add or remove devices without disruption",
            "A single device failure does not affect others",
            "Simple troubleshooting — isolate faults per port",
        ],
        "cons": [
            "Central switch is a single point of failure",
            "More cabling required than bus topology",
            "Performance limited by central switch capacity",
        ],
        "best_for": "Most offices, hotels, standard enterprise networks",
        "icon": "⭐",
    },
    "ring": {
        "display_name": "Ring",
        "description": "Devices form a closed loop; data travels in one direction",
        "pros": [
            "Predictable, consistent performance under load",
            "No network collisions — token-based access",
            "Equal bandwidth for all devices",
        ],
        "cons": [
            "One broken link can disrupt the whole network",
            "Adding or removing devices disrupts the ring",
            "Slower than star for small networks",
        ],
        "best_for": "Schools, campuses needing predictable throughput",
        "icon": "🔄",
    },
    "mesh": {
        "display_name": "Mesh",
        "description": "Every device connects to every other device",
        "pros": [
            "Maximum redundancy — multiple paths per connection",
            "Highest fault tolerance; no single point of failure",
            "Best performance for critical applications",
        ],
        "cons": [
            "Most expensive — cables and ports grow as n²",
            "Complex to configure and manage",
            "Overkill for small or medium networks",
        ],
        "best_for": "Hospitals, data centres, mission-critical environments",
        "icon": "🕸️",
    },
    "hierarchical": {
        "display_name": "Hierarchical",
        "description": "Three-tier design: core → distribution → access",
        "pros": [
            "Highly scalable — add floors/rooms without redesign",
            "Excellent performance through traffic segmentation",
            "Redundant core links available for large buildings",
        ],
        "cons": [
            "Higher hardware cost than star or ring",
            "More complex initial configuration",
            "Requires careful IP addressing and VLAN planning",
        ],
        "best_for": "Large offices, universities, multi-floor buildings",
        "icon": "🏗️",
    },
}


class ArchitectureConnections:

    def __init__(self, floors, rooms, users, width_m, building_type,
                 firewall_enabled, servers=None,
                 cost_priority="Medium",
                 speed_priority="High",
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

        # Compute top-2 topologies once; default active topology = #1
        self.top2 = self.choose_top2_topologies()
        self.topology = self.top2[0]["name"]      # active topology (changeable)

    # --------------------------------------------------
    # Network size helper
    # --------------------------------------------------

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
        self.connections.append({"from": src, "to": dst})

    # --------------------------------------------------
    # TOP-2 TOPOLOGY SELECTION
    # --------------------------------------------------

    def choose_top2_topologies(self):
        """
        Score all five topologies and return the top-2 as a list of dicts:
            [
              {
                "name":    "hierarchical",
                "score":   12,
                "rank":    1,
                "pros_cons": { ... }   ← from TOPOLOGY_PROS_CONS
              },
              { ... rank 2 ... }
            ]

        When two topologies tie, the one appearing earlier in the profile
        dict is ranked higher (stable sort preserves original order).
        """
        network_size = self.get_network_size()
        score_map = {"Low": 1, "Medium": 2, "High": 3}

        cost        = score_map.get(self.cost_priority, 2)
        speed       = score_map.get(self.speed_priority, 2)
        reliability = score_map.get(self.reliability_priority, 2)

        profiles = {
            "bus":          {"cost": 3, "speed": 1, "reliability": 1},
            "star":         {"cost": 2, "speed": 3, "reliability": 2},
            "ring":         {"cost": 2, "speed": 2, "reliability": 2},
            "mesh":         {"cost": 1, "speed": 3, "reliability": 3},
            "hierarchical": {"cost": 2, "speed": 3, "reliability": 3},
        }

        size_preferences = {
            "small":  ["bus", "star", "ring", "hierarchical", "mesh"],
            "medium": ["star", "ring", "hierarchical", "mesh", "bus"],
            "large":  ["hierarchical", "star", "ring", "bus"],
        }

        scored = []
        for topo, p in profiles.items():
            score = 10 - (
                abs(p["cost"]        - cost) +
                abs(p["speed"]       - speed) +
                abs(p["reliability"] - reliability)
            )
            if topo in size_preferences.get(network_size, []):
                score += 2
            scored.append((topo, score))

        # Sort descending by score (stable — ties keep original order)
        scored.sort(key=lambda x: x[1], reverse=True)

        result = []
        for rank, (topo_name, score) in enumerate(scored[:2], start=1):
            entry = {
                "name":      topo_name,
                "score":     score,
                "rank":      rank,
                "pros_cons": TOPOLOGY_PROS_CONS.get(topo_name, {}),
            }
            result.append(entry)

        return result

    # --------------------------------------------------
    # (kept for backward-compatibility — returns top-1)
    # --------------------------------------------------

    def choose_topology(self):
        return self.top2[0]["name"]

    # --------------------------------------------------
    # Switch the active topology and clear old connections
    # --------------------------------------------------

    def set_topology(self, topology_name: str):
        """Change the active topology before (re-)running connection generation."""
        if topology_name not in TOPOLOGY_PROS_CONS:
            raise ValueError(f"Unknown topology: {topology_name}")
        self.topology = topology_name
        self.connections = []   # clear any previously generated connections

    # --------------------------------------------------
    # RULE 1 — PC → ACCESS SWITCH
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
    # RULE 2 — ACCESS SWITCH → DISTRIBUTION SWITCH
    # --------------------------------------------------

    def connect_access_switches(self):
        for f in range(1, self.floors + 1):
            dist = f"dist_switch_f{f}"
            for r in range(1, self.rooms + 1):
                access = f"access_switch_f{f}_r{r}"
                self.connect(access, dist)

    # --------------------------------------------------
    # RULE 3 — ACCESS POINTS → DISTRIBUTION SWITCH
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
        else:
            radius = 12
            users_per_ap = 25

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
    # RULE 4 — DISTRIBUTION → CORE
    # --------------------------------------------------

    def connect_distribution_to_core(self):

        if self.topology in ("star", "hierarchical"):
            for f in range(1, self.floors + 1):
                dist = f"dist_switch_f{f}"
                self.connect(dist, "core_router_1")
                if self.floors >= 3:
                    self.connect(dist, "backup_core_router")

        elif self.topology == "ring":
            prev, first = None, None
            for f in range(1, self.floors + 1):
                dist = f"dist_switch_f{f}"
                if prev:
                    self.connect(prev, dist)
                if not first:
                    first = dist
                prev = dist
                self.connect(dist, "core_router_1")
                if self.floors >= 3:
                    self.connect(dist, "backup_core_router")
            if prev and first:
                self.connect(prev, first)

        elif self.topology == "mesh":
            switches = [f"dist_switch_f{f}" for f in range(1, self.floors + 1)]
            for i in range(len(switches)):
                for j in range(i + 1, len(switches)):
                    self.connect(switches[i], switches[j])
            for sw in switches:
                self.connect(sw, "core_router_1")
                if self.floors >= 3:
                    self.connect(sw, "backup_core_router")

        elif self.topology == "bus":
            prev = None
            for f in range(1, self.floors + 1):
                dist = f"dist_switch_f{f}"
                if prev:
                    self.connect(prev, dist)
                prev = dist
                self.connect(dist, "core_router_1")
                if self.floors >= 3:
                    self.connect(dist, "backup_core_router")

    # --------------------------------------------------
    # RULE 5 — SERVERS → SERVER SWITCH → CORE
    # --------------------------------------------------

    def connect_servers(self):
        if self.servers:
            self.connect("core_router_1", "server_switch")
            if self.floors >= 3:
                self.connect("backup_core_router", "server_switch")
            for s in self.servers:
                self.connect("server_switch", s)
            self.connect("server_switch", "dhcp_server")
            self.connect("server_switch", "dns_server")
        else:
            self.connect("dhcp_server", "core_router_1")
            self.connect("dns_server",  "core_router_1")
            if self.floors >= 3:
                self.connect("dns_server",  "backup_core_router")
                self.connect("dhcp_server", "backup_core_router")

    # --------------------------------------------------
    # RULE 6 — CORE → INTERNET / FIREWALL
    # --------------------------------------------------

    def connect_internet(self):
        if self.firewall_enabled:
            self.connect("core_router_1", "firewall_1")
            if self.floors >= 3:
                self.connect("backup_core_router", "firewall_1")
            self.connect("firewall_1", "internet_cloud")
        else:
            self.connect("core_router_1", "internet_cloud")

    # --------------------------------------------------
    # RUN ENGINE
    # --------------------------------------------------

    def _generate_connections(self):
        """(Re-)generate all connections for self.topology."""
        self.connections = []
        self.connect_pcs()
        self.connect_access_switches()
        self.connect_access_points()
        self.connect_distribution_to_core()
        self.connect_servers()
        self.connect_internet()

    def run(self, output_path):
        """Generate connections for the active topology and write to JSON."""
        self._generate_connections()

        print("Selected Topology:", self.topology)

        with open(output_path, "w") as f:
            json.dump(self.connections, f, indent=4)

        return self.connections

    def run_for_topology(self, topology_name: str, output_path: str):
        """
        Convenience: switch to topology_name, generate connections,
        write to output_path, and return the connection list.
        """
        self.set_topology(topology_name)
        return self.run(output_path)