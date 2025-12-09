#!/bin/bash
set -e  # exit on error

echo "🚀 Starting Instruction Orchestrator automation..."

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
NLP_DIR="$BASE_DIR/NLP1/prompts_description"

echo "📁 Base dir: $BASE_DIR"
echo "📁 NLP dir : $NLP_DIR"

# ----------------------------------------
# Step 1: Run fixes in PARALLEL
# ----------------------------------------
echo "⚙️ Running NLP fix scripts in parallel..."

python3 "$NLP_DIR/connections_fix.py" &
PID_CONN=$!

python3 "$NLP_DIR/machines_fix.py" &
PID_MACH=$!

wait $PID_CONN
wait $PID_MACH

echo "✅ NLP fix scripts completed"

# ----------------------------------------
# Step 2: Generate YAMLs (SEQUENTIAL)
# ----------------------------------------
echo "🧠 Generating machine YAML from NLP..."
python3 "$NLP_DIR/generate_machines_yaml_prompt.py"

echo "🔗 Generating connections YAML from NLP..."
python3 "$NLP_DIR/generate_connections_yaml_prompt.py"

echo "✅ YAML generation completed"

# ----------------------------------------
# Step 3: Run Ansible playbooks
# ----------------------------------------
PLAYBOOK_DIR="$BASE_DIR/Main_playbooks"
cd "$PLAYBOOK_DIR"

echo "▶️ Running Ansible Playbooks..."

echo "➡️ Gns3_Machines.yaml"
ansible-playbook Gns3_Machines.yaml

echo "➡️ Gns3_Connections.yaml"
ansible-playbook Gns3_Connections.yaml

echo "✅ Instruction Orchestrator completed successfully"
