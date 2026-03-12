"""
PyQt6 Dialog for previewing network topology before GNS3 deployment
Location: VisioGns3/preview_dialog.py
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                              QLabel, QTabWidget, QWidget, QTextEdit,
                              QMessageBox, QFileDialog, QSlider, QSpinBox,
                              QScrollArea)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QWheelEvent
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
import os
import sys
from pathlib import Path

# Add VisioGns3 to path for absolute imports
ARCH_DIR = Path(__file__).parent.absolute()
VISIO_GNS3_DIR = ARCH_DIR.parent

sys.path.insert(0, str(ARCH_DIR))
sys.path.insert(0, str(VISIO_GNS3_DIR))

from topology_visualization import TopologyVisualizer


class ZoomableSVGViewer(QWebEngineView):
    """Custom SVG viewer with native zoom support"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.zoom_level = 80  # Start at 80% to fit better
        self.min_zoom = 20
        self.max_zoom = 300
        
        # Enable settings
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.ShowScrollBars, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowGeolocationOnInsecureOrigins, False)
        
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel for zooming"""
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            zoom_step = 10
            
            if delta > 0:
                self.zoom_level = min(self.zoom_level + zoom_step, self.max_zoom)
            else:
                self.zoom_level = max(self.zoom_level - zoom_step, self.min_zoom)
            
            self.setZoomFactor(self.zoom_level / 100.0)
            event.accept()
        else:
            super().wheelEvent(event)
    
    def set_zoom(self, level: int):
        """Set zoom level"""
        self.zoom_level = max(self.min_zoom, min(level, self.max_zoom))
        self.setZoomFactor(self.zoom_level / 100.0)
    
    def fit_to_width(self):
        """Fit to available width"""
        self.set_zoom(80)
    
    def fit_to_height(self):
        """Fit to available height"""
        self.set_zoom(70)


class TopologyPreviewDialog(QDialog):
    """
    PyQt6 Dialog for previewing network topology before GNS3 deployment
    """
    
    def __init__(self, machines_yaml_path: str, connections_json_path: str, 
                 parent=None):
        super().__init__(parent)
        
        self.machines_yaml_path = machines_yaml_path
        self.connections_json_path = connections_json_path
        self.visualizer = TopologyVisualizer(
            machines_yaml_path, 
            connections_json_path,
            output_dir=os.path.dirname(machines_yaml_path)
        )
        
        self.setWindowTitle("🖼️ Network Topology Preview")
        self.setGeometry(0, 0, 1800, 1100)
        
        # Center on screen
        screen = self.screen()
        if screen:
            geometry = screen.availableGeometry()
            self.move(geometry.center() - self.frameGeometry().center())
        
        self.setup_ui()
        self.load_preview()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        main_layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("🖼️ Network Topology Preview - Confirm Before Deployment")
        title_font = title_label.font()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # Tab widget
        tabs = QTabWidget()
        
        # ===== SVG View Tab =====
        svg_widget = QWidget()
        svg_layout = QVBoxLayout(svg_widget)
        svg_layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Zoom label and spinbox
        zoom_label = QLabel("🔍 Zoom:")
        toolbar.addWidget(zoom_label)
        
        self.zoom_spinbox = QSpinBox()
        self.zoom_spinbox.setMinimum(20)
        self.zoom_spinbox.setMaximum(300)
        self.zoom_spinbox.setValue(80)
        self.zoom_spinbox.setSuffix("%")
        self.zoom_spinbox.setMaximumWidth(80)
        self.zoom_spinbox.valueChanged.connect(self.on_zoom_changed)
        toolbar.addWidget(self.zoom_spinbox)
        
        # Zoom slider
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setMinimum(20)
        self.zoom_slider.setMaximum(300)
        self.zoom_slider.setValue(80)
        self.zoom_slider.setMaximumWidth(200)
        self.zoom_slider.sliderMoved.connect(self.on_slider_moved)
        toolbar.addWidget(self.zoom_slider)
        
        # Buttons
        zoom_in_btn = QPushButton("➕")
        zoom_in_btn.setMaximumWidth(50)
        zoom_in_btn.clicked.connect(self.zoom_in)
        toolbar.addWidget(zoom_in_btn)
        
        zoom_out_btn = QPushButton("➖")
        zoom_out_btn.setMaximumWidth(50)
        zoom_out_btn.clicked.connect(self.zoom_out)
        toolbar.addWidget(zoom_out_btn)
        
        reset_btn = QPushButton("⟲ Reset")
        reset_btn.setMaximumWidth(80)
        reset_btn.clicked.connect(self.reset_zoom)
        toolbar.addWidget(reset_btn)
        
        fit_btn = QPushButton("⤢ Fit")
        fit_btn.setMaximumWidth(70)
        fit_btn.clicked.connect(self.fit_to_screen)
        toolbar.addWidget(fit_btn)
        
        toolbar.addStretch()
        
        help_text = QLabel("💡 Ctrl+Scroll to zoom")
        help_text.setStyleSheet("color: #999; font-size: 9px;")
        toolbar.addWidget(help_text)
        
        svg_layout.addLayout(toolbar)
        
        # SVG Viewer
        self.svg_viewer = ZoomableSVGViewer()
        svg_layout.addWidget(self.svg_viewer)
        
        tabs.addTab(svg_widget, "📊 Visual Diagram (SVG)")
        
        # ===== XML View Tab =====
        xml_widget = QWidget()
        xml_layout = QVBoxLayout(xml_widget)
        
        self.xml_viewer = QTextEdit()
        self.xml_viewer.setReadOnly(True)
        self.xml_viewer.setFont(self._get_monospace_font())
        xml_layout.addWidget(self.xml_viewer)
        
        tabs.addTab(xml_widget, "📋 XML Structure")
        
        # ===== Summary Tab =====
        summary_widget = QWidget()
        summary_layout = QVBoxLayout(summary_widget)
        
        self.summary_viewer = QTextEdit()
        self.summary_viewer.setReadOnly(True)
        self.summary_viewer.setFont(self._get_monospace_font())
        summary_layout.addWidget(self.summary_viewer)
        
        tabs.addTab(summary_widget, "📈 Topology Summary")
        
        main_layout.addWidget(tabs)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        export_svg_btn = QPushButton("💾 Export SVG")
        export_svg_btn.clicked.connect(self.export_svg)
        button_layout.addWidget(export_svg_btn)
        
        export_xml_btn = QPushButton("💾 Export XML")
        export_xml_btn.clicked.connect(self.export_xml)
        button_layout.addWidget(export_xml_btn)
        
        button_layout.addStretch()
        
        confirm_btn = QPushButton("✅ Confirm & Deploy")
        confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
                border: none;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        confirm_btn.clicked.connect(self.confirm_deployment)
        button_layout.addWidget(confirm_btn)
        
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
                border: none;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
    
    def on_zoom_changed(self, value: int):
        """Handle spinbox zoom change"""
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(value)
        self.zoom_slider.blockSignals(False)
        self.svg_viewer.set_zoom(value)
    
    def on_slider_moved(self, value: int):
        """Handle slider zoom change"""
        self.zoom_spinbox.blockSignals(True)
        self.zoom_spinbox.setValue(value)
        self.zoom_spinbox.blockSignals(False)
        self.svg_viewer.set_zoom(value)
    
    def zoom_in(self):
        """Zoom in"""
        new_zoom = min(self.zoom_spinbox.value() + 10, 300)
        self.zoom_spinbox.setValue(new_zoom)
    
    def zoom_out(self):
        """Zoom out"""
        new_zoom = max(self.zoom_spinbox.value() - 10, 20)
        self.zoom_spinbox.setValue(new_zoom)
    
    def reset_zoom(self):
        """Reset to 80%"""
        self.zoom_spinbox.setValue(80)
    
    def fit_to_screen(self):
        """Fit to screen"""
        self.zoom_spinbox.setValue(75)
    
# Replace the load_preview method:

    def load_preview(self):
        """Load preview"""
        try:
            summary = self.visualizer.get_topology_summary()
            self._display_summary(summary)
            
            self.visualizer.parser.parse_yaml_machines()
            self.visualizer.parser.parse_json_connections()
            
            from topology_visualization import SVGGenerator
            svg_gen = SVGGenerator(self.visualizer.parser.nodes, 
                                  self.visualizer.parser.connections,
                                  title="GNS3 Network Topology")
            svg_content = svg_gen.generate()
            
            # HTML with responsive SVG container
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    * {{
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }}
                    
                    html, body {{
                        width: 100%;
                        height: 100%;
                        background: white;
                    }}
                    
                    body {{
                        display: flex;
                        justify-content: center;
                        align-items: flex-start;
                        overflow: auto;
                        padding: 20px;
                    }}
                    
                    #svg-wrapper {{
                        background: white;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    }}
                    
                    svg {{
                        display: block;
                        width: 100%;
                        height: auto;
                        max-width: 1400px;
                    }}
                </style>
            </head>
            <body>
                <div id="svg-wrapper">
                    {svg_content}
                </div>
            </body>
            </html>
            """
            
            self.svg_viewer.setHtml(html)
            # Start at 60% to fit most content
            QTimer.singleShot(300, lambda: self.zoom_spinbox.setValue(60))
            
            from topology_visualization import XMLGenerator
            xml_gen = XMLGenerator(self.visualizer.parser.nodes,
                                  self.visualizer.parser.connections)
            self.xml_viewer.setPlainText(xml_gen.generate())
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to load preview: {str(e)}")
    
    def _display_summary(self, summary: dict):
        """Display summary"""
        text = f"""
╔════════════════════════════════════════════════════════════════╗
║              NETWORK TOPOLOGY SUMMARY                          ║
╚════════════════════════════════════════════════════════════════╝

📊 STATISTICS
─────────────────────────────────────────────────────────────────
  Total Devices:        {summary['total_devices']}
  Total Connections:    {summary['total_connections']}

🖥️  DEVICE BREAKDOWN
─────────────────────────────────────────────────────────────────
"""
        for device_type, count in summary['device_types'].items():
            text += f"  {device_type:.<30} {count:>3}\n"
        
        text += f"""
📍 DEVICES
─────────────────────────────────────────────────────────────────
"""
        for device in summary['devices']:
            text += f"  • {device}\n"
        
        text += f"""
🔗 CONNECTIONS ({len(summary['connections'])} total)
──────��──────────────────────────────────────────────────────────
"""
        for i, conn in enumerate(summary['connections'], 1):
            text += f"  {i:2d}. {conn['from']:.<20} → {conn['to']:.<20}\n"
        
        self.summary_viewer.setPlainText(text)
    
    def export_svg(self):
        """Export SVG"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save SVG", "", "SVG Files (*.svg)"
            )
            if file_path:
                path = self.visualizer.generate_svg(os.path.basename(file_path))
                QMessageBox.information(self, "Success", f"Saved to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    def export_xml(self):
        """Export XML"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save XML", "", "XML Files (*.xml)"
            )
            if file_path:
                path = self.visualizer.generate_xml(os.path.basename(file_path))
                QMessageBox.information(self, "Success", f"Saved to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    def confirm_deployment(self):
        """Confirm deployment"""
        reply = QMessageBox.question(
            self, "Confirm",
            "Deploy to GNS3?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.accept()
    
    @staticmethod
    def _get_monospace_font():
        """Get monospace font"""
        font = QFont()
        font.setFamily("Courier New")
        font.setPointSize(9)
        return font