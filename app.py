import sys
import os
import subprocess
import traceback
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QLineEdit, QTextEdit,
                              QFileDialog, QMessageBox, QFrame, QStackedWidget,
                              QGraphicsDropShadowEffect)
from PyQt6.QtGui import QPalette, QColor, QFont
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer

# GNS3 Config File Path
GNS3_CONF_PATH = os.path.expanduser("~/.config/GNS3/2.2/gns3_server.conf")


class WorkerThread(QThread):
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, script_path):
        super().__init__()
        self.script_path = script_path

    def run(self):
        process = subprocess.Popen(['bash', self.script_path],
                                   cwd=os.path.expanduser("~/INDA/VisioGns3"),
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in iter(process.stdout.readline, ''):
            self.output_signal.emit(line.strip())
        process.stdout.close()
        process.wait()
        self.finished_signal.emit()


class ScriptRunnerThread(QThread):
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, script_path, user_prompt):
        super().__init__()
        self.script_path = script_path
        self.user_prompt = user_prompt

    def run(self):
        try:
            cwd = os.path.dirname(self.script_path)
            proc = subprocess.Popen([sys.executable, self.script_path],
                                    cwd=cwd, stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            try:
                stdout, _ = proc.communicate(self.user_prompt + "\n", timeout=None)
            except Exception:
                try:
                    if proc.stdin:
                        proc.stdin.write(self.user_prompt + "\n")
                        proc.stdin.flush()
                        proc.stdin.close()
                except Exception:
                    pass
                stdout = proc.stdout.read() if proc.stdout is not None else ""
            if stdout is None:
                stdout = ""
            self.output_signal.emit(stdout)
        except Exception as e:
            tb = traceback.format_exc()
            self.output_signal.emit(f"Error: {e}\n{tb}")
        finally:
            self.finished_signal.emit()


class AutomationRunnerThread(QThread):
    """Dedicated thread for running automation script"""
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(int)  # Emits return code

    def __init__(self, script_path, working_dir):
        super().__init__()
        self.script_path = script_path
        self.working_dir = working_dir

    def run(self):
        try:
            process = subprocess.Popen(
                ["bash", self.script_path],
                cwd=self.working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            # Stream stdout
            for line in iter(process.stdout.readline, ''):
                if line:
                    self.output_signal.emit(line.rstrip())

            # Stream stderr
            for line in iter(process.stderr.readline, ''):
                if line:
                    self.output_signal.emit(f"❌ {line.rstrip()}")

            process.stdout.close()
            process.stderr.close()
            return_code = process.wait()
            self.finished_signal.emit(return_code)

        except Exception as e:
            self.output_signal.emit(f"❌ Exception: {str(e)}")
            self.finished_signal.emit(-1)


class VisioGNS3App(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_file = None
        self.automation_completed = False
        self.server_configured = False
        self.server_ip = ""
        self.server_port = ""
        self.automation_runner = None  # Store thread reference
        self.initUI()

    def initUI(self):
        self.setWindowTitle("INDA - Intelligent Network Design Automation")
        self.setGeometry(100, 50, 1100, 900)
        self.setMinimumSize(1050, 850)
        
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(15, 23, 42))
        self.setPalette(palette)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.stacked_widget = QStackedWidget()
        self.setup_page = self.create_setup_page()
        self.landing_page = self.create_landing_page()
        self.console_page = self.create_console_page()
        self.chatbot_page = self.create_chatbot_page()

        self.stacked_widget.addWidget(self.setup_page)
        self.stacked_widget.addWidget(self.landing_page)
        self.stacked_widget.addWidget(self.console_page)
        self.stacked_widget.addWidget(self.chatbot_page)

        main_layout.addWidget(self.stacked_widget)
        self.setLayout(main_layout)

    def add_shadow(self, widget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(6)
        shadow.setColor(QColor(0, 0, 0, 80))
        widget.setGraphicsEffect(shadow)

    def create_setup_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(60, 40, 60, 60)
        layout.setSpacing(30)
        layout.addStretch(1)

        # Brand section
        logo = QLabel("🌐")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("font-size: 72px;")

        title = QLabel("INDA")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #60A5FA; font-size: 56px; font-weight: 800; letter-spacing: 2px;")

        subtitle = QLabel("Intelligent Network Design Automation")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #94A3B8; font-size: 18px; font-weight: 500; letter-spacing: 1px;")

        layout.addWidget(logo)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(20)

        # Setup container
        setup_container = QFrame()
        setup_container.setMaximumWidth(600)
        setup_container.setMinimumWidth(500)
        setup_container.setStyleSheet("""
            QFrame {
                background: rgba(30, 41, 59, 0.7);
                border-radius: 24px;
            }
        """)
        self.add_shadow(setup_container)

        setup_layout = QVBoxLayout()
        setup_layout.setContentsMargins(60, 40, 60, 40)
        setup_layout.setSpacing(25)

        # IP Label
        ip_label = QLabel("🔗  GNS3 Server IP")
        ip_label.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: 600;")

        self.setup_input_ip = QLineEdit()
        self.setup_input_ip.setPlaceholderText("e.g., 127.0.0.1")
        self.setup_input_ip.setText("127.0.0.1")
        self.setup_input_ip.setMinimumHeight(50)
        self.setup_input_ip.setStyleSheet("""
            QLineEdit {
                background: rgba(15, 23, 42, 0.8); 
                color: #F8FAFC;
                border: 2px solid rgba(100, 116, 139, 0.3); 
                border-radius: 12px;
                padding: 0 18px; 
                font-size: 15px;
            }
            QLineEdit:focus {
                border: 2px solid #60A5FA;
            }
        """)

        # Port Label
        port_label = QLabel("⚡  GNS3 Server Port")
        port_label.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: 600;")

        self.setup_input_port = QLineEdit()
        self.setup_input_port.setPlaceholderText("e.g., 3080")
        self.setup_input_port.setText("3080")
        self.setup_input_port.setMinimumHeight(50)
        self.setup_input_port.setStyleSheet("""
            QLineEdit {
                background: rgba(15, 23, 42, 0.8); 
                color: #F8FAFC;
                border: 2px solid rgba(100, 116, 139, 0.3); 
                border-radius: 12px;
                padding: 0 18px; 
                font-size: 15px;
            }
            QLineEdit:focus {
                border: 2px solid #60A5FA;
            }
        """)

        self.setup_status = QLabel("")
        self.setup_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setup_status.setMinimumHeight(30)
        self.setup_status.setWordWrap(True)
        self.setup_status.setStyleSheet("color: #A0AEC0; font-size: 13px;")

        # Continue Button
        continue_btn = QPushButton("Continue to Dashboard →")
        continue_btn.setMinimumHeight(56)
        continue_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3B82F6, stop:1 #8B5CF6);
                color: #FFFFFF;
                border: none;
                border-radius: 14px;
                font-size: 16px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #7C3AED);
            }
        """)
        continue_btn.clicked.connect(self.complete_setup)
        continue_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        setup_layout.addWidget(ip_label)
        setup_layout.addWidget(self.setup_input_ip)
        setup_layout.addWidget(port_label)
        setup_layout.addWidget(self.setup_input_port)
        setup_layout.addWidget(self.setup_status)
        setup_layout.addWidget(continue_btn)
        setup_container.setLayout(setup_layout)

        container_layout = QHBoxLayout()
        container_layout.addStretch()
        container_layout.addWidget(setup_container)
        container_layout.addStretch()
        layout.addLayout(container_layout)
        layout.addStretch(2)

        page.setLayout(layout)
        return page

    def complete_setup(self):
        ip = self.setup_input_ip.text().strip()
        port = self.setup_input_port.text().strip()
        
        self.setup_status.setText("")
        self.setup_status.setStyleSheet("")
        
        if not ip or not port:
            self.setup_status.setText("⚠️  Enter both IP and port")
            self.setup_status.setStyleSheet("""
                QLabel {
                    color: #F87171;
                    background: rgba(248, 113, 113, 0.1);
                    padding: 8px;
                    border-radius: 8px;
                    border: 1px solid rgba(248, 113, 113, 0.3);
                }
            """)
            return
        
        try:
            self.server_ip = ip
            self.server_port = port
            self.save_gns3_config(ip, port)
            self.setup_status.setText("✅ Saved! Redirecting...")
            self.setup_status.setStyleSheet("""
                QLabel {
                    color: #4ADE80;
                    background: rgba(74, 222, 128, 0.1);
                    padding: 8px;
                    border-radius: 8px;
                    border: 1px solid rgba(74, 222, 128, 0.3);
                }
            """)
            self.server_configured = True
            QTimer.singleShot(600, self.show_landing_page)
        except Exception as e:
            self.setup_status.setText(f"❌ Error: {str(e)[:50]}")
            self.setup_status.setStyleSheet("""
                QLabel {
                    color: #F87171;
                    background: rgba(248, 113, 113, 0.1);
                    padding: 8px;
                    border-radius: 8px;
                    border: 1px solid rgba(248, 113, 113, 0.3);
                }
            """)

    def create_landing_page(self):
        page = QWidget()
        page.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0F172A, stop:1 #1E293B);")
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(60, 50, 60, 50)
        main_layout.setSpacing(40)

        title = QLabel("INDA Dashboard")
        title.setStyleSheet("color: #F8FAFC; font-size: 42px; font-weight: 800; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Choose your workflow")
        subtitle.setStyleSheet("color: #94A3B8; font-size: 17px; font-weight: 500; background: transparent;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        main_layout.addStretch(1)
        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)
        main_layout.addSpacing(20)

        cards_container = QWidget()
        cards_container.setStyleSheet("background: transparent;")
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(30)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        
        cards_layout.addWidget(self.create_card("🤖", "Instruction Orchestrator",
                                            "Natural language topology generation", "#3B82F6", self.show_chatbot_page))
        cards_layout.addWidget(self.create_card("📊", "Topology Interpreter",
                                            "Upload Visio/XML/SVG files", "#8B5CF6", self.show_console_page))
        
        cards_container.setLayout(cards_layout)
        
        center_layout = QHBoxLayout()
        center_layout.addStretch()
        center_layout.addWidget(cards_container)
        center_layout.addStretch()
        
        main_layout.addLayout(center_layout)
        main_layout.addStretch(2)
        
        page.setLayout(main_layout)
        return page

    def create_card(self, emoji, title, desc, color, callback):
        card = QFrame()
        card.setMinimumHeight(320)
        card.setMinimumWidth(400)
        card.setStyleSheet(f"""
            QFrame {{
                background: rgba(30, 41, 59, 0.6);
                border: 1px solid rgba(148, 163, 184, 0.2);
                border-radius: 20px;
            }}
            QFrame:hover {{
                background: rgba(30, 41, 59, 0.8);
                border: 1px solid {color};
            }}
        """)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_shadow(card)
        
        content_label = QLabel(f"""
            <div align="center">
                <div style="font-size: 48px;">{emoji}</div>
                <div style="color: #F8FAFC; font-size: 24px; font-weight: 700; margin: 20px 0;">{title}</div>
                <div style="color: #94A3B8; font-size: 15px; line-height: 1.6; margin-bottom: 30px;">{desc}</div>
                <div style="color: {color}; font-size: 32px;">→</div>
            </div>
        """)
        content_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_label.setWordWrap(True)
        content_label.setStyleSheet("background: transparent; padding: 40px;")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(content_label)
        
        card.setLayout(layout)
        card.mousePressEvent = lambda e: callback()
        return card

    def create_chatbot_page(self):
        page = QWidget()
        page.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0F172A, stop:1 #1E293B);")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QFrame()
        header.setStyleSheet("background: rgba(30, 41, 59, 0.95); padding: 24px 40px; border-bottom: 1px solid rgba(148, 163, 184, 0.2);")
        h_layout = QHBoxLayout()

        back_btn = QPushButton("← Back")
        back_btn.setFixedHeight(44)
        back_btn.setStyleSheet("""
            QPushButton {
                background: rgba(59, 130, 246, 0.1); 
                color: #60A5FA;
                border: 1px solid rgba(59, 130, 246, 0.3); 
                border-radius: 22px; 
                font-size: 14px;
                font-weight: 600;
                padding: 0 20px;
            }
            QPushButton:hover {
                background: rgba(59, 130, 246, 0.2);
                border: 1px solid #60A5FA;
            }
        """)
        back_btn.clicked.connect(self.show_landing_page)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        title = QLabel("Instruction Orchestrator")
        title.setStyleSheet("color: #F8FAFC; font-size: 26px; font-weight: 700; background: transparent;")

        badge = QLabel("● AI Active")
        badge.setStyleSheet("""
            color: #4ADE80; 
            font-size: 13px; 
            font-weight: 600;
            padding: 6px 14px;
            background: rgba(74, 222, 128, 0.1); 
            border-radius: 12px;
        """)

        h_layout.addWidget(back_btn)
        h_layout.addSpacing(16)
        h_layout.addWidget(title)
        h_layout.addStretch()
        h_layout.addWidget(badge)
        header.setLayout(h_layout)

        # Content
        content = QWidget()
        c_layout = QVBoxLayout()
        c_layout.setContentsMargins(50, 30, 50, 40)
        c_layout.setSpacing(24)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setMinimumHeight(500)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background: rgba(15, 23, 42, 0.5); 
                color: #E2E8F0;
                border: 1px solid rgba(100, 116, 139, 0.3); 
                border-radius: 16px;
                padding: 24px; 
                font-size: 15px;
            }
            QScrollBar:vertical {
                background: rgba(30, 41, 59, 0.5);
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: rgba(100, 116, 139, 0.5);
                border-radius: 5px;
            }
        """)
        self.chat_display.setHtml("""
            <div style='color: #94A3B8;'>
                <p style='color: #60A5FA; font-weight: 700; font-size: 16px;'>🤖 AI Assistant</p>
                <p style='color: #CBD5E1; margin: 16px 0;'>Welcome! Describe your network in natural language.</p>
                    <p style='font-weight: 600; margin-bottom: 12px;'>💡 Examples:</p>
                    <ul style='color: #64748B; padding-left: 20px;'>
                        <li>"Create 3 PCs connected to a router"</li>
                        <li>"Star topology with 5 servers"</li>
                        <li>"Mesh network with 4 routers"</li>
                    </ul>
                </div>
            </div>
        """)

        # Input and buttons
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                background: rgba(30, 41, 59, 0.6); 
                border: 1px solid rgba(100, 116, 139, 0.3);
                border-radius: 16px; 
                padding: 16px;
            }
        """)
        i_layout = QHBoxLayout()

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Describe your network...")
        self.chat_input.setMinimumHeight(52)
        self.chat_input.setStyleSheet("""
            QLineEdit {
                background: rgba(15, 23, 42, 0.6); 
                color: #F8FAFC;
                border: 1px solid rgba(100, 116, 139, 0.2); 
                border-radius: 12px;
                padding: 0 20px; 
                font-size: 15px;
            }
            QLineEdit:focus {
                border: 1px solid #60A5FA;
            }
        """)
        self.chat_input.returnPressed.connect(self.send_message)

        self.run_btn = QPushButton("🚀 Run")
        self.run_btn.setMinimumHeight(52)
        self.run_btn.setMinimumWidth(100)
        self.run_btn.setStyleSheet("""
            QPushButton {
                background: rgba(139, 92, 246, 0.2);
                color: #8B5CF6;
                border: 1px solid rgba(139, 92, 246, 0.4);
                border-radius: 12px;
                font-size: 15px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: rgba(139, 92, 246, 0.3);
                border: 1px solid #8B5CF6;
            }
            QPushButton:disabled {
                background: rgba(100, 116, 139, 0.2);
                color: #64748B;
                border: 1px solid rgba(100, 116, 139, 0.3);
            }
        """)
        self.run_btn.clicked.connect(self.run_automation)
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_btn.setEnabled(False)

        send_btn = QPushButton("Send →")
        send_btn.setMinimumHeight(52)
        send_btn.setMinimumWidth(120)
        send_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3B82F6, stop:1 #8B5CF6);
                color: #FFFFFF; 
                border: none; 
                border-radius: 12px; 
                font-size: 15px; 
                font-weight: 700;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #7C3AED);
            }
        """)
        send_btn.clicked.connect(self.send_message)
        send_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        i_layout.addWidget(self.chat_input)
        i_layout.addWidget(self.run_btn)
        i_layout.addWidget(send_btn)
        input_frame.setLayout(i_layout)

        c_layout.addWidget(self.chat_display)
        c_layout.addWidget(input_frame)
        content.setLayout(c_layout)

        layout.addWidget(header)
        layout.addWidget(content)
        page.setLayout(layout)
        return page

    def send_message(self):
        msg = self.chat_input.text().strip()
        if not msg:
            return
        
        self.run_btn.setEnabled(False)
        
        self.add_chat_message("user", msg)
        self.add_chat_message("bot", "🔮 Processing your request...")
        self.chat_input.clear()
        self.chat_input.setEnabled(False)

        script_path = os.path.expanduser("~/INDA/VisioGns3/NLP1/run_pipeline.py")
        self.script_runner = ScriptRunnerThread(script_path, msg)
        self.script_runner.output_signal.connect(self.handle_script_output)
        self.script_runner.finished_signal.connect(self.on_script_completed)
        self.script_runner.start()

    def handle_script_output(self, output):
        import html
        escaped = html.escape(output)
        
        if "✅" in output or "success" in output.lower() or "completed" in output.lower():
            self.automation_completed = True
            
        formatted = f"<pre style='color: #E2E8F0; background: #1A202C; padding: 10px; border-radius: 6px;'>{escaped}</pre>"
        current = self.chat_display.toHtml()
        self.chat_display.setHtml(current.replace("🔮 Processing your request...", formatted, 1))
        self.chat_display.verticalScrollBar().setValue(self.chat_display.verticalScrollBar().maximum())

    def on_script_completed(self):
        self.chat_input.setEnabled(True)
        
        if self.automation_completed:
            self.run_btn.setEnabled(True)
            self.add_chat_message("bot", "✅ Ready to run the automation! Click the 🚀 Run button to execute.")

    def run_automation(self):
        """Function to handle the Run button click - FIXED VERSION"""
        if not self.automation_completed:
            return

        # Disable Run button during execution
        self.run_btn.setEnabled(False)

        # UI feedback
        self.add_chat_message("bot", "🚀 Running network automation...")

        # Resolve paths correctly
        gui_dir = os.path.dirname(os.path.abspath(__file__))
        visio_dir = os.path.join(gui_dir, "VisioGns3")
        script_path = os.path.join(visio_dir, "automation_instruction_orchestrator.sh")

        # Safety checks
        if not os.path.exists(script_path):
            self.add_chat_message("bot", f"❌ Script not found:\n{script_path}")
            self.run_btn.setEnabled(True)
            return

        if not os.access(script_path, os.X_OK):
            self.add_chat_message("bot", "❌ Script is not executable (chmod +x needed)")
            self.run_btn.setEnabled(True)
            return

        # Create and start the worker thread
        self.automation_runner = AutomationRunnerThread(script_path, visio_dir)
        self.automation_runner.output_signal.connect(self.on_automation_output)
        self.automation_runner.finished_signal.connect(self.on_automation_complete)
        self.automation_runner.start()

    def on_automation_output(self, line):
        """Handle output from automation thread - called via signal"""
        self.add_chat_message("bot", line)

    def on_automation_complete(self, return_code):
        """Handle automation completion - called via signal"""
        self.run_btn.setEnabled(True)
        
        if return_code == 0:
            self.add_chat_message("bot", "✅ Automation completed successfully!")
        else:
            self.add_chat_message("bot", f"❌ Automation failed with code {return_code}. Check logs above.")
        
        # Reset flag for next operation
        self.automation_completed = False

    def add_chat_message(self, role, content):
        current = self.chat_display.toHtml()
        if role == "user":
            msg = f"<div style='margin: 15px 0;'><span style='color: #68D391; font-weight: 700;'>👤 You:</span><br/><span style='color: #E2E8F0;'>{content}</span></div>"
        else:
            msg = f"<div style='margin: 15px 0;'><span style='color: #4299E1; font-weight: 700;'>🤖 Assistant:</span><br/>{content}</div>"
        self.chat_display.setHtml(current + msg)
        self.chat_display.verticalScrollBar().setValue(self.chat_display.verticalScrollBar().maximum())

    def create_console_page(self):
        page = QWidget()
        page.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0F172A, stop:1 #1E293B);")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QFrame()
        header.setStyleSheet("background: rgba(30, 41, 59, 0.95); padding: 24px 40px;")
        h_layout = QHBoxLayout()

        back_btn = QPushButton("← Back")
        back_btn.setFixedHeight(44)
        back_btn.setStyleSheet("""
            QPushButton {
                background: rgba(139, 92, 246, 0.1); 
                color: #A78BFA; 
                border: 1px solid rgba(139, 92, 246, 0.3); 
                border-radius: 22px; 
                font-size: 14px;
                font-weight: 600;
                padding: 0 20px;
            }
            QPushButton:hover {
                background: rgba(139, 92, 246, 0.2);
                border: 1px solid #A78BFA;
            }
        """)
        back_btn.clicked.connect(self.show_landing_page)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        title = QLabel("Topology Interpreter")
        title.setStyleSheet("color: #F8FAFC; font-size: 26px; font-weight: 700; background: transparent;")

        h_layout.addWidget(back_btn)
        h_layout.addSpacing(16)
        h_layout.addWidget(title)
        h_layout.addStretch()
        header.setLayout(h_layout)

        # Content
        content = QWidget()
        c_layout = QVBoxLayout()
        c_layout.setContentsMargins(50, 30, 50, 40)
        c_layout.setSpacing(24)

        upload_label = QLabel("⬆️  Upload Topology File")
        upload_label.setStyleSheet("color: #F1F5F9; font-size: 16px; font-weight: 600; background: transparent;")

        upload_frame = QFrame()
        upload_frame.setStyleSheet("""
            QFrame {
                background: rgba(30, 41, 59, 0.6); 
                border: 1px solid rgba(100, 116, 139, 0.3); 
                border-radius: 12px; 
                padding: 16px;
            }
        """)
        u_layout = QHBoxLayout()

        browse_btn = QPushButton("Browse...")
        browse_btn.setMinimumHeight(44)
        browse_btn.setStyleSheet("""
            QPushButton {
                background: #4A5568; 
                color: #FFFFFF; 
                border: none; 
                border-radius: 8px; 
                padding: 0 20px; 
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #5A6678;
            }
        """)
        browse_btn.clicked.connect(self.upload_file)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("color: #94A3B8; font-size: 14px; background: transparent;")

        u_layout.addWidget(browse_btn)
        u_layout.addWidget(self.file_label)
        u_layout.addStretch()
        upload_frame.setLayout(u_layout)

        self.run_button = QPushButton("▶  Run Automation")
        self.run_button.setMinimumHeight(56)
        self.run_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8B5CF6, stop:1 #EC4899);
                color: #FFFFFF; 
                border: none; 
                border-radius: 14px; 
                font-size: 16px; 
                font-weight: 700;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7C3AED, stop:1 #DB2777);
            }
        """)
        self.run_button.clicked.connect(self.run_script)
        self.run_button.setCursor(Qt.CursorShape.PointingHandCursor)

        console_label = QLabel(">_  Output Console")
        console_label.setStyleSheet("color: #F1F5F9; font-size: 16px; font-weight: 600; margin-top: 10px; background: transparent;")

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(450)
        self.output_text.setStyleSheet("""
            QTextEdit {
                background: rgba(15, 23, 42, 0.8); 
                color: #E2E8F0;
                border: 1px solid rgba(100, 116, 139, 0.3); 
                border-radius: 12px;
                padding: 20px; 
                font-family: 'Courier New', monospace; 
                font-size: 14px;
            }
        """)

        c_layout.addWidget(upload_label)
        c_layout.addWidget(upload_frame)
        c_layout.addWidget(self.run_button)
        c_layout.addWidget(console_label)
        c_layout.addWidget(self.output_text)
        content.setLayout(c_layout)

        layout.addWidget(header)
        layout.addWidget(content)
        page.setLayout(layout)
        return page

    def show_landing_page(self):
        self.stacked_widget.setCurrentIndex(1)

    def show_console_page(self):
        self.stacked_widget.setCurrentIndex(2)

    def show_chatbot_page(self):
        self.stacked_widget.setCurrentIndex(3)
        self.chat_input.setFocus()

    def save_gns3_config(self, ip, port):
        config_dir = os.path.dirname(GNS3_CONF_PATH)
        os.makedirs(config_dir, exist_ok=True)
        with open(GNS3_CONF_PATH, "w") as f:
            f.write(f"[Server]\nhost = {ip}\nport = {port}\n")
        subprocess.run(["pkill", "-f", "gns3server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.Popen(["gns3server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def upload_file(self):
        if self.automation_completed:
            self.output_text.clear()
            self.automation_completed = False

        file_path, _ = QFileDialog.getOpenFileName(self, "Select File", "", "All Files (*)")
        if file_path:
            if not file_path.lower().endswith((".vsdx", ".xml", ".svg")):
                QMessageBox.critical(self, "Invalid", "Only .vsdx, .xml, or .svg allowed")
                self.file_label.setText("No file selected")
                return

            self.selected_file = file_path
            self.file_label.setText(os.path.basename(file_path))
            self.file_label.setStyleSheet("color: #4ADE80; font-size: 14px;")

            upload_folder = os.path.expanduser("~/INDA/VisioGns3/uploads")
            os.makedirs(upload_folder, exist_ok=True)
            os.system(f"cp '{file_path}' '{upload_folder}'")
            self.output_text.append(f"✅ Uploaded: {os.path.basename(file_path)}")

    def run_script(self):
        if self.server_configured:
            try:
                self.save_gns3_config(self.server_ip, self.server_port)
                self.output_text.append(f"🔧 Config: {self.server_ip}:{self.server_port}")
            except Exception as e:
                self.output_text.append(f"⚠️  Config error: {e}")

        script_path = os.path.expanduser("~/INDA/VisioGns3/automation_final.sh")
        self.output_text.clear()
        self.output_text.append("🚀 Starting automation...\n")
        self.automation_completed = False

        self.worker = WorkerThread(script_path)
        self.worker.output_signal.connect(self.update_output)
        self.worker.finished_signal.connect(self.on_topology_automation_finished)
        self.worker.start()

    def update_output(self, text):
        self.output_text.append(text)
        self.output_text.ensureCursorVisible()

    def on_topology_automation_finished(self):
        self.output_text.append("\n✅ Completed!")
        self.file_label.setText("No file selected")
        self.file_label.setStyleSheet("color: #94A3B8;")
        self.automation_completed = True


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("INDA")
    font = QFont("Inter", 10)
    app.setFont(font)
    window = VisioGNS3App()
    window.show()
    sys.exit(app.exec())