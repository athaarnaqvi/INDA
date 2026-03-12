#!/bin/bash
set -e
set -u

echo "🚀 Starting Architecture Orchestrator automation..."

# ----------------------------------------
# Base directory (VisioGns3)
# ----------------------------------------

BASE_DIR="/home/fiza-wajid/INDA/VisioGns3"
ARCH_DIR="$BASE_DIR/Architecture"
GENERATED_DIR="$BASE_DIR/Generated_files"
MAIN_PLAYBOOKS_DIR="$BASE_DIR/Main_playbooks"
NLP_DIR="$BASE_DIR/NLP1/prompts_description"
PYTHON="/home/fiza-wajid/INDA/venv/bin/python"

echo "📁 Base dir          : $BASE_DIR"
echo "📁 Architecture dir  : $ARCH_DIR"
echo "📁 Generated files   : $GENERATED_DIR"
echo "📁 Main playbooks    : $MAIN_PLAYBOOKS_DIR"

# ----------------------------------------
# Step 1: Generate machine names and pre-connections JSON
# ----------------------------------------

echo "⚙️ Fixing connections..."
$PYTHON "$NLP_DIR/connections_fix.py"

echo "✅ Connections fixed"

# ----------------------------------------
# Step 2: Retrieve GNS3 server details & templates
# ----------------------------------------

echo "⚙️ Retrieving GNS3 server details and templates..."
$PYTHON "$BASE_DIR/retrieve_detail.py"

echo "✅ GNS3 server details retrieved"

# ----------------------------------------
# Step 3: Generate YAMLs from architecture JSON
# ----------------------------------------

echo "🧾 Generating machine YAML from architecture..."
$PYTHON "$ARCH_DIR/generate_machines_yaml_architecture.py"

echo "🔗 Generating connections YAML from architecture..."
$PYTHON "$ARCH_DIR/generate_connections_yaml_architecture.py"

echo "✅ YAML generation completed"

# ----------------------------------------
# Step 4: Generate Topology Preview
# ----------------------------------------

echo "🎨 Generating topology preview (SVG/XML)..."
$PYTHON "$BASE_DIR/Architecture/topology_visualization.py" "$BASE_DIR/Main_playbooks/Gns3_Machines.yaml" "$BASE_DIR/Generated_files/Connections.json" both

# ----------------------------------------
# Step 5: Show Preview Dialog
# ----------------------------------------

echo "📺 Launching topology preview dialog..."
cd "$BASE_DIR/Architecture"
python3 run_preview.py "$BASE_DIR/Main_playbooks/Gns3_Machines.yaml" "$BASE_DIR/Generated_files/Connections.json"

if [ $? -eq 0 ]; then
    echo "✅ User confirmed - proceeding with deployment"

    # ----------------------------------------
    # Step 6: Run Ansible Playbooks
    # ----------------------------------------
    echo "▶️ Running Ansible Playbooks..."

    cd "$MAIN_PLAYBOOKS_DIR"

    echo "➡️ Running Gns3_Machines.yaml"
    ansible-playbook Gns3_Machines.yaml

    echo "➡️ Running Gns3_Connections.yaml"
    ansible-playbook Gns3_Connections.yaml

    echo "✅ Architecture Orchestrator completed successfully"
else
    echo "⚠️ Deployment cancelled by user"
    exit 0
fi