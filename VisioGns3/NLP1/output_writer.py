import os
import json

def write_outputs(result, output_dir):
    machines_path = os.path.join(output_dir, "machine_names.txt")
    connections_path = os.path.join(output_dir, "Connections.json")

    with open(machines_path, "w") as f:
        for m in result["machines"]:
            f.write(m + "\n")

    with open(connections_path, "w") as f:
        json.dump(result["connections"], f, indent=2)

    return machines_path, connections_path
