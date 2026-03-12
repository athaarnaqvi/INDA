#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status
set -u  # Treat unset variables as an error

# ────────── Paths ──────────
BASE_DIR="/home/athaar/INDA/VisioGns3"

# Python environment
PYTHON="/home/athaar/INDA/venv/bin/python"

# Scripts to generate YAMLs
SCRIPTS=(
    "$BASE_DIR/NLP1/prompts_description/connections_fix.py"
    "$BASE_DIR/retrieve_detail.py"
    "$BASE_DIR/Architecture/generate_machines_yaml_architecture.py"
    "$BASE_DIR/Architecture/generate_connections_yaml_architecture.py"
)

# ────────── Execute each script sequentially ──────────
for SCRIPT in "${SCRIPTS[@]}"; do
    echo "➡️ Running $SCRIPT ..."
    $PYTHON "$SCRIPT"
    echo "✅ Finished $SCRIPT"
done

# ────────── Run the generated Ansible playbooks ──────────
echo "➡️ Running Gns3_Machines.yaml"
ansible-playbook "$BASE_DIR/Main_playbooks/Gns3_Machines.yaml"

echo "➡️ Running Gns3_Connections.yaml"
ansible-playbook "$BASE_DIR/Main_playbooks/Gns3_Connections.yaml"

echo "✅ All scripts and playbooks executed successfully!"