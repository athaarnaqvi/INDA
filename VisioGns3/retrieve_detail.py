import json
import os
import re
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

GNS3_CONF_PATH = os.path.expanduser("~/.config/GNS3/2.2/gns3_server.conf")

OUTPUT_JSON_FILE = os.path.join(BASE_DIR, "Generated_files", "gns3_templates.json")
SERVER_DETAILS_FILE = os.path.join(BASE_DIR, "Generated_files", "gns3_server_details.txt")


def get_gns3_server_details(conf_path):
    try:
        with open(conf_path, "r") as file:
            conf_content = file.read()
        ip = re.search(r"host\s*=\s*([\d.]+)", conf_content).group(1)
        port = re.search(r"port\s*=\s*(\d+)", conf_content).group(1)
        return ip, port
    except Exception as e:
        raise RuntimeError(f"Failed to read GNS3 configuration file: {e}")


def save_server_details_to_file(ip, port, file_path):
    with open(file_path, "w") as file:
        file.write(f"{ip}\n{port}\n")


# def fetch_templates(ip, port):
#     url = f"http://{ip}:{port}/v2/templates"
#     result = subprocess.run(["curl", "-X", "GET", url], capture_output=True, text=True)
#     return json.loads(result.stdout)

import requests

def fetch_templates(ip, port):
    url = f"http://{ip}:{port}/v2/templates"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # raises error if not 200
        return response.json()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"GNS3 API request failed: {e}")
    except ValueError:
        raise RuntimeError("Invalid JSON received from GNS3")


def save_templates_to_json(templates, output_file):
    formatted_templates = {}

    for template in templates:
        name = template.get("name")
        template_id = template.get("template_id")
        node_type = template.get("template_type")

        if not name or not template_id:
            continue

        if template.get("builtin"):
            formatted_templates[name] = {
                "compute_id": "local",
                "node_type": node_type,
                "symbol": template.get("symbol"),
                "template_id": template_id
            }

        elif node_type == "qemu":
            formatted_templates[name] = {
                "compute_id": template.get("compute_id", "local"),
                "node_type": node_type,
                "symbol": template.get("symbol"),
                "template_id": template_id,
                "first_port_name": template.get("first_port_name"),
                "port_name_format": template.get("port_name_format"),
                "properties": {
                    "adapter_type": template.get("adapter_type"),
                    "adapters": template.get("adapters", 0),
                    "console_type": template.get("console_type"),
                    "cpus": template.get("cpus", 1),
                    "hda_disk_image": template.get("hda_disk_image"),
                    "hda_disk_interface": template.get("hda_disk_interface"),
                    "ram": template.get("ram", 0),
                    "qemu_path": template.get("qemu_path"),
                    "replicate_network_connection_state": template.get(
                        "replicate_network_connection_state", False)
                }
            }

        elif node_type == "ethernet_switch":
            formatted_templates[name] = {
                "compute_id": template.get("compute_id", "local"),
                "node_type": node_type,
                "symbol": template.get("symbol"),
                "template_id": template_id
            }

    with open(output_file, "w") as file:
        json.dump(formatted_templates, file, indent=4)


def main():
    ip, port = get_gns3_server_details(GNS3_CONF_PATH)
    if ip == "localhost":
        ip = "127.0.0.1"

    save_server_details_to_file(ip, port, SERVER_DETAILS_FILE)

    templates = fetch_templates(ip, port)
    save_templates_to_json(templates, OUTPUT_JSON_FILE)


if __name__ == "__main__":
    main()