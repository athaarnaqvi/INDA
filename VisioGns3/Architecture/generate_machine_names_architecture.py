import math


class ArchitectureEngine:

    def __init__(self, floors, rooms, users, width, unit, building_type):

        self.floors = floors
        self.rooms = rooms
        self.users = users
        self.width = width
        self.unit = unit
        self.building_type = building_type

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
        self.machines.append("dhcp_server")
        self.machines.append("dns_server")
        self.machines.append("internet_cloud")


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

    def add_user_pcs(self):

        """
        RULE:

        Each user in a room gets one PC.

        Naming Convention:
        pc_f{floor}_r{room}_u{user}
        """

        for floor in range(1, self.floors + 1):

            for room in range(1, self.rooms + 1):

                for user in range(1, self.users + 1):

                    name = f"pc_f{floor}_r{room}_u{user}"
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