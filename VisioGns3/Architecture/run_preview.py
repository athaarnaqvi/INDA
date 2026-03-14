"""
Entry point for the topology preview dialog — called by automation_architecture.sh.
Exit codes:
    0  → user clicked "Confirm & Deploy"
    1  → user cancelled / closed the dialog / error
"""

import sys
import os
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────────────
ARCH_DIR = Path(__file__).parent.absolute()          # .../VisioGns3/Architecture
VISIO_DIR = ARCH_DIR.parent                          # .../VisioGns3
ROOT_DIR  = VISIO_DIR.parent                         # .../INDA  (project root)

for p in (str(ARCH_DIR), str(VISIO_DIR), str(ROOT_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)
# ─────────────────────────────────────────────────────────────────────────────


def main() -> int:
    """
    Returns 0 if the user confirmed deployment, 1 otherwise.
    """
    if len(sys.argv) < 3:
        print(
            "Usage: python run_preview.py <machines_yaml_path> <connections_json_path>",
            file=sys.stderr,
        )
        return 1

    machines_yaml    = sys.argv[1]
    connections_json = sys.argv[2]

    # Validate paths before launching the GUI
    for label, path in (("machines YAML", machines_yaml),
                        ("connections JSON", connections_json)):
        if not os.path.exists(path):
            print(f"Error: {label} not found: {path}", file=sys.stderr)
            return 1

    # ── Qt application ────────────────────────────────────────────────────────
    from PyQt6.QtWidgets import QApplication
    from preview_dialog import TopologyPreviewDialog

    app = QApplication(sys.argv)
    app.setApplicationName("VisioGNS3 Topology Preview")

    dialog = TopologyPreviewDialog(
        machines_yaml_path=machines_yaml,
        connections_json_path=connections_json,
    )

    result = dialog.exec()   # QDialog.Accepted == 1, Rejected == 0

    # Map Qt result → shell exit code
    # QDialog.Accepted (user pressed "Confirm & Deploy") → exit 0  ✅
    # QDialog.Rejected (user cancelled / closed)         → exit 1  ⚠️
    from PyQt6.QtWidgets import QDialog
    return 0 if result == QDialog.DialogCode.Accepted else 1


if __name__ == "__main__":
    sys.exit(main())