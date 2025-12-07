# output_writer.py
import json

def write_outputs(result: dict, machines_path="machines.txt", connections_path="connections.json"):
    machines = result.get("machines", [])
    connections = result.get("connections", [])

    # Write machines.txt
    with open(machines_path, "w") as f:
        for m in machines:
            f.write(f"{m}\n")

    # Write connections.json (pretty)
    with open(connections_path, "w") as f:
        json.dump(connections, f, indent=4)

    return machines_path, connections_path
