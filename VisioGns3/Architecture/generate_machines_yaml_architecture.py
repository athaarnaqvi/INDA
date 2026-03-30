import json
import os
import re
import math
from datetime import datetime

# ----------------------------------------------------
# PATHS (PORTABLE)
# ----------------------------------------------------

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
GENERATED_DIR = os.path.join(BASE_DIR, "Generated_files")

GNS3_SERVER_DETAILS = os.path.join(GENERATED_DIR, "gns3_server_details.txt")
TEMPLATES_JSON = os.path.join(GENERATED_DIR, "gns3_templates.json")
MACHINE_NAMES_TXT = os.path.join(GENERATED_DIR, "machine_names.txt")
VSDX_PATH_FILE = os.path.join(BASE_DIR, "vsdx_path.txt")
OUTPUT_YAML = os.path.join(BASE_DIR, "Main_playbooks", "Gns3_Machines.yaml")

# ----------------------------------------------------
# DEVICE PLACEMENT
# ----------------------------------------------------

X_START = -750
Y_START = -400
X_INCREMENT = 150
Y_INCREMENT = 150

# ----------------------------------------------------
# 🔥 NEW: PORT GENERATION
# ----------------------------------------------------

def generate_ports_mapping(num_ports=50):
    return [
        {
            "name": f"Ethernet{i}",
            "port_number": i,
            "type": "access",
            "vlan": 1
        }
        for i in range(num_ports)
    ]

# ----------------------------------------------------
# GENERIC TEMPLATE MAPPING
# ----------------------------------------------------

GENERIC_TEMPLATE_MAPPING = {
    "core_router": "Dell OS10 N3248TE-10.5.5.5.105",
    "backup_core_router": "Dell OS10 N3248TE-10.5.5.5.105",

    "dist_switch": "Ethernet Switch",
    "access_switch": "Ethernet Switch",
    "server_switch": "Ethernet Switch",

    "pc": "VPCS",
    "lab_pc": "VPCS",
    "laptop": "VPCS",
    "medical_pc": "VPCS",

    "ap": "Ethernet Switch",
    "internet_cloud": "Cloud",
    "firewall": "pfSense 2.7.0",

    "dhcp_server": "Alpine Linux Virt 3.18.4",
    "dns_server": "Alpine Linux Virt 3.18.4",

    "emr_server": "Alpine Linux Virt 3.18.4",
    "lab_server": "Alpine Linux Virt 3.18.4",
    "radiology_server": "Alpine Linux Virt 3.18.4",
    "pharmacy_server": "Alpine Linux Virt 3.18.4",

    "file_server": "Alpine Linux Virt 3.18.4",
    "mail_server": "Alpine Linux Virt 3.18.4",
    "backup_server": "Alpine Linux Virt 3.18.4",
    "vpn_server": "Alpine Linux Virt 3.18.4",

    "lms_server": "Alpine Linux Virt 3.18.4",
    "exam_server": "Alpine Linux Virt 3.18.4",
    "library_server": "Alpine Linux Virt 3.18.4",
    "research_server": "Alpine Linux Virt 3.18.4",

    "booking_server": "Alpine Linux Virt 3.18.4",
    "guest_management_server": "Alpine Linux Virt 3.18.4",
    "billing_server": "Alpine Linux Virt 3.18.4",
    "cctv_server": "Alpine Linux Virt 3.18.4"
}

# ----------------------------------------------------
# HELPERS
# ----------------------------------------------------

def read_gns3_server_details():
    with open(GNS3_SERVER_DETAILS, "r") as f:
        lines = f.readlines()
        return lines[0].strip(), lines[1].strip()

def load_templates():
    with open(TEMPLATES_JSON, "r") as f:
        return json.load(f)

def load_machine_names():
    with open(MACHINE_NAMES_TXT, "r") as f:
        return [line.strip() for line in f if line.strip()]

def generate_project_name():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"architecture_topology_{timestamp}"

def normalize_name(name):
    name = re.sub(r"ONFrontView.*$", "", name)
    name = re.sub(r"[^a-zA-Z0-9]", "", name).lower()
    return name

