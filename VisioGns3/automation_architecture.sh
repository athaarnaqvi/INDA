#!/bin/bash
set -e  # Exit immediately if any command fails

echo "🚀 Starting Architecture Orchestrator automation..."

# ----------------------------------------
# Base directory (VisioGns3)
# ----------------------------------------
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
ARCH_DIR="$BASE_DIR/Architecture"
GENERATED_DIR="$BASE_DIR/Generated_files"
MAIN_PLAYBOOKS_DIR="$BASE_DIR/Main_playbooks"
NLP_DIR="$BASE_DIR/NLP1/prompts_description"  # optional if any NLP integration

echo "📁 Base dir          : $BASE_DIR"
echo "📁 Architecture dir  : $ARCH_DIR"
echo "📁 Generated files   : $GENERATED_DIR"
echo "📁 Main playbooks    : $MAIN_PLAYBOOKS_DIR"

# ----------------------------------------
# Step 1: Generate machine names and pre-connections JSON
# ----------------------------------------
echo "⚙️ Fixing connections..."

python3 "$NLP_DIR/connections_fix.py"

echo "✅ Architecture generation completed"

# ----------------------------------------
# Step 2: Retrieve GNS3 server details & templates
# ----------------------------------------
echo "⚙️ Retrieving GNS3 server details and templates..."

python3 "$BASE_DIR/retrieve_detail.py"

echo "✅ GNS3 server details retrieved"

# ----------------------------------------
# Step 3: Generate YAMLs from architecture JSON
# ----------------------------------------
echo "🧾 Generating machine YAML from architecture..."
python3 "$ARCH_DIR/generate_machines_yaml_architecture.py"

echo "🔗 Generating connections YAML from architecture..."
python3 "$ARCH_DIR/generate_connections_yaml_architecture.py"

echo "✅ YAML generation completed"

# ----------------------------------------
# Step 4: Run Ansible playbooks
# ----------------------------------------
echo "▶️ Running Ansible Playbooks..."

cd "$MAIN_PLAYBOOKS_DIR"

echo "➡️ Running Gns3_Machines.yaml"
ansible-playbook Gns3_Machines.yaml

echo "➡️ Running Gns3_Connections.yaml"
ansible-playbook Gns3_Connections.yaml

echo "✅ Architecture Orchestrator completed successfully"