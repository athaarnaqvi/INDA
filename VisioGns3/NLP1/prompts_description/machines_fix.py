import json
import os

# ----------------------------------------------------
# PATH SETUP (PORTABLE)
# ----------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Move up: prompts_description → NLP1 → VisioGns3
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))

GENERATED_FILES_DIR = os.path.join(
    PROJECT_ROOT,
    "Generated_files"
)

INPUT_FILE = os.path.join(GENERATED_FILES_DIR, "pre_Connections.json")
OUTPUT_FILE = os.path.join(GENERATED_FILES_DIR, "machine_names.txt")

# ----------------------------------------------------
# LOGIC
# ----------------------------------------------------

def normalize_name(name):
    """Remove spaces and convert to lowercase if desired."""
    return name.replace(" ", "")

def extract_unique_machine_names(connections):
    machines = set()

    for conn in connections:
        if "from" in conn:
            machines.add(normalize_name(conn["from"]))
        if "to" in conn:
            machines.add(normalize_name(conn["to"]))

    return sorted(machines)


def main():
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"[ERROR] Missing input file: {INPUT_FILE}")

    with open(INPUT_FILE, "r") as f:
        connections = json.load(f)

    machine_names = extract_unique_machine_names(connections)

    os.makedirs(GENERATED_FILES_DIR, exist_ok=True)

    with open(OUTPUT_FILE, "w") as f:
        for name in machine_names:
            f.write(name + "\n")

    print("[SUCCESS] Machine names extracted from NLP connections")
    print(f"→ Input : {INPUT_FILE}")
    print(f"→ Output: {OUTPUT_FILE}")
    print(f"→ Count : {len(machine_names)} devices")


# ----------------------------------------------------
# ENTRY POINT
# ----------------------------------------------------

if __name__ == "__main__":
    main()
