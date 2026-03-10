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

X_START = 100
Y_START = 100
X_INCREMENT = 60
Y_INCREMENT = 60

# ----------------------------------------------------
# GENERIC TEMPLATE MAPPING
# ----------------------------------------------------
GENERIC_TEMPLATE_MAPPING = {

    # Routers
    "core_router": "Dell OS10 N3248TE-10.5.5.5.105",
    "backup_core_router": "Dell OS10 N3248TE-10.5.5.5.105",

    # Switches
    "dist_switch": "Ethernet switch",
    "access_switch": "Ethernet switch",
    "server_switch": "Ethernet switch",

    # PCs
    "pc": "VPCS",
    "lab_pc": "VPCS",
    "laptop": "VPCS",
    "medical_pc": "VPCS",

    # Access Points
    "ap": "Ethernet switch",

    # Internet
    "internet_cloud": "Cloud",

    # Firewall
    "firewall": "pfSense 2.7.0",

    # Infrastructure servers
    "dhcp_server": "ubuntu-server",
    "dns_server": "ubuntu-server",

    # Hospital servers
    "emr_server": "ubuntu-server",
    "lab_server": "ubuntu-server",
    "radiology_server": "ubuntu-server",
    "pharmacy_server": "ubuntu-server",

    # Office servers
    "file_server": "ubuntu-server",
    "mail_server": "ubuntu-server",
    "backup_server": "ubuntu-server",
    "vpn_server": "ubuntu-server",

    # School servers
    "lms_server": "ubuntu-server",
    "exam_server": "ubuntu-server",
    "library_server": "ubuntu-server",
    "research_server": "ubuntu-server",

    # Hotel servers
    "booking_server": "ubuntu-server",
    "guest_management_server": "ubuntu-server",
    "billing_server": "ubuntu-server",
    "cctv_server": "ubuntu-server"
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

# ----------------------------------------------------
# YAML GENERATION
# ----------------------------------------------------

def generate_yaml(ip, port, machines, templates):
    project_name = generate_project_name()
    with open(VSDX_PATH_FILE, "w") as f:
        f.write(project_name)

    print(f"[INFO] Architecture project name stored → {VSDX_PATH_FILE}")
    
    yaml_content = f"""
- hosts: localhost
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

    grid = int(math.sqrt(nearest_square(len(machines))))

    x, y = X_START, Y_START
    count = 0

    for machine in machines:
        template = find_template(machine, templates)
        if not template:
            continue

        body_items = [
            f'"{k}": {json.dumps(v)}'
            for k, v in template.items()
            if k not in {"name", "x", "y"}
        ]

        body_str = ",\n            ".join(body_items)

        yaml_content += f"""
    - name: Add {machine}
      uri:
        url: "{{{{ gns3_url }}}}/v2/projects/{{{{ project_result.json.project_id }}}}/nodes"
        method: POST
        headers:
          Content-Type: "application/json"
        body: |
          {{
            "name": "{machine}",
            "x": {x},
            "y": {y},
            {body_str}
          }}
        body_format: json
        status_code: 201
"""

        x += X_INCREMENT
        count += 1
        if count % grid == 0:
            x = X_START
            y += Y_INCREMENT

    with open(OUTPUT_YAML, "w") as f:
        f.write(yaml_content)

    print(f"[SUCCESS] Architecture Machines YAML generated:")
    print(f"→ {OUTPUT_YAML}")

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
