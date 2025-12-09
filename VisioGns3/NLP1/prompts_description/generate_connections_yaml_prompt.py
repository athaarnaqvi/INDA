import json
import os

# ─────────────────────────────────────────────
# Base directory: VisioGns3
# prompts_description → NLP1 → VisioGns3
# ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

GENERATED_DIR = os.path.join(BASE_DIR, "Generated_files")

GNS3_SERVER_DETAILS = os.path.join(GENERATED_DIR, "gns3_server_details.txt")
CONNECTIONS_FILE = os.path.join(GENERATED_DIR, "Connections.json")
VSDX_PATH_FILE = os.path.join(BASE_DIR, "vsdx_path.txt")
OUTPUT_PLAYBOOK = os.path.join(
    BASE_DIR,
    "Main_playbooks",
    "Gns3_Connections.yaml"
)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def require_file(path, label):
    if not os.path.exists(path):
        raise FileNotFoundError(f"[MISSING] {label} → {path}")


def read_gns3_server_details(path):
    with open(path, "r") as f:
        lines = f.readlines()
        return lines[0].strip(), lines[1].strip()


def read_project_name(path):
    with open(path, "r") as f:
        return f.read().strip()


def is_switch_or_hub(name):
    return any(k in name.lower() for k in ["switch", "hub", "atm_switch"])


# ─────────────────────────────────────────────
# Playbook Generator
# ─────────────────────────────────────────────
def generate_ansible_playbook(ip, port, project_name, connections):
    playbook = f"""---
- name: Create NLP-based connections in GNS3
  hosts: localhost
  gather_facts: no

  vars:
    gns3_server: "http://{ip}:{port}"
    project_name: "{project_name}"

  tasks:
    - name: Get all projects
      uri:
        url: "{{{{ gns3_server }}}}/v2/projects"
        method: GET
        return_content: yes
      register: gns3_projects

    - name: Set project ID
      set_fact:
        project_id: "{{{{ (gns3_projects.json | selectattr('name','equalto',project_name) | list)[0].project_id }}}}"
      when: gns3_projects.json | selectattr('name','equalto',project_name) | list | length > 0

    - name: Open project if needed
      uri:
        url: "{{{{ gns3_server }}}}/v2/projects/{{{{ project_id }}}}/open"
        method: POST
        status_code: [200, 201]

    - name: Get nodes
      uri:
        url: "{{{{ gns3_server }}}}/v2/projects/{{{{ project_id }}}}/nodes"
        method: GET
        return_content: yes
      register: gns3_nodes
"""

    for conn in connections:
        frm = conn["from"]
        to = conn["to"]
        fa = conn["from_adapter_number"]
        ta = conn["to_adapter_number"]

        if is_switch_or_hub(frm):
            fa_adapter, fa_port = 0, fa
        else:
            fa_adapter, fa_port = fa, 0

        if is_switch_or_hub(to):
            ta_adapter, ta_port = 0, ta
        else:
            ta_adapter, ta_port = ta, 0

        playbook += f"""
    - name: Connect {frm} to {to}
      vars:
        node_map: "{{{{ gns3_nodes.json | items2dict(key_name='name', value_name='node_id') }}}}"
      uri:
        url: "{{{{ gns3_server }}}}/v2/projects/{{{{ project_id }}}}/links"
        method: POST
        body_format: json
        headers:
          Content-Type: application/json
        status_code: [200, 201]
        body:
          nodes:
            - node_id: "{{{{ node_map['{frm}'] }}}}"
              adapter_number: {fa_adapter}
              port_number: {fa_port}
            - node_id: "{{{{ node_map['{to}'] }}}}"
              adapter_number: {ta_adapter}
              port_number: {ta_port}
"""

    return playbook


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
if __name__ == "__main__":
    require_file(GNS3_SERVER_DETAILS, "GNS3 server details")
    require_file(CONNECTIONS_FILE, "NLP connections JSON")
    require_file(VSDX_PATH_FILE , "NLP project name")

    ip, port = read_gns3_server_details(GNS3_SERVER_DETAILS)
    project_name = read_project_name(VSDX_PATH_FILE)

    with open(CONNECTIONS_FILE, "r") as f:
        connections = json.load(f)

    playbook = generate_ansible_playbook(ip, port, project_name, connections)

    os.makedirs(os.path.dirname(OUTPUT_PLAYBOOK), exist_ok=True)
    with open(OUTPUT_PLAYBOOK, "w") as f:
        f.write(playbook)

    print("[SUCCESS] NLP Connections playbook generated:")
    print(OUTPUT_PLAYBOOK)
