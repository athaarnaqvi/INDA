import json
import os
import re
import subprocess

# Paths to files
GNS3_CONF_PATH = os.path.expanduser("~/.config/GNS3/2.2/gns3_server.conf")
OUTPUT_JSON_FILE = "gns3_templates.json"
SERVER_DETAILS_FILE = "gns3_server_details.txt"

def get_gns3_server_details(conf_path):
    """
    Reads the GNS3 configuration file and extracts the server IP and port.
    """
    try:
        with open(conf_path, "r") as file:
            conf_content = file.read()
        ip = re.search(r"host\s*=\s*([\d.]+)", conf_content).group(1)
        port = re.search(r"port\s*=\s*(\d+)", conf_content).group(1)
        return ip, port
    except Exception as e:
        raise RuntimeError(f"Failed to read GNS3 configuration file: {e}")

def save_server_details_to_file(ip, port, file_path):
    """
    Saves the server IP and port to a text file.
    """
    try:
        with open(file_path, "w") as file:
            file.write(f"{ip}\n{port}\n")
        print(f"Server details saved to {file_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to save server details to file: {e}")

def fetch_templates(ip, port):
    """
    Fetches the templates from the GNS3 server using the IP and port.
    """
    url = f"http://{ip}:{port}/v2/templates"
    try:
        result = subprocess.run(["curl", "-X", "GET", url], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to fetch templates: {result.stderr}")
        return json.loads(result.stdout)
    except Exception as e:
        raise RuntimeError(f"Error fetching templates: {e}")

def save_templates_to_json(templates, output_file):
    """
    Saves the templates to a JSON file in the specified format.
    """
    formatted_templates = {}

    for template in templates:
        name = template.get("name")
        template_id = template.get("template_id")
        node_type = template.get("template_type")
        
        if not name or not template_id:
            continue

        # Format for built-in templates
        if template.get("builtin"):
            formatted_templates[name] = {
                'compute_id':  "local",
                'node_type': node_type,
                'symbol': template.get("symbol"),
                'template_id': template_id
            }
        # Format for QEMU templates
        elif node_type == "qemu":
            formatted_templates[name] = {
                'compute_id': template.get("compute_id", "local"),
                'node_type': node_type,
                'symbol': template.get("symbol"),
                'template_id': template_id,
                'first_port_name': template.get("first_port_name"),
                'port_name_format': template.get("port_name_format"),
                'properties': {
                    'adapter_type': template.get("adapter_type"),
                    'adapters': template.get("adapters", 0),
                    'console_type': template.get("console_type"),
                    'cpus': template.get("cpus", 1),
                    'hda_disk_image': template.get("hda_disk_image"),
                    'hda_disk_interface': template.get("hda_disk_interface"),
                    'hdb_disk_image': template.get("hdb_disk_image"),
                    'hdb_disk_interface': template.get("hdb_disk_interface"),
                    'hdc_disk_image': template.get("hdc_disk_image"),
                    'hdc_disk_interface': template.get("hdc_disk_interface"),
                    'ram': template.get("ram", 0),
                    'boot_priority': template.get("boot_priority"),
                    'qemu_path': template.get("qemu_path"),
                    'replicate_network_connection_state': template.get("replicate_network_connection_state", False)
                }
            }

    try:
        with open(output_file, "w") as file:
            json.dump(formatted_templates, file, indent=4)
        print(f"Templates saved to {output_file}")
    except Exception as e:
        raise RuntimeError(f"Failed to save templates to JSON file: {e}")

def main():
    try:
        # Step 1: Get GNS3 server details
        ip, port = get_gns3_server_details(GNS3_CONF_PATH)
        print(f"Found GNS3 server: IP={ip}, Port={port}")

        # Step 2: Save server details to a text file
        save_server_details_to_file(ip, port, SERVER_DETAILS_FILE)

        # Step 3: Fetch templates
        templates = fetch_templates(ip, port)
        print(f"Fetched {len(templates)} templates from the server.")

        # Step 4: Save templates to JSON file
        save_templates_to_json(templates, OUTPUT_JSON_FILE)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()

