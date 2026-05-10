import json
import os
import re
import math
from datetime import datetime

# ----------------------------------------------------
# PATHS (PORTABLE)
# ----------------------------------------------------

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
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
    "router": "Dell OS10 N3248TE-10.5.5.5.105",
    "switch": "Ethernet switch",
    "hub": "Ethernet hub",
    "server": "Alpine Linux Virt 3.18.4",
    "pc": "VPCS",
    "terminal": "VPCS",
    "computer": "VPCS",
    "cloud": "Cloud",
    "nat": "NAT"
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
    return f"nlp_topology_{timestamp}"

def read_project_name(path):
    with open(path, "r") as f:
        return f.read().strip()
    
def normalize_name(name):
    name = re.sub(r"ONFrontView.*$", "", name)
    name = re.sub(r"[^a-zA-Z0-9]", "", name).lower()
    return name

def find_template(machine_name, templates):
    base_name = machine_name.lower()

    for keyword, mapped_name in GENERIC_TEMPLATE_MAPPING.items():
        if keyword in base_name:
            normalized_mapped = normalize_name(mapped_name)

            for template_name, template_data in templates.items():
                normalized_template = normalize_name(template_name)
                if normalized_mapped in normalized_template or normalized_template in normalized_mapped:
                    print(f"[NLP TEMPLATE] {machine_name} → {template_name}")
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
    # project_name = generate_project_name()
    # with open(VSDX_PATH_FILE, "w") as f:
    #     f.write(project_name)

    # print(f"[INFO] NLP project name stored → {VSDX_PATH_FILE}")
    project_name = read_project_name(VSDX_PATH_FILE)
    yaml_content = f"""
- hosts: localhost
  gather_facts: no
  vars:
    gns3_url: "http://{ip}:{port}"
    ansible_python_interpreter: /usr/bin/python3

  tasks:
    - name: Create NLP GNS3 project
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

    print(f"[SUCCESS] NLP Machines YAML generated:")
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
