"""
Topology Preview Launcher
Location: VisioGns3/run_preview.py
Usage: python run_preview.py <machines_yaml> <connections_json>
"""

import sys
import os
from pathlib import Path

# Add current directory to path
ARCH_DIR = Path(__file__).parent.absolute()
VISIO_GNS3_DIR = ARCH_DIR.parent

sys.path.insert(0, str(ARCH_DIR))
sys.path.insert(0, str(VISIO_GNS3_DIR))

from PyQt6.QtWidgets import QApplication, QMessageBox
from preview_dialog import TopologyPreviewDialog


def main():
    """Launch the topology preview dialog"""
    
    # Default paths if not provided
    if len(sys.argv) >= 3:
        machines_yaml = sys.argv[1]
        connections_json = sys.argv[2]
    else:
        # Use defaults
        machines_yaml = os.path.join(VISIO_GNS3_DIR, "Main_playbooks", "Gns3_Machines.yaml")
        connections_json = os.path.join(VISIO_GNS3_DIR, "Generated_files", "Connections.json")
    
    # Check if files exist
    if not os.path.exists(machines_yaml):
        print(f"❌ Machines YAML not found: {machines_yaml}")
        sys.exit(1)
    
    if not os.path.exists(connections_json):
        print(f"❌ Connections JSON not found: {connections_json}")
        sys.exit(1)
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Show preview dialog
    dialog = TopologyPreviewDialog(machines_yaml, connections_json)
    result = dialog.exec()
    
    if result == dialog.accepted:
        print("✅ User confirmed deployment")
        sys.exit(0)
    else:
        print("❌ User cancelled deployment")
        sys.exit(1)


if __name__ == '__main__':
    main()