def find_template(machine_name, templates):
    base_name = machine_name.lower()
    for keyword, mapped_template in GENERIC_TEMPLATE_MAPPING.items():
        if base_name.startswith(keyword) or keyword in base_name:
            for template_name, template_data in templates.items():
                if template_name == mapped_template:
                    print(f"[MAPPED] {machine_name} → {template_name}")
                    return template_data
    print(f"[WARNING] No template match for: {machine_name}")
    return None

def nearest_square(n):
    r = math.sqrt(n)
    return math.floor(r) ** 2 if (n - math.floor(r) ** 2) < (math.ceil(r) ** 2 - n) else math.ceil(r) ** 2

def extract_floor(machine):
    match = re.search(r"_f(\d+)", machine)
    if match:
        return int(match.group(1))
    return 0

def group_machines_by_floor(machines):
    floors = {}
    for m in machines:
        f = extract_floor(m)
        floors.setdefault(f, []).append(m)
    return floors

# ----------------------------------------------------
# YAML GENERATION
# ----------------------------------------------------

# ----------------------------------------------------
# YAML GENERATION
# ----------------------------------------------------

def generate_yaml(ip, port, machines, templates):
    project_name = generate_project_name()
    with open(VSDX_PATH_FILE, "w") as f:
        f.write(project_name)

    floors = group_machines_by_floor(machines)
    floors_per_row = 2
    floor_spacing_x = 700
    floor_spacing_y = 600
    floor_index = 0

    yaml_content = f"""- hosts: localhost
  gather_facts: no
  vars:
    gns3_url: "http://{ip}:{port}"
    ansible_python_interpreter: /usr/bin/python3

  tasks:
    - name: Create Architecture GNS3 project
      uri:
        url: "{{{{ gns3_url }}}}/v2/projects"
        method: POST
        headers:
          Content-Type: "application/json"
        body:
          name: "{project_name}"
        body_format: json
        status_code: 201
      register: project_result
"""

    for floor, floor_machines in floors.items():
        row = floor_index // floors_per_row
        col = floor_index % floors_per_row
        base_x = X_START + (col * floor_spacing_x)
        base_y = Y_START + (row * floor_spacing_y)

        grid = int(math.sqrt(nearest_square(len(floor_machines))))
        x = base_x
        y = base_y
        count = 0

        for machine in floor_machines:
            template = find_template(machine, templates)
            if not template:
                continue

            body_dict = {
                "name": machine,
                "x": x,
                "y": y,
                **template
            }

            if template.get("node_type") == "ethernet_switch":
                body_dict["properties"] = {
                    "ports_mapping": generate_ports_mapping(50)
                }

            # Convert dict to JSON with correct indentation
            body_str = json.dumps(body_dict, indent=4)
            indented_body = "\n".join("          " + line for line in body_str.splitlines())

            yaml_content += f"""    - name: Add {machine}
      uri:
        url: "{{{{ gns3_url }}}}/v2/projects/{{{{ project_result.json.project_id }}}}/nodes"
        method: POST
        headers:
          Content-Type: "application/json"
        body: |
{indented_body}
        body_format: json
        status_code: 201
"""

            x += X_INCREMENT
            count += 1
            if count % grid == 0:
                x = base_x
                y += Y_INCREMENT

        # DRAW FLOOR
        radius = 300
        center_x = base_x + 200
        center_y = base_y + 200

        yaml_content += f"""    - name: Draw Floor {floor} boundary
      uri:
        url: "{{{{ gns3_url }}}}/v2/projects/{{{{ project_result.json.project_id }}}}/drawings"
        method: POST
        headers:
          Content-Type: "application/json"
        body_format: json
        body: |
          {{
              "svg": "<ellipse cx='{center_x}' cy='{center_y}' rx='{radius}' ry='{radius}' style='fill:none;stroke:blue;stroke-width:3'/>",
              "x": {base_x},
              "y": {base_y},
              "z": -1
          }}
        status_code: 201
"""
        floor_index += 1

    with open(OUTPUT_YAML, "w") as f:
        f.write(yaml_content)

    print("[SUCCESS] YAML generated")


# ----------------------------------------------------
# MAIN
# ----------------------------------------------------

def main():
    ip, port = read_gns3_server_details()
    templates = load_templates()
    machines = load_machine_names()
    generate_yaml(ip, port, machines, templates)


if __name__ == "__main__":
    main()