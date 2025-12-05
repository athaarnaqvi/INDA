import sys
import os
import subprocess
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                              QPushButton, QLabel, QLineEdit, QTextEdit, 
                              QFileDialog, QMessageBox, QFrame, QStackedWidget, QScrollArea)
from PyQt6.QtGui import QPalette, QColor, QFont
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer

# Import NLP handler from your version
from nlp_handler import NLPHandler

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


class NLPWorkerThread(QThread):
    """Thread for processing NLP commands"""
    response_signal = pyqtSignal(dict)
    
    def __init__(self, nlp_handler, command):
        super().__init__()
        self.nlp_handler = nlp_handler
        self.command = command
    
    def run(self):
        result = self.nlp_handler.process_command(self.command)
        self.response_signal.emit(result)


class VisioGNS3App(QWidget):
    # FIX A: Add signal for NLP status updates
    nlp_status_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.selected_file = None
        self.chat_messages = []
        self.automation_completed = False
        self.server_configured = False
        self.server_ip = ""
        self.server_port = ""
        
        # Initialize NLP handler
        self.nlp_handler = None
        self.nlp_loading = False
        
        # FIX B: Connect signal in constructor
        self.nlp_status_signal.connect(self.update_chatbot_status)
        
        self.initUI()
        
        # Load NLP model in background
        self.load_nlp_model()

    def load_nlp_model(self):
        """Load NLP model in background - FIXED VERSION"""
        def init_nlp():
            try:
                model_path = os.path.expanduser("~/INDA/VisioGns3/NLP1/trained_topology_model")
                
                # Check if model directory exists
                if not os.path.exists(model_path):
                    self.nlp_status_signal.emit(f"❌ Model path not found: {model_path}")
                    self.nlp_handler = None
                    self.nlp_loading = False
                    return
                
                # FIX C: Create handler in thread, then assign to self in main thread via signal
                print(f"🔄 Loading NLP model from: {model_path}")
                handler = NLPHandler(model_path=model_path)
                
                # Update attributes - these are thread-safe as they're simple assignments
                self.nlp_handler = handler
                self.nlp_loading = False

                # FIX D: EMIT signal instead of directly updating GUI
                self.nlp_status_signal.emit("✅ NLP model loaded successfully!")
                print("✅ NLP model loaded successfully in background thread")

            except ImportError as e:
                self.nlp_handler = None
                self.nlp_loading = False
                self.nlp_status_signal.emit(f"❌ Missing dependency: {e}")
                print(f"❌ Missing dependency: {e}")
            except Exception as e:
                self.nlp_handler = None
                self.nlp_loading = False
                # FIX D: EMIT signal instead of directly updating GUI
                self.nlp_status_signal.emit(f"⚠️ Error loading NLP model: {e}")
                print(f"❌ Error loading NLP model in background thread: {e}")

        self.nlp_loading = True
        # FIX D: Initialize with thread-safe signal
        self.nlp_status_signal.emit("🔄 Loading NLP model, please wait...")
        
        from threading import Thread
        Thread(target=init_nlp, daemon=True).start()

    def update_chatbot_status(self, message):
        """Update chatbot display with status message - THREAD-SAFE"""
        # This method is called via signal, so it's already in the main thread
        if hasattr(self, 'chat_display'):
            # Use QTimer.singleShot to ensure we're in the main event loop
            QTimer.singleShot(0, lambda: self._update_chat_display(message))

    def _update_chat_display(self, message):
        """Internal method to update chat display - runs in main thread"""
        try:
            current_html = self.chat_display.toHtml()
            status_html = f"""
                <div style='margin-bottom: 15px; padding: 10px; background-color: #2D3748; border-radius: 6px;'>
                    <span style='color: #9F7AEA; font-weight: bold;'>⚙️ System:</span><br/>
                    <span style='color: #A0AEC0;'>{message}</span>
                </div>
            """
            self.chat_display.setHtml(current_html + status_html)
            scrollbar = self.chat_display.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        except Exception as e:
            print(f"Error updating chat display: {e}")

    def initUI(self):
        self.setWindowTitle("Visio to GNS3")
        self.setGeometry(100, 100, 900, 700)
        
        # Set dark mode styling
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(26, 32, 44))
        self.setPalette(palette)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Stacked widget for pages
        self.stacked_widget = QStackedWidget()
        
        # Create pages
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

    def create_setup_page(self):
        """Create initial setup page for IP and Port configuration"""
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)
        
        # Center content vertically
        layout.addStretch()
        
        # Title
        title = QLabel("🚀 Initial Setup")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            color: white;
            font-size: 42px;
            font-weight: bold;
            margin-bottom: 10px;
        """)
        
        # Subtitle
        subtitle = QLabel("Configure your GNS3 Server connection")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            color: #A0AEC0;
            font-size: 16px;
            margin-bottom: 40px;
        """)
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        
        # Setup container
        setup_container = QFrame()
        setup_container.setMaximumWidth(500)
        setup_container.setStyleSheet("""
            QFrame {
                background-color: #2D3748;
                border-radius: 12px;
                padding: 40px;
            }
        """)
        setup_layout = QVBoxLayout()
        setup_layout.setSpacing(20)
        
        # Server IP Section
        ip_label = QLabel("⚙️  GNS3 Server IP Address:")
        ip_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        
        self.setup_input_ip = QLineEdit()
        self.setup_input_ip.setPlaceholderText("e.g., 127.0.0.1")
        self.setup_input_ip.setText("127.0.0.1")
        self.setup_input_ip.setStyleSheet("""
            QLineEdit {
                background-color: #1A202C;
                color: white;
                border: 1px solid #4A5568;
                border-radius: 6px;
                padding: 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #4299E1;
            }
        """)
        
        # Server Port Section
        port_label = QLabel("🔌 GNS3 Server Port:")
        port_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold; margin-top: 10px;")
        
        self.setup_input_port = QLineEdit()
        self.setup_input_port.setPlaceholderText("e.g., 3080")
        self.setup_input_port.setText("3080")
        self.setup_input_port.setStyleSheet("""
            QLineEdit {
                background-color: #1A202C;
                color: white;
                border: 1px solid #4A5568;
                border-radius: 6px;
                padding: 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #4299E1;
            }
        """)
        
        # Status message
        self.setup_status = QLabel("")
        self.setup_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setup_status.setStyleSheet("color: #A0AEC0; font-size: 13px; margin-top: 5px;")
        
        # Continue Button
        continue_button = QPushButton("Continue to Application")
        continue_button.setStyleSheet("""
            QPushButton {
                background-color: #48BB78;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 14px;
                font-size: 15px;
                font-weight: bold;
                margin-top: 20px;
            }
            QPushButton:hover {
                background-color: #38A169;
            }
            QPushButton:pressed {
                background-color: #2F855A;
            }
        """)
        continue_button.clicked.connect(self.complete_setup)
        continue_button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        setup_layout.addWidget(ip_label)
        setup_layout.addWidget(self.setup_input_ip)
        setup_layout.addWidget(port_label)
        setup_layout.addWidget(self.setup_input_port)
        setup_layout.addWidget(self.setup_status)
        setup_layout.addWidget(continue_button)
        
        setup_container.setLayout(setup_layout)
        
        # Center the container horizontally
        container_layout = QHBoxLayout()
        container_layout.addStretch()
        container_layout.addWidget(setup_container)
        container_layout.addStretch()
        
        layout.addLayout(container_layout)
        layout.addStretch()
        
        page.setLayout(layout)
        return page

    def complete_setup(self):
        """Save configuration and proceed to landing page"""
        ip = self.setup_input_ip.text().strip()
        port = self.setup_input_port.text().strip()

        if not ip or not port:
            self.setup_status.setText("⚠️  Please enter both IP and port.")
            self.setup_status.setStyleSheet("color: #FC8181; font-size: 13px; margin-top: 5px;")
            return

        try:
            # Store IP and port for future use
            self.server_ip = ip
            self.server_port = port
            
            # Save configuration
            self.save_gns3_config(ip, port)

            self.setup_status.setText(f"✅ Configuration saved successfully!")
            self.setup_status.setStyleSheet("color: #68D391; font-size: 13px; margin-top: 5px;")

            # Mark as configured
            self.server_configured = True
            
            # Show landing page after a brief moment
            QTimer.singleShot(500, self.show_landing_page)
        
        except Exception as e:
            self.setup_status.setText(f"❌ Error: {str(e)}")
            self.setup_status.setStyleSheet("color: #FC8181; font-size: 13px; margin-top: 5px;")

    def create_landing_page(self):
        """Create the landing page with two cards"""
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)
        
        # Title
        title = QLabel(" INDA ")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            color: white;
            font-size: 42px;
            font-weight: bold;
            margin-bottom: 20px;
        """)
        
        # Subtitle
        subtitle = QLabel("Intelligent Network Design Automation")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            color: #A0AEC0;
            font-size: 16px;
            margin-bottom: 40px;
        """)
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        
        # Cards container
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)
        
        # Card 1 - Instruction Orchestrator
        card1 = self.create_card(
            "⚙️",
            "Instruction Orchestrator",
            "Describe your network in plain language and get instant topology generation",
            self.show_chatbot_page
        )
        
        # Card 2 - Topology Interpreter
        card2 = self.create_card(
            "🖥️",
            "Topology Interpreter",
            "Upload Visio/XML/SVG files and automate GNS3 project creation",
            self.show_console_page
        )
        
        cards_layout.addWidget(card1)
        cards_layout.addWidget(card2)
        
        layout.addLayout(cards_layout)
        layout.addStretch()
        
        page.setLayout(layout)
        return page

    def create_card(self, emoji, title, description, callback):
        """Create a styled card widget"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #2D3748;
                border-radius: 12px;
                padding: 30px;
            }
        """)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        
        card_layout = QVBoxLayout()
        card_layout.setSpacing(15)
        
        # Emoji
        emoji_label = QLabel(emoji)
        emoji_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        emoji_label.setStyleSheet("font-size: 48px;")
        
        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            color: white;
            font-size: 20px;
            font-weight: bold;
        """)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            color: #A0AEC0;
            font-size: 14px;
        """)
        
        card_layout.addWidget(emoji_label)
        card_layout.addWidget(title_label)
        card_layout.addWidget(desc_label)
        card_layout.addStretch()
        
        card.setLayout(card_layout)
        
        # Make card clickable
        card.mousePressEvent = lambda e: callback()
        
        return card

    def create_chatbot_page(self):
        """Create the chatbot interface page"""
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setStyleSheet("background-color: #1A202C; padding: 20px;")
        header_layout = QHBoxLayout()
        
        back_button = QPushButton("← Back to Home")
        back_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #63B3ED;
                border: none;
                font-size: 14px;
                text-align: left;
                padding: 5px;
            }
            QPushButton:hover {
                color: #90CDF4;
            }
        """)
        back_button.clicked.connect(self.show_landing_page)
        back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        title = QLabel("Instruction Orchestrator Console")
        title.setStyleSheet("""
            color: white;
            font-size: 24px;
            font-weight: bold;
        """)
        
        header_layout.addWidget(back_button)
        header_layout.addStretch()
        header_layout.addWidget(title)
        header_layout.addStretch()
        header.setLayout(header_layout)
        
        # Content area
        content = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(40, 30, 40, 30)
        content_layout.setSpacing(20)
        
        # Welcome message
        welcome_label = QLabel("💬 Describe your network topology in natural language")
        welcome_label.setStyleSheet("""
            color: #A0AEC0;
            font-size: 14px;
            margin-bottom: 10px;
        """)
        
        # Chat display area
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #1A202C;
                color: #E2E8F0;
                border: 1px solid #2D3748;
                border-radius: 8px;
                padding: 20px;
                font-size: 14px;
                line-height: 1.6;
            }
        """)
        self.chat_display.setMinimumHeight(400)
        
        # Add initial welcome message
        self.chat_display.setHtml("""
            <div style='color: #A0AEC0; margin-bottom: 15px;'>
                <span style='color: #4299E1; font-weight: bold;'>🤖 Assistant:</span><br/>
                Hello! I'm your Network Topology AI. I can generate structured network topologies from your descriptions.<br/><br/>
                <b>Try asking me:</b>
                <ul style='margin-top: 10px; color: #718096;'>
                    <li>"Create a network with 3 PCs connected to a router"</li>
                    <li>"Design a topology with PC1, PC2 and Switch1"</li>
                    <li>"Build a simple network with 2 computers and 1 router"</li>
                    <li>Type "help" for more examples</li>
                </ul>
            </div>
        """)
        
        # NLP loading status will be updated via signal
        
        # Input area container
        input_container = QFrame()
        input_container.setStyleSheet("""
            QFrame {
                background-color: #2D3748;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(10)
        
        # Chat input field
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Describe your network topology...")
        self.chat_input.setStyleSheet("""
            QLineEdit {
                background-color: #1A202C;
                color: white;
                border: 1px solid #4A5568;
                border-radius: 6px;
                padding: 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #4299E1;
            }
        """)
        self.chat_input.returnPressed.connect(self.send_message)
        
        # Send button
        send_button = QPushButton("Send")
        send_button.setStyleSheet("""
            QPushButton {
                background-color: #4299E1;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3182CE;
            }
            QPushButton:pressed {
                background-color: #2C5282;
            }
        """)
        send_button.clicked.connect(self.send_message)
        send_button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        input_layout.addWidget(self.chat_input)
        input_layout.addWidget(send_button)
        input_container.setLayout(input_layout)
        
        # Add all widgets to content layout
        content_layout.addWidget(welcome_label)
        content_layout.addWidget(self.chat_display)
        content_layout.addWidget(input_container)
        
        content.setLayout(content_layout)
        
        # Add header and content to page
        layout.addWidget(header)
        layout.addWidget(content)
        
        page.setLayout(layout)
        return page

    def send_message(self):
        """Handle sending a message in the chatbot interface"""
        message = self.chat_input.text().strip()
        
        if not message:
            return
        
        # Check if NLP is still loading
        if self.nlp_loading:
            self.add_chat_message("user", message)
            self.add_chat_message("bot", "⏳ NLP model is still loading. Please wait a moment...")
            self.chat_input.clear()
            return
        
        # Check if NLP handler is ready
        if self.nlp_handler is None:
            self.add_chat_message("user", message)
            self.add_chat_message("bot", "❌ NLP model is not available. Please check the model path.")
            self.chat_input.clear()
            return
        
        # Add user message
        self.add_chat_message("user", message)
        
        # Add loading indicator
        self.add_chat_message("bot", "🔮 Processing your request...")
        
        # Clear input
        self.chat_input.clear()
        self.chat_input.setEnabled(False)
        
        # Process in background thread
        self.nlp_worker = NLPWorkerThread(self.nlp_handler, message)
        self.nlp_worker.response_signal.connect(self.handle_nlp_response)
        self.nlp_worker.start()
    
    def handle_nlp_response(self, result):
        """Handle NLP response from worker thread - FIXED for thread safety"""
        # Use QTimer.singleShot to ensure GUI update happens in main thread
        QTimer.singleShot(0, lambda: self._update_nlp_response(result))
    
    def _update_nlp_response(self, result):
        """Update NLP response in main thread"""
        try:
            # Remove loading message
            html = self.chat_display.toHtml()
            html = html.replace("🔮 Processing your request...", result.get('message', 'No response'))
            self.chat_display.setHtml(html)
            
            # Scroll to bottom
            scrollbar = self.chat_display.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
            # Re-enable input
            self.chat_input.setEnabled(True)
            self.chat_input.setFocus()
        except Exception as e:
            print(f"Error updating NLP response: {e}")
            self.chat_input.setEnabled(True)
            self.chat_input.setFocus()
    
    def add_chat_message(self, role, content):
        """Add a message to the chat display"""
        try:
            current_html = self.chat_display.toHtml()
            
            if role == "user":
                message_html = f"""
                    <div style='margin-bottom: 15px;'>
                        <span style='color: #68D391; font-weight: bold;'>👤 You:</span><br/>
                        <span style='color: #E2E8F0;'>{content}</span>
                    </div>
                """
            else:  # bot
                message_html = f"""
                    <div style='margin-bottom: 15px;'>
                        <span style='color: #4299E1; font-weight: bold;'>🤖 Assistant:</span><br/>
                        {content}
                    </div>
                """
            
            self.chat_display.setHtml(current_html + message_html)
            
            # Scroll to bottom
            scrollbar = self.chat_display.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        except Exception as e:
            print(f"Error adding chat message: {e}")

    def create_console_page(self):
        """Create the automation console page"""
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setStyleSheet("background-color: #1A202C; padding: 20px;")
        header_layout = QHBoxLayout()
        
        back_button = QPushButton("← Back to Home")
        back_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #63B3ED;
                border: none;
                font-size: 14px;
                text-align: left;
                padding: 5px;
            }
            QPushButton:hover {
                color: #90CDF4;
            }
        """)
        back_button.clicked.connect(self.show_landing_page)
        back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        title = QLabel("Topology Interpreter Console")
        title.setStyleSheet("""
            color: white;
            font-size: 24px;
            font-weight: bold;
        """)
        
        header_layout.addWidget(back_button)
        header_layout.addStretch()
        header_layout.addWidget(title)
        header_layout.addStretch()
        header.setLayout(header_layout)
        
        # Content area
        content = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(40, 30, 40, 30)
        content_layout.setSpacing(20)
        
        # Server Configuration Status
        if self.server_configured:
            config_label = QLabel(f"⚙️  Server Configured: {self.server_ip}:{self.server_port}")
            config_label.setStyleSheet("""
                color: #68D391;
                font-size: 13px;
                padding: 8px;
                background-color: #2D3748;
                border-radius: 4px;
                margin-bottom: 10px;
            """)
            content_layout.addWidget(config_label)
        else:
            config_label = QLabel("⚠️  Server not configured. Please set up from Home page.")
            config_label.setStyleSheet("""
                color: #FC8181;
                font-size: 13px;
                padding: 8px;
                background-color: #2D3748;
                border-radius: 4px;
                margin-bottom: 10px;
            """)
            content_layout.addWidget(config_label)
        
        # Upload File Section
        upload_label = QLabel("⬆️  Upload Topology File")
        upload_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        
        upload_container = QFrame()
        upload_container.setStyleSheet("""
            QFrame {
                background-color: #2D3748;
                border: 1px solid #4A5568;
                border-radius: 6px;
                padding: 12px;
            }
        """)
        upload_layout = QHBoxLayout()
        upload_layout.setContentsMargins(0, 0, 0, 0)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.setStyleSheet("""
            QPushButton {
                background-color: #4A5568;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #5A6678;
            }
        """)
        self.browse_button.clicked.connect(self.upload_file)
        self.browse_button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.file_label = QLabel("No file selected.")
        self.file_label.setStyleSheet("color: #A0AEC0; font-size: 13px;")
        
        upload_layout.addWidget(self.browse_button)
        upload_layout.addWidget(self.file_label)
        upload_layout.addStretch()
        upload_container.setLayout(upload_layout)
        
        # Run Automation Button
        self.run_button = QPushButton("▶  Run Automation")
        self.run_button.setStyleSheet("""
            QPushButton {
                background-color: #ED8936;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 14px;
                font-size: 15px;
                font-weight: bold;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #DD6B20;
            }
            QPushButton:pressed {
                background-color: #C05621;
            }
        """)
        self.run_button.clicked.connect(self.run_script)
        self.run_button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Output Console Section
        console_label = QLabel(">_  Output Console")
        console_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold; margin-top: 10px;")
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("Ready for commands...")
        self.output_text.setStyleSheet("""
            QTextEdit {
                background-color: #1A202C;
                color: #E2E8F0;
                border: 1px solid #2D3748;
                border-radius: 6px;
                padding: 15px;
                font-family: 'Courier New', monospace;
                font-size: 13px;
            }
        """)
        self.output_text.setMinimumHeight(400)
        
        # Add all widgets to content layout
        content_layout.addWidget(upload_label)
        content_layout.addWidget(upload_container)
        content_layout.addWidget(self.run_button)
        content_layout.addWidget(console_label)
        content_layout.addWidget(self.output_text)
        
        content.setLayout(content_layout)
        
        # Add header and content to page
        layout.addWidget(header)
        layout.addWidget(content)
        
        page.setLayout(layout)
        return page

    def show_landing_page(self):
        """Switch to landing page"""
        self.stacked_widget.setCurrentIndex(1)

    def show_console_page(self):
        """Switch to console page"""
        self.stacked_widget.setCurrentIndex(2)

    def show_chatbot_page(self):
        """Switch to chatbot page"""
        self.stacked_widget.setCurrentIndex(3)
        self.chat_input.setFocus()

    def save_gns3_config(self, ip, port):
        """Save GNS3 configuration and restart server"""
        try:
            # Ensure config directory exists
            config_dir = os.path.dirname(GNS3_CONF_PATH)
            os.makedirs(config_dir, exist_ok=True)
            
            # Save configuration
            with open(GNS3_CONF_PATH, "w") as file:
                file.write(f"[Server]\nhost = {ip}\nport = {port}\n")

            # Restart GNS3 server
            subprocess.run(["pkill", "-f", "gns3server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.Popen(["gns3server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            return True
        except Exception as e:
            raise e

    def upload_file(self):
        """Handle file upload"""
        if self.automation_completed:
            self.output_text.clear()
            self.output_text.append("🧹 Logs cleared for new upload.")
            self.automation_completed = False

        file_path, _ = QFileDialog.getOpenFileName(self, "Select a File", "", "All Files (*)")
        if file_path:
            valid_extensions = (".vsdx", ".xml", ".svg")
            if not file_path.lower().endswith(valid_extensions):
                QMessageBox.critical(self, "Invalid File", 
                                    "❌ Only .vsdx, .xml, or .svg files are allowed.\nPlease upload a valid file.")
                self.file_label.setText("No file selected.")
                self.file_label.setStyleSheet("color: #A0AEC0; font-size: 13px;")
                self.output_text.append("❌ Invalid file type. Please upload a .vsdx, .xml, or .svg file.")
                self.selected_file = None
                return

            self.selected_file = file_path
            filename = os.path.basename(file_path)
            self.file_label.setText(filename)
            self.file_label.setStyleSheet("color: #68D391; font-size: 13px;")
            
            upload_folder = os.path.expanduser("~/INDA/VisioGns3/uploads")
            os.makedirs(upload_folder, exist_ok=True)
            os.system(f"cp '{file_path}' '{upload_folder}'")
            self.output_text.append(f"✅ File uploaded: {filename}")

    def run_script(self):
        """Run automation script"""
        # Re-apply server configuration before running automation
        if self.server_configured and self.server_ip and self.server_port:
            try:
                self.save_gns3_config(self.server_ip, self.server_port)
                self.output_text.append(f"🔧 Re-applied server configuration: {self.server_ip}:{self.server_port}")
            except Exception as e:
                self.output_text.append(f"⚠️  Warning: Could not re-apply config: {e}")
        
        script_path = os.path.expanduser("~/INDA/VisioGns3/automation_final.sh")
        
        self.output_text.clear()
        self.output_text.append("🚀 Starting automation script...\n")
        self.automation_completed = False

        self.worker = WorkerThread(script_path)
        self.worker.output_signal.connect(self.update_output)
        self.worker.finished_signal.connect(self.on_automation_finished)
        self.worker.start()

    def update_output(self, text):
        """Update output console"""
        self.output_text.append(text)
        self.output_text.ensureCursorVisible()
        
    def on_automation_finished(self):
        """Handle automation completion"""
        self.output_text.append("\n✅ Automation completed successfully!")
        
        # Clear file selection
        self.selected_file = None
        self.file_label.setText("No file selected.")
        self.file_label.setStyleSheet("color: #A0AEC0; font-size: 13px;")
        
        self.output_text.append("🧹 Ready for next task.")
        self.automation_completed = True

# Run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Visio-GNS3")
    app.setDesktopFileName("visio-gns3.desktop")
    
    # Set application-wide font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = VisioGNS3App()
    window.show()
    sys.exit(app.exec())