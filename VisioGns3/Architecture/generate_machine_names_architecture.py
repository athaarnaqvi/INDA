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