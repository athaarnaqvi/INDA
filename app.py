import sys
import os
import subprocess
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QTextEdit, QFileDialog
from PyQt6.QtGui import QPalette, QColor, QFont
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# GNS3 Config File Path
GNS3_CONF_PATH = os.path.expanduser("~/.config/GNS3/2.2/gns3_server.conf")

class WorkerThread(QThread):
    output_signal = pyqtSignal(str)

    def __init__(self, script_path):
        super().__init__()
        self.script_path = script_path

    def run(self):
        process = subprocess.Popen(['bash', self.script_path], cwd=os.path.expanduser("~/VisioGns3"),
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        for line in iter(process.stdout.readline, ''):
            self.output_signal.emit(line.strip())

        process.stdout.close()
        process.wait()


class VisioGNS3App(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Visio to GNS3")
        self.setGeometry(200, 200, 550, 400)
        
        # Set dark mode styling
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
        self.setPalette(palette)

        layout = QVBoxLayout()

        self.label_ip = QLabel("Enter GNS3 Server IP:")
        self.label_ip.setStyleSheet("color: white; font-weight: bold;")
        self.input_ip = QLineEdit()
        self.input_ip.setStyleSheet("background-color: white; padding: 5px;")

        self.label_port = QLabel("Enter GNS3 Server Port:")
        self.label_port.setStyleSheet("color: white; font-weight: bold;")
        self.input_port = QLineEdit()
        self.input_port.setStyleSheet("background-color: white; padding: 5px;")

        self.save_button = QPushButton("Save & Apply")
        self.save_button.setStyleSheet("background-color: #2196F3; color: white; padding: 8px; font-weight: bold;")
        self.save_button.clicked.connect(self.save_gns3_config)

        self.upload_button = QPushButton("Upload File")
        self.upload_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; font-weight: bold;")
        self.upload_button.clicked.connect(self.upload_file)

        self.run_button = QPushButton("Run Automation")
        self.run_button.setStyleSheet("background-color: #FF9800; color: white; padding: 8px; font-weight: bold;")
        self.run_button.clicked.connect(self.run_script)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet("background-color: #121212; color: #FFFFFF; font-size: 12px;")

        layout.addWidget(self.label_ip)
        layout.addWidget(self.input_ip)
        layout.addWidget(self.label_port)
        layout.addWidget(self.input_port)
        layout.addWidget(self.save_button)
        layout.addWidget(self.upload_button)
        layout.addWidget(self.run_button)
        layout.addWidget(self.output_text)

        self.setLayout(layout)

    def save_gns3_config(self):
        ip = self.input_ip.text().strip()
        port = self.input_port.text().strip()

        if not ip or not port:
            self.output_text.append("⚠️ Please enter both IP and port.")
            return

        try:
            with open(GNS3_CONF_PATH, "w") as file:
                file.write(f"[Server]\nhost = {ip}\nport = {port}\n")

            self.output_text.append(f"✅ GNS3 Server configured with IP={ip}, Port={port}")

            subprocess.run(["pkill", "-f", "gns3server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.Popen(["gns3server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            self.output_text.append("🚀 GNS3 Server restarted with new settings.")
        
        except Exception as e:
            self.output_text.append(f"❌ Error saving configuration: {e}")

    def upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select a File", "", "All Files (*)")
        if file_path:
            self.output_text.clear()  # Clear console before upload
            upload_folder = os.path.expanduser("~/INDA/VisioGns3/uploads")
            os.makedirs(upload_folder, exist_ok=True)
            os.system(f"cp '{file_path}' '{upload_folder}'")
            self.output_text.append(f"✅ File uploaded: {file_path}")

    def run_script(self):
        script_path = os.path.expanduser("~/INDA/VisioGns3/automation_final.sh")

        self.worker = WorkerThread(script_path)
        self.worker.output_signal.connect(self.update_output)
        self.worker.start()

    def update_output(self, text):
        self.output_text.append(text)
        self.output_text.ensureCursorVisible()


# Run the application
app = QApplication(sys.argv)
app.setApplicationName("Visio-GNS3")
app.setDesktopFileName("visio-gns3.desktop")
window = VisioGNS3App()
window.show()
sys.exit(app.exec())
