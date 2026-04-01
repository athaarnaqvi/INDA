import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Move up: prompts_description → NLP1 → VisioGns3
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))

GENERATED_FILES_DIR = os.path.join(
    PROJECT_ROOT,
    "Generated_files"
)

INPUT_FILE = os.path.join(GENERATED_FILES_DIR, "pre_Connections.json")
OUTPUT_FILE = os.path.join(GENERATED_FILES_DIR, "Connections.json")

def normalize_name(name):
    """Remove spaces and convert to lowercase if desired."""
    return name.replace(" ", "")

def is_vpcs(name):
    name = name.lower()
    return any(k in name for k in ["vpcs", "pc", "computer", "terminal"])


def assign_adapters(connections):
    adapter_counter = {}
    mapped_connections = []
    vpcs_used = set()   # 🔥 track used VPCS

    for conn in connections:
        src = normalize_name(conn["from"])
        dst = normalize_name(conn["to"])

        # 🚨 Skip if VPCS already used
        if is_vpcs(src):
            if src in vpcs_used:
                print(f"[SKIPPED] {src} already connected (VPCS limit)")
                continue

        if is_vpcs(dst):
            if dst in vpcs_used:
                print(f"[SKIPPED] {dst} already connected (VPCS limit)")
                continue

        # Initialize counters
        if src not in adapter_counter:
            adapter_counter[src] = 0
        if dst not in adapter_counter:
            adapter_counter[dst] = 0

        # Assign adapters
        src_adapter = 0 if is_vpcs(src) else adapter_counter[src]
        dst_adapter = 0 if is_vpcs(dst) else adapter_counter[dst]

        mapped_connections.append({
            "from": src,
            "to": dst,
            "from_adapter_number": src_adapter,
            "to_adapter_number": dst_adapter
        })

        # Mark VPCS as used
        if is_vpcs(src):
            vpcs_used.add(src)
        else:
            adapter_counter[src] += 1

        if is_vpcs(dst):
            vpcs_used.add(dst)
        else:
            adapter_counter[dst] += 1

    return mapped_connections


def main():
    with open(INPUT_FILE, "r") as f:
        simple_connections = json.load(f)

    mapped = assign_adapters(simple_connections)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(mapped, f, indent=2)

    print(f"[SUCCESS] Adapter mapping written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
