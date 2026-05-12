from __future__ import annotations
import sys
import os
import subprocess
import traceback
import math
import random
from PyQt6.QtWidgets import (QApplication, QWidget, QDialog, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QLineEdit, QTextEdit,
                              QFileDialog, QMessageBox, QFrame, QStackedWidget,
                              QGraphicsDropShadowEffect, QSpinBox, QComboBox, QCheckBox, QScrollArea, QGraphicsOpacityEffect, QSizePolicy)
from PyQt6.QtGui import QPalette, QColor, QFont, QPainter, QBrush, QRadialGradient, QPen, QPainterPath, QLinearGradient
from PyQt6.QtCore import QSize, Qt, QPropertyAnimation, QThread, pyqtSignal, QTimer, pyqtProperty, QObject,QEasingCurve,QRectF, QPointF, QRectF, QRect
from typing import List, Dict, Any
from PyQt6.QtWebEngineWidgets import QWebEngineView

# GNS3 Config File Path
GNS3_CONF_PATH = os.path.expanduser("~/.config/GNS3/2.2/gns3_server.conf")


def _log_topology_history(connections: list, out_dir: str):
    """Append a timestamped entry to topology_history.json after each generation."""
    import json, datetime
    history_path = os.path.join(out_dir, "topology_history.json")
    try:
        with open(history_path) as f:
            history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        history = []
    
    history.append({
        "timestamp": datetime.datetime.now().isoformat(),
        "connection_count": len(connections)
    })
    with open(history_path, "w") as f:
        json.dump(history, f, indent=2)

class ToggleSwitch(QCheckBox):
    def __init__(self, parent=None, width=60, height=28):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self._offset = 2
        self._anim = QPropertyAnimation(self, b"offset", self)
        self._anim.setDuration(180)
        self.stateChanged.connect(self.start_transition)

    def start_transition(self, value):
        self._anim.stop()
        self._anim.setStartValue(self._offset)
        self._anim.setEndValue(self.width() - self.height() + 2 if self.isChecked() else 2)
        self._anim.start()

    @pyqtProperty(int)
    def offset(self):
        return self._offset

    @offset.setter
    def offset(self, value):
        self._offset = value
        self.update()  # repaint

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Track
        track_color = QColor("#22D3EE") if self.isChecked() else QColor("#334155")
        painter.setBrush(QBrush(track_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), self.height()/2, self.height()/2)

        # Knob
        knob_color = QColor("#F8FAFC")
        painter.setBrush(QBrush(knob_color))
        painter.drawEllipse(self._offset, 2, self.height()-4, self.height()-4)

class StyledSpinBox(QWidget):
    """Custom SpinBox with clearly visible up/down arrow buttons"""
    valueChanged = pyqtSignal(int)

    def __init__(self, minimum=0, maximum=100, value=1, parent=None):
        super().__init__(parent)
        self._min = minimum
        self._max = maximum
        self._value = value

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.line_edit = QLineEdit(str(value))
        self.line_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.line_edit.setMinimumHeight(46)
        self.line_edit.setStyleSheet("""
            QLineEdit {
                background: rgba(15, 23, 42, 0.8);
                color: #F8FAFC;
                border: 2px solid rgba(100, 116, 139, 0.3);
                border-right: none;
                border-top-left-radius: 10px;
                border-bottom-left-radius: 10px;
                font-size: 15px;
                padding: 0 8px;
            }
            QLineEdit:focus {
                border: 2px solid #22D3EE;
                border-right: none;
            }
        """)
        self.line_edit.textChanged.connect(self._on_text_changed)

        btn_container = QWidget()
        btn_container.setFixedWidth(36)
        btn_container.setMinimumHeight(46)
        btn_container.setStyleSheet("""
            QWidget {
                background: rgba(15, 23, 42, 0.8);
                border: 2px solid rgba(100, 116, 139, 0.3);
                border-left: none;
                border-top-right-radius: 10px;
                border-bottom-right-radius: 10px;
            }
        """)
        btn_layout = QVBoxLayout()
        btn_layout.setContentsMargins(2, 3, 3, 3)
        btn_layout.setSpacing(2)

        self.up_btn = QPushButton("▲")
        self.up_btn.setFixedHeight(18)
        self.up_btn.setStyleSheet("""
            QPushButton {
                background: rgba(34, 211, 238, 0.15);
                color: #22D3EE;
                border: none;
                border-radius: 4px;
                font-size: 9px;
                font-weight: 700;
                padding: 0;
            }
            QPushButton:hover { background: rgba(34, 211, 238, 0.4); }
            QPushButton:pressed { background: rgba(34, 211, 238, 0.6); }
        """)
        self.up_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.up_btn.clicked.connect(self.increment)

        self.down_btn = QPushButton("▼")
        self.down_btn.setFixedHeight(18)
        self.down_btn.setStyleSheet("""
            QPushButton {
                background: rgba(34, 211, 238, 0.15);
                color: #22D3EE;
                border: none;
                border-radius: 4px;
                font-size: 9px;
                font-weight: 700;
                padding: 0;
            }
            QPushButton:hover { background: rgba(34, 211, 238, 0.4); }
            QPushButton:pressed { background: rgba(34, 211, 238, 0.6); }
        """)
        self.down_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.down_btn.clicked.connect(self.decrement)

        btn_layout.addWidget(self.up_btn)
        btn_layout.addWidget(self.down_btn)
        btn_container.setLayout(btn_layout)

        layout.addWidget(self.line_edit)
        layout.addWidget(btn_container)
        self.setLayout(layout)

    def increment(self):
        if self._value < self._max:
            self._value += 1
            self.line_edit.setText(str(self._value))
            self.valueChanged.emit(self._value)

    def decrement(self):
        if self._value > self._min:
            self._value -= 1
            self.line_edit.setText(str(self._value))
            self.valueChanged.emit(self._value)

    def _on_text_changed(self, text):
        try:
            v = int(text)
            if self._min <= v <= self._max:
                self._value = v
                self.valueChanged.emit(self._value)
        except ValueError:
            pass

    def value(self):
        return self._value

    def setValue(self, v):
        self._value = max(self._min, min(self._max, v))
        self.line_edit.setText(str(self._value))

    def setMinimum(self, v):
        self._min = v

    def setMaximum(self, v):
        self._max = v


class StyledComboBox(QWidget):
    """QComboBox wrapper with a clearly visible ▼ arrow button"""
    currentIndexChanged = pyqtSignal(int)

    def __init__(self, items=None, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._combo = QComboBox()
        if items:
            self._combo.addItems(items)
        self._combo.setMinimumHeight(46)
        self._combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self._combo.setStyleSheet("""
            QComboBox {
                background: rgba(15, 23, 42, 0.8);
                color: #F8FAFC;
                border: 2px solid rgba(100, 116, 139, 0.3);
                border-right: none;
                border-top-left-radius: 10px;
                border-bottom-left-radius: 10px;
                padding: 0 14px;
                font-size: 15px;
            }
            QComboBox:focus {
                border: 2px solid #22D3EE;
                border-right: none;
            }
            QComboBox::drop-down { width: 0px; border: none; }
            QComboBox::down-arrow { image: none; width: 0px; }
            QComboBox QAbstractItemView {
                background: #1E293B;
                color: #F8FAFC;
                border: 1px solid rgba(6, 182, 212, 0.3);
                border-radius: 8px;
                selection-background-color: rgba(6, 182, 212, 0.25);
                outline: none;
                padding: 4px;
                font-size: 14px;
            }
            QComboBox QAbstractItemView::item {
                min-height: 32px;
                padding: 4px 12px;
            }
        """)
        self._combo.currentIndexChanged.connect(self.currentIndexChanged)

        arrow_btn = QPushButton("▼")
        arrow_btn.setFixedWidth(40)
        arrow_btn.setMinimumHeight(46)
        arrow_btn.setStyleSheet("""
            QPushButton {
                background: rgba(34, 211, 238, 0.15);
                color: #22D3EE;
                border: 2px solid rgba(100, 116, 139, 0.3);
                border-left: none;
                border-top-right-radius: 10px;
                border-bottom-right-radius: 10px;
                font-size: 12px;
                font-weight: 700;
                padding: 0;
            }
            QPushButton:hover { background: rgba(34, 211, 238, 0.35); }
            QPushButton:pressed { background: rgba(34, 211, 238, 0.55); }
        """)
        arrow_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        arrow_btn.clicked.connect(self._combo.showPopup)

        layout.addWidget(self._combo)
        layout.addWidget(arrow_btn)
        self.setLayout(layout)

    def addItems(self, items):
        self._combo.addItems(items)

    def currentText(self):
        return self._combo.currentText()

    def currentIndex(self):
        return self._combo.currentIndex()

    def setCurrentIndex(self, i):
        self._combo.setCurrentIndex(i)

    def setMinimumHeight(self, h):
        self._combo.setMinimumHeight(h)

    def setMinimumWidth(self, w):
        super().setMinimumWidth(w)


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
                    self.output_signal.emit(f"{line.rstrip()}")

            process.stdout.close()
            process.stderr.close()
            return_code = process.wait()
            self.finished_signal.emit(return_code)

        except Exception as e:
            self.output_signal.emit(f"Exception: {str(e)}")
            self.finished_signal.emit(-1)


class ScriptWorker(QObject):
    finished = pyqtSignal(int)
    error    = pyqtSignal(str)

    def __init__(self, script_path: str):
        super().__init__()
        self.script_path = script_path

    def run(self):
        try:
            result = subprocess.run(
                ["bash", self.script_path],
                check=False
            )
            self.finished.emit(result.returncode)
        except Exception as e:
            self.error.emit(str(e))


class NetworkCanvas(QWidget):
    """Draws animated nodes + connection lines + pulse rings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)

        self._tick = 0
        self._nodes = []
        self._regen_nodes()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance)
        self._timer.start(16)  # ~60 fps

    def _regen_nodes(self):
        random.seed(42)
        w, h = max(self.width(), 1200), max(self.height(), 900)
        self._nodes = [
            {
                "x": random.uniform(0.05, 0.95),
                "y": random.uniform(0.05, 0.95),
                "vx": random.uniform(-0.00008, 0.00008),
                "vy": random.uniform(-0.00008, 0.00008),
                "r": random.uniform(3, 7),
                "phase": random.uniform(0, math.pi * 2),
            }
            for _ in range(55)
        ]
        self._edges = []
        n = len(self._nodes)
        for i in range(n):
            for j in range(i + 1, n):
                dx = self._nodes[i]["x"] - self._nodes[j]["x"]
                dy = self._nodes[i]["y"] - self._nodes[j]["y"]
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < 0.22:
                    self._edges.append((i, j, dist))

    def resizeEvent(self, e):
        self._regen_nodes()

    def _advance(self):
        self._tick += 1
        for nd in self._nodes:
            nd["x"] = (nd["x"] + nd["vx"]) % 1.0
            nd["y"] = (nd["y"] + nd["vy"]) % 1.0
        if self._tick % 120 == 0:
            # Rebuild edges periodically
            self._edges = []
            n = len(self._nodes)
            for i in range(n):
                for j in range(i + 1, n):
                    dx = self._nodes[i]["x"] - self._nodes[j]["x"]
                    dy = self._nodes[i]["y"] - self._nodes[j]["y"]
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist < 0.22:
                        self._edges.append((i, j, dist))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # ── deep background gradient ──
        bg = QLinearGradient(0, 0, w, h)
        bg.setColorAt(0.0, QColor(2, 6, 23))
        bg.setColorAt(0.45, QColor(7, 15, 40))
        bg.setColorAt(1.0, QColor(3, 10, 30))
        painter.fillRect(0, 0, w, h, QBrush(bg))

        # ── subtle grid ──
        grid_pen = QPen(QColor(30, 58, 100, 35))
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)
        step = 55
        for x in range(0, w, step):
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, step):
            painter.drawLine(0, y, w, y)

        t = self._tick / 60.0  # seconds

        # ── glow orbs ──
        for ox, oy, cr, cg, cb, rad in [
            (0.15, 0.25, 0, 100, 220, 320),
            (0.80, 0.15, 80, 0, 200, 280),
            (0.50, 0.80, 0, 180, 200, 350),
            (0.90, 0.70, 0, 60, 180, 240),
        ]:
            pulse = 1.0 + 0.15 * math.sin(t * 0.7 + ox * 5)
            rr = QRadialGradient(ox * w, oy * h, rad * pulse)
            rr.setColorAt(0, QColor(cr, cg, cb, 55))
            rr.setColorAt(1, QColor(cr, cg, cb, 0))
            painter.setBrush(QBrush(rr))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(
                QRectF(ox * w - rad * pulse, oy * h - rad * pulse,
                       rad * pulse * 2, rad * pulse * 2))

        # ── edges ──
        for i, j, base_dist in self._edges:
            ni, nj = self._nodes[i], self._nodes[j]
            x1, y1 = ni["x"] * w, ni["y"] * h
            x2, y2 = nj["x"] * w, nj["y"] * h
            alpha = max(0, int(200 * (1 - base_dist / 0.22)))
            pen = QPen(QColor(0, 180, 255, alpha))
            pen.setWidthF(0.8)
            painter.setPen(pen)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

            # Traveling data packet
            frac = (t * 0.4 + (i * 0.37 + j * 0.23)) % 1.0
            px = x1 + (x2 - x1) * frac
            py = y1 + (y2 - y1) * frac
            packet_pen = QPen(QColor(0, 230, 255, 220))
            packet_pen.setWidthF(2.5)
            painter.setPen(packet_pen)
            painter.setBrush(QBrush(QColor(0, 230, 255, 220)))
            painter.drawEllipse(QPointF(px, py), 2.0, 2.0)

        # ── nodes ──
        for nd in self._nodes:
            nx, ny = nd["x"] * w, nd["y"] * h
            pulse = 1.0 + 0.3 * math.sin(t * 1.8 + nd["phase"])
            nr = nd["r"] * pulse

            # outer ring
            ring_r = nr * 2.2
            ring = QRadialGradient(nx, ny, ring_r)
            ring.setColorAt(0, QColor(0, 200, 255, 0))
            ring.setColorAt(0.6, QColor(0, 200, 255, 30))
            ring.setColorAt(1, QColor(0, 200, 255, 0))
            painter.setBrush(QBrush(ring))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(nx, ny), ring_r, ring_r)

            # core node
            grad = QRadialGradient(nx - nr * 0.3, ny - nr * 0.3, nr * 1.5)
            grad.setColorAt(0, QColor(150, 240, 255))
            grad.setColorAt(0.5, QColor(0, 160, 220))
            grad.setColorAt(1, QColor(0, 80, 140))
            painter.setBrush(QBrush(grad))
            painter.drawEllipse(QPointF(nx, ny), nr, nr)

        painter.end()


# ─────────────────────────────────────────────
#  Animated title label (character fade-in)
# ─────────────────────────────────────────────
class GlowLabel(QLabel):
    def __init__(self, text, color="#00E5FF", glow_radius=30, parent=None):
        super().__init__(text, parent)
        self._color = QColor(color)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(glow_radius)
        shadow.setOffset(0, 0)
        shadow.setColor(self._color)
        self.setGraphicsEffect(shadow)


# ─────────────────────────────────────────────
#  Neon input field
# ─────────────────────────────────────────────
NEON_INPUT_STYLE = """
QLineEdit {{
    background: rgba(0, 10, 30, 0.75);
    color: #E0F7FF;
    border: 1.5px solid rgba(0, 180, 255, 0.35);
    border-radius: {radius}px;
    padding: 0 20px;
    font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
    font-size: 15px;
    letter-spacing: 1px;
    selection-background-color: rgba(0, 200, 255, 0.3);
}}
QLineEdit:focus {{
    border: 1.5px solid #00D4FF;
    background: rgba(0, 20, 50, 0.85);
}}
QLineEdit::placeholder {{
    color: rgba(120, 180, 200, 0.5);
}}
"""


# ─────────────────────────────────────────────
#  Hexagon button
# ─────────────────────────────────────────────
class HexButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self._glow = 0.0
        self._anim = QPropertyAnimation(self, b"glow")
        self._anim.setDuration(300)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(58)

    @pyqtProperty(float)
    def glow(self):
        return self._glow

    @glow.setter
    def glow(self, v):
        self._glow = v
        self.update()

    def enterEvent(self, e):
        self._anim.stop()
        self._anim.setStartValue(self._glow)
        self._anim.setEndValue(1.0)
        self._anim.start()

    def leaveEvent(self, e):
        self._anim.stop()
        self._anim.setStartValue(self._glow)
        self._anim.setEndValue(0.0)
        self._anim.start()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # background gradient
        grad = QLinearGradient(0, 0, w, h)
        r = int(0 + self._glow * 30)
        g = int(180 + self._glow * 40)
        b = int(255)
        grad.setColorAt(0.0, QColor(r, g - 40, b, 210))
        grad.setColorAt(1.0, QColor(r + 40, g, b, 210))
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), 14, 14)
        p.fillPath(path, QBrush(grad))

        # outer glow border
        pen = QPen(QColor(0, int(200 + self._glow * 55), 255, int(180 + self._glow * 75)))
        pen.setWidthF(1.5)
        p.setPen(pen)
        p.drawPath(path)

        # inner shine
        shine = QLinearGradient(0, 0, 0, h * 0.55)
        shine.setColorAt(0, QColor(255, 255, 255, int(60 + self._glow * 40)))
        shine.setColorAt(1, QColor(255, 255, 255, 0))
        shine_path = QPainterPath()
        shine_path.addRoundedRect(QRectF(2, 2, w - 4, h * 0.5), 12, 12)
        p.fillPath(shine_path, QBrush(shine))

        # text
        p.setPen(QPen(QColor(255, 255, 255, 240)))
        font = QFont()
        font.setPointSize(13)
        font.setWeight(QFont.Weight.Bold)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.5)
        p.setFont(font)
        p.drawText(QRect(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, self.text())
        p.end()


# ─────────────────────────────────────────────
#  Pulsing ring widget (decorative)
# ─────────────────────────────────────────────
class PulseRing(QWidget):
    def __init__(self, color="#00D4FF", parent=None):
        super().__init__(parent)
        self._color = QColor(color)
        self._phase = 0.0
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setFixedSize(300, 300)
        t = QTimer(self)
        t.timeout.connect(self._tick)
        t.start(20)

    def _tick(self):
        self._phase = (self._phase + 0.025) % (math.pi * 2)
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = self.width() / 2, self.height() / 2
        for i, (base_r, speed, alpha_max) in enumerate([
            (60, 1.0, 120),
            (90, 0.7, 80),
            (120, 0.4, 50),
        ]):
            phase_offset = i * math.pi / 3
            r = base_r + 18 * math.sin(self._phase * speed + phase_offset)
            alpha = int(alpha_max * (0.5 + 0.5 * math.sin(self._phase * speed + phase_offset)))
            c = QColor(self._color.red(), self._color.green(), self._color.blue(), alpha)
            pen = QPen(c)
            pen.setWidthF(1.5)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(cx, cy), r, r)
        p.end()


# ─────────────────────────────────────────────
#  Scanline overlay (CRT retro-futurism touch)
# ─────────────────────────────────────────────
class ScanlineOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)

    def paintEvent(self, e):
        p = QPainter(self)
        for y in range(0, self.height(), 4):
            p.fillRect(0, y, self.width(), 1, QColor(0, 0, 0, 18))
        p.end()


# ─────────────────────────────────────────────
#  Main setup page
# ─────────────────────────────────────────────
class SetupPage(QWidget):
    setup_complete = pyqtSignal(str, str)  # ip, port

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        # ── background canvas ──
        self.canvas = NetworkCanvas(self)
        self.canvas.setGeometry(0, 0, 1600, 1000)

        # ── scanline ──
        self.scanlines = ScanlineOverlay(self)
        self.scanlines.setGeometry(0, 0, 1600, 1000)

        # ── pulse rings (decorative, behind card) ──
        self.ring_tl = PulseRing("#00D4FF", self)
        self.ring_br = PulseRing("#7B2FFF", self)

        # ── main content (stacked on canvas) ──
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # spacer top
        outer.addStretch(1)

        # center row
        center_row = QHBoxLayout()
        center_row.setSpacing(0)
        center_row.addStretch(1)

        # ── card ──
        card = QFrame()
        card.setFixedWidth(520)
        card.setStyleSheet("""
            QFrame {
                background: rgba(4, 14, 38, 0.82);
                border-radius: 28px;
                border: 1px solid rgba(0, 180, 255, 0.25);
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(80)
        shadow.setOffset(0, 20)
        shadow.setColor(QColor(0, 100, 255, 80))
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(52, 48, 52, 52)
        card_layout.setSpacing(0)

        # ── icon row ──
        icon_row = QHBoxLayout()
        icon_lbl = QLabel("⬡")
        icon_lbl.setStyleSheet("""
            color: #00D4FF;
            font-size: 42px;
        """)
        icon_shadow = QGraphicsDropShadowEffect()
        icon_shadow.setBlurRadius(30)
        icon_shadow.setOffset(0, 0)
        icon_shadow.setColor(QColor(0, 212, 255, 200))
        icon_lbl.setGraphicsEffect(icon_shadow)
        icon_row.addStretch()
        icon_row.addWidget(icon_lbl)
        icon_row.addStretch()
        card_layout.addLayout(icon_row)
        card_layout.addSpacing(12)

        # ── title ──
        title = GlowLabel("INDA", "#00D4FF", 45)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            color: #FFFFFF;
            font-size: 52px;
            font-weight: 900;
            font-family: 'Orbitron', 'Rajdhani', 'Exo 2', 'Arial Black', sans-serif;
            letter-spacing: 10px;
            background: transparent;
        """)
        card_layout.addWidget(title)
        card_layout.addSpacing(6)

        # ── subtitle ──
        sub = QLabel("INTELLIGENT NETWORK DESIGN AUTOMATION")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("""
            color: rgba(0, 200, 255, 0.7);
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 4px;
            font-family: 'Rajdhani', 'Exo 2', 'Trebuchet MS', sans-serif;
            background: transparent;
        """)
        card_layout.addWidget(sub)
        card_layout.addSpacing(6)

        # ── divider ──
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                          "stop:0 transparent, stop:0.3 rgba(0,200,255,0.5),"
                          "stop:0.7 rgba(0,200,255,0.5), stop:1 transparent);")
        card_layout.addWidget(div)
        card_layout.addSpacing(32)

        # ── IP field ──
        ip_label = QLabel("◈  SERVER ADDRESS")
        ip_label.setStyleSheet("""
            color: rgba(100, 200, 255, 0.8);
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 3px;
            font-family: 'Rajdhani', monospace;
            background: transparent;
        """)
        card_layout.addWidget(ip_label)
        card_layout.addSpacing(8)

        self.ip_input = QLineEdit("127.0.0.1")
        self.ip_input.setMinimumHeight(52)
        self.ip_input.setStyleSheet(NEON_INPUT_STYLE.format(radius=13))
        self.ip_input.setPlaceholderText("e.g.  127.0.0.1")
        card_layout.addWidget(self.ip_input)
        card_layout.addSpacing(20)

        # ── Port field ──
        port_label = QLabel("◈  SERVER PORT")
        port_label.setStyleSheet("""
            color: rgba(100, 200, 255, 0.8);
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 3px;
            font-family: 'Rajdhani', monospace;
            background: transparent;
        """)
        card_layout.addWidget(port_label)
        card_layout.addSpacing(8)

        self.port_input = QLineEdit("3080")
        self.port_input.setMinimumHeight(52)
        self.port_input.setStyleSheet(NEON_INPUT_STYLE.format(radius=13))
        self.port_input.setPlaceholderText("e.g.  3080")
        card_layout.addWidget(self.port_input)
        card_layout.addSpacing(8)

        # ── status label ──
        self.status_lbl = QLabel("")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_lbl.setMinimumHeight(28)
        self.status_lbl.setWordWrap(True)
        self.status_lbl.setStyleSheet("background: transparent; color: transparent; font-size: 12px;")
        card_layout.addWidget(self.status_lbl)
        card_layout.addSpacing(10)

        # ── connect button ──
        self.connect_btn = HexButton("⟶  INITIALIZE CONNECTION")
        self.connect_btn.clicked.connect(self._on_connect)
        card_layout.addWidget(self.connect_btn)
        card_layout.addSpacing(24)

        # ── bottom badge ──
        badge_row = QHBoxLayout()
        for dot_color, dot_text in [("#00FF88", "SECURE"), ("#00D4FF", "GNS3 v2.2"), ("#FF6B35", "LIVE")]:
            dot_lbl = QLabel(f"● {dot_text}")
            dot_lbl.setStyleSheet(f"""
                color: {dot_color};
                font-size: 9px;
                font-weight: 700;
                letter-spacing: 2px;
                font-family: monospace;
                background: transparent;
            """)
            badge_row.addStretch()
            badge_row.addWidget(dot_lbl)
        badge_row.addStretch()
        card_layout.addLayout(badge_row)

        center_row.addWidget(card)
        center_row.addStretch(1)

        outer.addLayout(center_row)
        outer.addStretch(1)

        # ── corner decoration labels ──
        self._add_corner_deco()

        # ── fade-in animation ──
        self._opacity_effect = QGraphicsOpacityEffect(card)
        card.setGraphicsEffect(self._opacity_effect)
        self._opacity_effect.setOpacity(0)
        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_anim.setDuration(900)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        QTimer.singleShot(100, self._fade_anim.start)

    def _add_corner_deco(self):
        """Adds small corner decoration labels."""
        style = """
            color: rgba(0, 180, 255, 0.4);
            font-size: 10px;
            font-family: monospace;
            background: transparent;
            letter-spacing: 2px;
        """
        tl = QLabel("◤ SYS::INIT", self)
        tl.setStyleSheet(style)
        tl.move(24, 20)

        tr = QLabel("NET::OK ◥", self)
        tr.setStyleSheet(style)
        tr.adjustSize()

        bl = QLabel("◣ VER::2.2.0", self)
        bl.setStyleSheet(style)

        self._corner_labels = [tl, tr, bl]

    def resizeEvent(self, e):
        w, h = self.width(), self.height()
        self.canvas.setGeometry(0, 0, w, h)
        self.scanlines.setGeometry(0, 0, w, h)
        # Position pulse rings
        self.ring_tl.move(-80, -80)
        self.ring_br.move(w - 220, h - 220)
        # Reposition corner labels
        if hasattr(self, "_corner_labels") and len(self._corner_labels) >= 3:
            tl, tr, bl = self._corner_labels
            tl.move(24, 20)
            tr.adjustSize()
            tr.move(w - tr.width() - 24, 20)
            bl.adjustSize()
            bl.move(24, h - bl.height() - 20)

    def _on_connect(self):
        ip = self.ip_input.text().strip()
        port = self.port_input.text().strip()

        if not ip or not port:
            self._show_status("⚠  Please fill in both fields", "#FF5555")
            return

        self._show_status("◌  Establishing connection …", "#00D4FF")
        QTimer.singleShot(700, lambda: self._finalize(ip, port))

    def _finalize(self, ip, port):
        self._show_status("✔  Connection established!", "#00FF88")
        QTimer.singleShot(500, lambda: self.setup_complete.emit(ip, port))

    def _show_status(self, msg, color):
        self.status_lbl.setText(msg)
        self.status_lbl.setStyleSheet(
            f"background: transparent; color: {color}; "
            f"font-size: 12px; font-weight: 700; letter-spacing: 1px; font-family: monospace;")


"""
TopologySelectionDialog
=======================
Shows the top-2 recommended topologies side-by-side.
Each card contains:
  • Rank / score badge
  • Pros & cons list
  • Live SVG network-diagram preview (generated in-memory, no disk I/O)

The user can inspect both previews and then click "Deploy <topology>" to confirm.

Usage (from app.py / start_architecture_engine):
    dlg = TopologySelectionDialog(conn_engine.top2, conn_engine, machines, parent=self)
    if dlg.exec() == QDialog.DialogCode.Accepted:
        chosen = dlg.chosen_topology          # e.g. "star"
        connections = dlg.chosen_connections  # list of {"from":…,"to":…} dicts
"""

# ---------------------------------------------------------------------------
# Re-use the SVG machinery that already exists in the project
# ---------------------------------------------------------------------------
try:
    from VisioGns3.Architecture.topology_visualization import SVGGenerator, Node as TVNode, Connection as TVConnection, LayoutCalculator
    _HAS_VIZ = True
except ImportError:
    _HAS_VIZ = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_nodes_from_machines(machine_list: List[str]) -> Dict[str, "TVNode"]:
    """
    Convert a flat list of machine names (from ArchitectureEngine.machines)
    into a dict of TVNode objects that SVGGenerator can consume.
    Positions are set to 0,0 — SVGGenerator's auto-layout will fix them.
    """
    nodes: Dict[str, TVNode] = {}
    for name in machine_list:
        nl = name.lower()
        if "router" in nl or "core" in nl:
            ntype = "router"
        elif "firewall" in nl:
            ntype = "firewall"
        elif "internet" in nl or "cloud" in nl:
            ntype = "cloud"
        elif "switch" in nl:
            ntype = "ethernet_switch"
        elif "server" in nl:
            ntype = "server"
        elif "ap" in nl:
            ntype = "access_point"
        elif "laptop" in nl:
            ntype = "vpcs"
        else:
            ntype = "vpcs"
        nodes[name] = TVNode(
            name=name, node_type=ntype,
            x=0.0, y=0.0, symbol="", template_id=""
        )
    return nodes


def _build_tv_connections(raw_connections: List[Dict]) -> List["TVConnection"]:
    """Convert raw {"from":…,"to":…} dicts to TVConnection objects."""
    result = []
    for c in raw_connections:
        result.append(TVConnection(
            from_node=c["from"],
            to_node=c["to"],
        ))
    return result


def _generate_preview_svg(machine_list: List[str], raw_connections: List[Dict],
                           title: str) -> str:
    """
    Build an SVG string for the given topology.
    Returns an empty string on any failure.
    """
    if not _HAS_VIZ:
        return ""
    try:
        nodes = _build_nodes_from_machines(machine_list)
        tv_conns = _build_tv_connections(raw_connections)
        # Filter connections to only those whose endpoints exist in nodes
        tv_conns = [c for c in tv_conns
                    if c.from_node in nodes and c.to_node in nodes]
        gen = SVGGenerator(nodes, tv_conns, title=title, auto_layout=True)
        return gen.generate()
    except Exception as exc:
        return f"<!-- SVG generation failed: {exc} -->"


def _wrap_svg_in_html(svg: str) -> str:
    """Wrap raw SVG in a minimal responsive HTML page for QWebEngineView."""
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html, body {{ width:100%; height:100%; background:#0F172A; overflow:auto; }}
  body {{ display:flex; justify-content:center; align-items:flex-start; padding:12px; }}
  #wrap {{ background:#1E293B; border:1px solid #334155; border-radius:6px;
           box-shadow:0 2px 12px rgba(0,0,0,0.5); }}
  svg {{ display:block; width:100%; height:auto; }}
</style>
</head>
<body>
  <div id="wrap">{svg if svg else '<p style="color:#94A3B8;padding:20px">Preview unavailable</p>'}</div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Main dialog
# ---------------------------------------------------------------------------

class TopologySelectionDialog(QDialog):
    """
    Two-column dialog: each column = one topology card with
    pros/cons + live SVG preview.  User picks one, then deploys.

    Parameters
    ----------
    top2          : list of 2 dicts from ArchitectureConnections.choose_top2_topologies()
    conn_engine   : ArchitectureConnections instance (used to generate preview connections)
    machine_list  : list[str] — engine.machines (already generated before this dialog opens)
    parent        : Qt parent widget
    """

    def __init__(self, top2: List[Dict], conn_engine=None,
                 machine_list: List[str] = None, parent=None):
        super().__init__(parent)
        self.top2 = top2
        self.conn_engine = conn_engine
        self.machine_list = machine_list or []
        self.chosen_topology: str = top2[0]["name"]
        self.chosen_connections: List[Dict] = []

        # Pre-generate connections + SVGs for both topologies
        self._preview_data: Dict[str, Dict] = {}
        self._pregenerate_previews()

        self.setWindowTitle("Select & Preview Network Topology")
        self.setMinimumSize(1400, 920)
        # IMPORTANT: only target QDialog and QLabel at the top level.
        # Child QFrame / QWidget styles must be set via setStyleSheet() on the
        # individual widget, NOT through a cascading rule here — otherwise Qt
        # will apply "QFrame { border … }" to every nested frame/widget too.
        self.setStyleSheet("""
            QDialog { background: #0F172A; }
        """)
        self._build_ui()

    # ------------------------------------------------------------------
    # Pre-generation
    # ------------------------------------------------------------------

    def _pregenerate_previews(self):
        """
        For each of the top-2 topologies, generate connections in-memory
        and build an SVG preview string.  Nothing is written to disk.
        """
        if self.conn_engine is None:
            return

        for entry in self.top2:
            topo_name = entry["name"]
            try:
                # Clone the engine's internal state for this topology
                import copy
                engine_copy = copy.copy(self.conn_engine)
                engine_copy.connections = []
                engine_copy.topology = topo_name

                engine_copy._generate_connections()
                raw_conns = list(engine_copy.connections)

                # Build SVG
                svg = _generate_preview_svg(
                    self.machine_list, raw_conns,
                    title=f"{topo_name.upper()} Topology Preview"
                )
                self._preview_data[topo_name] = {
                    "connections": raw_conns,
                    "svg": svg,
                }
            except Exception as exc:
                self._preview_data[topo_name] = {
                    "connections": [],
                    "svg": f"<!-- preview error: {exc} -->",
                }

        # Default chosen connections = rank-1 topology
        default = self.top2[0]["name"]
        self.chosen_connections = self._preview_data.get(default, {}).get("connections", [])

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        # ── Header ──────────────────────────────────────────────────────
        hdr = QLabel("🏗️  Choose Your Network Topology")
        hdr.setStyleSheet(
            "color:#F8FAFC; font-size:22px; font-weight:800; letter-spacing:0.5px;"
        )
        root.addWidget(hdr)

        sub = QLabel(
            "Both topologies are shown below with pros & cons and a live network preview. "
            "Select the one that best fits your requirements."
        )
        sub.setWordWrap(True)
        sub.setStyleSheet("color:#94A3B8; font-size:13px;")
        root.addWidget(sub)

        # ── Two-column area: each column = card (no button) + button below ──
        cards_row = QHBoxLayout()
        cards_row.setSpacing(20)

        self._card_frames: List[tuple] = []
        self._select_btns: List[tuple] = []
        self._web_views:  Dict[str, QWebEngineView] = {}

        for entry in self.top2:
            card, btn, webview = self._make_card(entry)

            # Plain transparent wrapper — no border, no background of its own
            col = QWidget()
            col.setStyleSheet("background: transparent;")
            col_layout = QVBoxLayout(col)
            col_layout.setContentsMargins(0, 0, 0, 0)
            col_layout.setSpacing(10)
            col_layout.addWidget(card, stretch=1)
            col_layout.addWidget(btn)

            cards_row.addWidget(col)
            self._card_frames.append((card, entry["name"]))
            self._select_btns.append((btn, entry["name"]))
            self._web_views[entry["name"]] = webview

        root.addLayout(cards_row, stretch=1)

        # Load SVGs slightly after the dialog is shown (WebEngine needs a moment)
        QTimer.singleShot(300, self._load_svg_previews)

        # ── Divider ──────────────────────────────────────────────────────
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(
            "background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 transparent,stop:0.3 rgba(100,116,139,0.4),"
            "stop:0.7 rgba(100,116,139,0.4),stop:1 transparent);"
        )
        root.addWidget(div)

        # ── Bottom bar ───────────────────────────────────────────────────
        bar = QHBoxLayout()

        self._confirm_lbl = QLabel(
            f"Selected: <b>{self._display(self.chosen_topology)}</b>"
        )
        self._confirm_lbl.setStyleSheet("color:#22D3EE; font-size:13px;")
        bar.addWidget(self._confirm_lbl)
        bar.addStretch()

        cancel_btn = QPushButton("✕  Cancel")
        cancel_btn.setFixedHeight(44)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background:rgba(248,113,113,0.1); color:#F87171;
                border:1px solid rgba(248,113,113,0.3); border-radius:10px;
                font-size:13px; font-weight:700; padding:0 20px;
            }
            QPushButton:hover { background:rgba(248,113,113,0.22); }
        """)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        bar.addWidget(cancel_btn)

        self._deploy_btn = QPushButton(
            f"✅  Deploy  {self._icon(self.chosen_topology)}"
            f"  {self._display(self.chosen_topology)}"
        )
        self._deploy_btn.setFixedHeight(44)
        self._deploy_btn.setStyleSheet("""
            QPushButton {
                background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #0891B2,stop:1 #06B6D4);
                color:#FFFFFF; border:none; border-radius:10px;
                font-size:14px; font-weight:700; padding:0 28px;
            }
            QPushButton:hover {
                background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #0E7490,stop:1 #0891B2);
            }
        """)
        self._deploy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._deploy_btn.clicked.connect(self.accept)
        bar.addWidget(self._deploy_btn)

        root.addLayout(bar)

        # Apply initial highlight
        self._highlight(self.chosen_topology)

    # ------------------------------------------------------------------
    # Card builder
    # ------------------------------------------------------------------

    def _make_card(self, entry: Dict):
        """
        Build one topology card.

        Structural fix notes
        --------------------
        • The card QFrame has ONE stylesheet rule (border on QFrame only).
          No nested QFrame/QWidget children carry a border style — that was
          causing every child container to get highlighted on selection.
        • Pros/cons are plain QLabel rows — no wrapping QWidget/QFrame needed.
        • The webview is given a FIXED height so it cannot overflow its parent.
        • The Select button is NOT added here — it is added outside the card
          by _build_ui, below the card in the column wrapper.

        Returns (card QFrame, select QPushButton, QWebEngineView)
        """
        pc        = entry.get("pros_cons", {})
        name      = entry["name"]
        rank      = entry["rank"]
        score     = entry["score"]
        icon      = pc.get("icon", "◈")
        disp_name = pc.get("display_name", name.title())
        desc      = pc.get("description", "")
        pros      = pc.get("pros", [])
        cons      = pc.get("cons", [])
        best_for  = pc.get("best_for", "")

        # ── Outer card frame ──────────────────────────────────────────
        # setStyleSheet targets ONLY "QFrame" — not children — because the
        # rule has no descendant selector.  Sub-widgets use inline styles.
        card = QFrame()
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # Explicit object name so the stylesheet selector is unambiguous
        card.setObjectName("topoCard")
        card.setStyleSheet("""
            QFrame#topoCard {
                background: rgba(30, 41, 59, 0.70);
                border: 2px solid rgba(100, 116, 139, 0.25);
                border-radius: 16px;
            }
        """)

        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(20, 18, 20, 18)
        vbox.setSpacing(8)

        # ── Badge + score row ─────────────────────────────────────────
        badge_row = QHBoxLayout()
        rank_badge = QLabel(f"  #{rank} Recommended  ")
        rank_badge.setStyleSheet(
            "color: #22D3EE; font-size: 10px; font-weight: 700;"
            "letter-spacing: 2px; background: rgba(34,211,238,0.12);"
            "border-radius: 8px; padding: 3px 0; border: none;"
        )
        badge_row.addWidget(rank_badge)
        badge_row.addStretch()
        score_lbl = QLabel(f"Score: {score}")
        score_lbl.setStyleSheet(
            "color: #94A3B8; font-size: 11px; font-weight: 600;"
            "background: transparent; border: none;"
        )
        badge_row.addWidget(score_lbl)
        vbox.addLayout(badge_row)

        # ── Title + description ───────────────────────────────────────
        title_lbl = QLabel(f"{icon}  {disp_name}")
        title_lbl.setStyleSheet(
            "color: #F8FAFC; font-size: 19px; font-weight: 800;"
            "background: transparent; border: none;"
        )
        vbox.addWidget(title_lbl)

        desc_lbl = QLabel(desc)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet(
            "color: #64748B; font-size: 11px;"
            "background: transparent; border: none;"
        )
        vbox.addWidget(desc_lbl)

        # ── Thin divider ──────────────────────────────────────────────
        vbox.addWidget(self._divider())

        # ── Pros & Cons as plain label lists (no nested frames) ───────
        # Both columns are laid out in a single QHBoxLayout containing
        # two QVBoxLayouts — no QWidget/QFrame wrappers, so no border bleed.
        pc_row = QHBoxLayout()
        pc_row.setSpacing(20)

        pros_col = QVBoxLayout()
        pros_col.setSpacing(3)
        pros_hdr = QLabel("✅  Pros")
        pros_hdr.setStyleSheet(
            "color: #4ADE80; font-size: 12px; font-weight: 700;"
            "background: transparent; border: none;"
        )
        pros_col.addWidget(pros_hdr)
        for p in pros:
            lbl = QLabel(f"  •  {p}")
            lbl.setWordWrap(True)
            lbl.setStyleSheet(
                "color: #CBD5E1; font-size: 11px;"
                "background: transparent; border: none;"
            )
            pros_col.addWidget(lbl)
        pros_col.addStretch()

        cons_col = QVBoxLayout()
        cons_col.setSpacing(3)
        cons_hdr = QLabel("⚠️  Cons")
        cons_hdr.setStyleSheet(
            "color: #FBBF24; font-size: 12px; font-weight: 700;"
            "background: transparent; border: none;"
        )
        cons_col.addWidget(cons_hdr)
        for c in cons:
            lbl = QLabel(f"  •  {c}")
            lbl.setWordWrap(True)
            lbl.setStyleSheet(
                "color: #CBD5E1; font-size: 11px;"
                "background: transparent; border: none;"
            )
            cons_col.addWidget(lbl)
        cons_col.addStretch()

        pc_row.addLayout(pros_col)
        pc_row.addLayout(cons_col)
        vbox.addLayout(pc_row)

        # ── Best for ──────────────────────────────────────────────────
        best_lbl = QLabel(f"🎯  Best for: {best_for}")
        best_lbl.setWordWrap(True)
        best_lbl.setStyleSheet(
            "color: #7DD3FC; font-size: 11px; font-style: italic;"
            "background: transparent; border: none;"
        )
        vbox.addWidget(best_lbl)

        # ── Thin divider ──────────────────────────────────────────────
        vbox.addWidget(self._divider())

        # ── Network preview label ─────────────────────────────────────
        preview_lbl = QLabel("📊  Network Preview")
        preview_lbl.setStyleSheet(
            "color: #94A3B8; font-size: 11px; font-weight: 700;"
            "letter-spacing: 1px; background: transparent; border: none;"
        )
        vbox.addWidget(preview_lbl)

        # ── WebView — FIXED height so it never overflows the card ─────
        # Do NOT use stretch here.  A fixed pixel height keeps the webview
        # fully contained regardless of dialog resize.
        webview = QWebEngineView()
        webview.setFixedHeight(320)
        webview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        webview.setHtml(_wrap_svg_in_html(""))   # loading placeholder
        vbox.addWidget(webview)                   # no stretch= argument

        # ── Select button is built here but returned for placement ────
        # It will be added OUTSIDE the card by _build_ui.
        btn = QPushButton(f"Select  {disp_name}")
        btn.setFixedHeight(44)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background: rgba(34, 211, 238, 0.10);
                color: #22D3EE;
                border: 1px solid rgba(34, 211, 238, 0.30);
                border-radius: 10px;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: rgba(34, 211, 238, 0.22);
                border: 1px solid #22D3EE;
            }
        """)
        btn.clicked.connect(lambda _, n=name: self._on_select(n))

        return card, btn, webview

    # ------------------------------------------------------------------
    # Load SVG previews into web views
    # ------------------------------------------------------------------

    def _load_svg_previews(self):
        """Called via QTimer after dialog is visible — loads SVG into web views."""
        for topo_name, webview in self._web_views.items():
            svg = self._preview_data.get(topo_name, {}).get("svg", "")
            webview.setHtml(_wrap_svg_in_html(svg))

    # ------------------------------------------------------------------
    # Interaction
    # ------------------------------------------------------------------

    def _on_select(self, topology_name: str):
        self.chosen_topology   = topology_name
        self.chosen_connections = self._preview_data.get(
            topology_name, {}
        ).get("connections", [])
        self._highlight(topology_name)
        self._confirm_lbl.setText(
            f"Selected: <b>{self._display(topology_name)}</b>"
        )
        self._deploy_btn.setText(
            f"✅  Deploy  {self._icon(topology_name)}"
            f"  {self._display(topology_name)}"
        )

    def _highlight(self, topology_name: str):
        for frame, name in self._card_frames:
            if name == topology_name:
                frame.setStyleSheet("""
                    QFrame#topoCard {
                        background: rgba(30, 41, 59, 0.92);
                        border: 2px solid #22D3EE;
                        border-radius: 16px;
                    }
                """)
            else:
                frame.setStyleSheet("""
                    QFrame#topoCard {
                        background: rgba(30, 41, 59, 0.70);
                        border: 2px solid rgba(100, 116, 139, 0.25);
                        border-radius: 16px;
                    }
                """)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _divider() -> QFrame:
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background:rgba(100,116,139,0.20);")
        return div

    def _display(self, name: str) -> str:
        try:
            from VisioGns3.Architecture.generate_connections_architecture import TOPOLOGY_PROS_CONS
        except ImportError:
            try:
                from VisioGns3.Architecture.generate_connections_architecture import TOPOLOGY_PROS_CONS
            except ImportError:
                return name.title()
        return TOPOLOGY_PROS_CONS.get(name, {}).get("display_name", name.title())

    def _icon(self, name: str) -> str:
        try:
            from VisioGns3.Architecture.generate_connections_architecture import TOPOLOGY_PROS_CONS
        except ImportError:
            try:
                from VisioGns3.Architecture.generate_connections_architecture import TOPOLOGY_PROS_CONS
            except ImportError:
                return "◈"
        return TOPOLOGY_PROS_CONS.get(name, {}).get("icon", "◈")

class VisioGNS3App(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_file = None
        self.automation_completed = False
        self.server_configured = False
        self.server_ip = ""
        self.server_port = ""
        self.automation_runner = None  # Store thread reference
        self.assistant_active = False
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
        self.architecture_page = self.create_architecture_page()

        self.stacked_widget.addWidget(self.setup_page)       # index 0
        self.stacked_widget.addWidget(self.landing_page)     # index 1
        self.stacked_widget.addWidget(self.console_page)     # index 2
        self.stacked_widget.addWidget(self.chatbot_page)     # index 3
        self.stacked_widget.addWidget(self.architecture_page) # index 4

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
        page.setStyleSheet("background: transparent;")

        # ── Animated background layers ──
        self._setup_canvas = NetworkCanvas(page)
        self._setup_scanlines = ScanlineOverlay(page)
        self._setup_ring_tl = PulseRing("#00D4FF", page)
        self._setup_ring_br = PulseRing("#7B2FFF", page)

        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Outer vertical centering ──
        layout.addStretch(1)

        center_row = QHBoxLayout()
        center_row.setSpacing(0)
        center_row.addStretch(1)

        # ══════════════════════════════════════════
        #  CARD
        # ══════════════════════════════════════════
        setup_container = QFrame()
        setup_container.setMaximumWidth(580)
        setup_container.setMinimumWidth(520)
        setup_container.setStyleSheet("""
            QFrame {
                background: rgba(4, 12, 35, 0.78);
                border-radius: 24px;
                border: 1px solid rgba(0, 180, 255, 0.18);
            }
        """)
        # card_shadow = QGraphicsDropShadowEffect()
        # card_shadow.setBlurRadius(60)
        # card_shadow.setOffset(0, 16)
        # card_shadow.setColor(QColor(0, 80, 200, 100))
        # setup_container.setGraphicsEffect(card_shadow)

        setup_layout = QVBoxLayout()
        setup_layout.setContentsMargins(52, 44, 52, 44)
        setup_layout.setSpacing(0)
        setup_container.setLayout(setup_layout)

        # ── Icon ──────────────────────────────────────
        icon_row = QHBoxLayout()
        icon_lbl = QLabel("⬡")
        icon_lbl.setStyleSheet("""
            color: #00D4FF;
            font-size: 38px;
            background: transparent;
            border: none;
        """)
        icon_shadow = QGraphicsDropShadowEffect()
        icon_shadow.setBlurRadius(28)
        icon_shadow.setOffset(0, 0)
        icon_shadow.setColor(QColor(0, 212, 255, 180))
        icon_lbl.setGraphicsEffect(icon_shadow)
        icon_row.addStretch()
        icon_row.addWidget(icon_lbl)
        icon_row.addStretch()
        setup_layout.addLayout(icon_row)
        setup_layout.addSpacing(10)

        # ── Title ─────────────────────────────────────
        title_lbl = QLabel("INDA")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet("""
            color: #FFFFFF;
            font-size: 48px;
            font-weight: 900;
            letter-spacing: 10px;
            font-family: 'Orbitron', 'Arial Black', sans-serif;
            background: transparent;
            border: none;
        """)
        title_shadow = QGraphicsDropShadowEffect()
        title_shadow.setBlurRadius(40)
        title_shadow.setOffset(0, 0)
        title_shadow.setColor(QColor(0, 200, 255, 160))
        title_lbl.setGraphicsEffect(title_shadow)
        setup_layout.addWidget(title_lbl)
        setup_layout.addSpacing(6)

        # ── Subtitle ──────────────────────────────────
        sub_lbl = QLabel("INTELLIGENT NETWORK DESIGN AUTOMATION")
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_lbl.setStyleSheet("""
            color: rgba(0, 200, 255, 0.55);
            font-size: 9px;
            font-weight: 700;
            letter-spacing: 4px;
            font-family: 'Rajdhani', 'Trebuchet MS', sans-serif;
            background: transparent;
            border: none;
        """)
        setup_layout.addWidget(sub_lbl)
        setup_layout.addSpacing(26)

        # ── Top divider ───────────────────────────────
        div_top = QFrame()
        div_top.setFixedHeight(1)
        div_top.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent,
                stop:0.3 rgba(0, 180, 255, 0.22),
                stop:0.7 rgba(0, 180, 255, 0.22),
                stop:1 transparent);
            border: none;
        """)
        setup_layout.addWidget(div_top)
        setup_layout.addSpacing(30)

        # ── IP label ──────────────────────────────────
        ip_label = QLabel("SERVER ADDRESS")
        ip_label.setStyleSheet("""
            color: rgba(80, 180, 255, 0.60);
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 3px;
            font-family: monospace;
            background: transparent;
            border: none;
            padding: 0;
        """)
        setup_layout.addWidget(ip_label)
        setup_layout.addSpacing(7)

        # ── IP input ──────────────────────────────────
        self.setup_input_ip = QLineEdit()
        self.setup_input_ip.setPlaceholderText("127.0.0.1")
        self.setup_input_ip.setText("127.0.0.1")
        self.setup_input_ip.setMinimumHeight(50)
        self.setup_input_ip.setStyleSheet("""
            QLineEdit {
                background: rgba(0, 15, 40, 0.60);
                color: #D0EFFF;
                border: none;
                border-bottom: 1.5px solid rgba(0, 160, 240, 0.28);
                border-radius: 0px;
                padding: 0 4px;
                font-size: 15px;
                font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
                letter-spacing: 1px;
                selection-background-color: rgba(0, 180, 255, 0.25);
            }
            QLineEdit:focus {
                border-bottom: 1.5px solid #00C8FF;
                background: rgba(0, 25, 60, 0.65);
                color: #FFFFFF;
            }
        """)
        setup_layout.addWidget(self.setup_input_ip)
        setup_layout.addSpacing(28)

        # ── Port label ────────────────────────────────
        port_label = QLabel("SERVER PORT")
        port_label.setStyleSheet("""
            color: rgba(80, 180, 255, 0.60);
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 3px;
            font-family: monospace;
            background: transparent;
            border: none;
            padding: 0;
        """)
        setup_layout.addWidget(port_label)
        setup_layout.addSpacing(7)

        # ── Port input ────────────────────────────────
        self.setup_input_port = QLineEdit()
        self.setup_input_port.setPlaceholderText("3080")
        self.setup_input_port.setText("3080")
        self.setup_input_port.setMinimumHeight(50)
        self.setup_input_port.setStyleSheet("""
            QLineEdit {
                background: rgba(0, 15, 40, 0.60);
                color: #D0EFFF;
                border: none;
                border-bottom: 1.5px solid rgba(0, 160, 240, 0.28);
                border-radius: 0px;
                padding: 0 4px;
                font-size: 15px;
                font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
                letter-spacing: 1px;
                selection-background-color: rgba(0, 180, 255, 0.25);
            }
            QLineEdit:focus {
                border-bottom: 1.5px solid #00C8FF;
                background: rgba(0, 25, 60, 0.65);
                color: #FFFFFF;
            }
        """)
        setup_layout.addWidget(self.setup_input_port)
        setup_layout.addSpacing(10)

        # ── Status label ──────────────────────────────
        self.setup_status = QLabel("")
        self.setup_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setup_status.setMinimumHeight(32)
        self.setup_status.setWordWrap(True)
        self.setup_status.setStyleSheet("""
            color: transparent;
            font-size: 12px;
            background: transparent;
            border: none;
            padding: 0;
        """)
        setup_layout.addWidget(self.setup_status)
        setup_layout.addSpacing(6)

        # ── Bottom divider ────────────────────────────
        div_bot = QFrame()
        div_bot.setFixedHeight(1)
        div_bot.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent,
                stop:0.3 rgba(0, 180, 255, 0.22),
                stop:0.7 rgba(0, 180, 255, 0.22),
                stop:1 transparent);
            border: none;
        """)
        setup_layout.addWidget(div_bot)
        setup_layout.addSpacing(22)

        # ── Connect button ────────────────────────────
        continue_btn = HexButton("⟶  INITIALIZE CONNECTION")
        continue_btn.clicked.connect(self.complete_setup)
        setup_layout.addWidget(continue_btn)
        setup_layout.addSpacing(22)

        # ── Bottom status dots ────────────────────────
        dots_row = QHBoxLayout()
        dots_row.setSpacing(0)
        for dot_color, dot_text in [
            ("#00FF88", "● SECURE"),
            ("#00BFFF", "● GNS3 v2.2"),
            ("#FF6B35", "● LIVE"),
        ]:
            dot = QLabel(dot_text)
            dot.setStyleSheet(f"""
                color: {dot_color};
                font-size: 9px;
                font-weight: 700;
                letter-spacing: 2px;
                font-family: monospace;
                background: transparent;
                border: none;
                padding: 0;
            """)
            dots_row.addStretch()
            dots_row.addWidget(dot)
        dots_row.addStretch()
        setup_layout.addLayout(dots_row)

        # ── Assemble center row ───────────────────────
        # ── Card shadow — apply to a wrapper, not the card itself ──
        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent;")
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.addWidget(setup_container)

        # card_shadow = QGraphicsDropShadowEffect()
        # card_shadow.setBlurRadius(60)
        # card_shadow.setOffset(0, 16)
        # card_shadow.setColor(QColor(0, 80, 200, 100))
        # wrapper.setGraphicsEffect(card_shadow)

        # ── Fade-in — on the card directly (no shadow on same widget) ──
        # self._setup_opacity = QGraphicsOpacityEffect(setup_container)
        # setup_container.setGraphicsEffect(self._setup_opacity)
        # self._setup_opacity.setOpacity(0.0)
        # self._fade_anim = QPropertyAnimation(self._setup_opacity, b"opacity")
        # self._fade_anim.setDuration(900)
        # self._fade_anim.setStartValue(0.0)
        # self._fade_anim.setEndValue(1.0)
        # self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        # QTimer.singleShot(120, self._fade_anim.start)

        center_row.addStretch(1)  # bigger = pushes card more to the right
        # setup_container
        center_row.addWidget(wrapper)
        center_row.addStretch(2)
        

        layout.addLayout(center_row)
        layout.addStretch(1)

        # ── Corner decorations ────────────────────────
        tl = QLabel("◤ SYS::INIT", page)
        tl.setStyleSheet("""
            color: rgba(0, 180, 255, 0.35);
            font-size: 10px;
            font-family: monospace;
            background: transparent;
            border: none;
            letter-spacing: 2px;
        """)
        tl.move(24, 20)

        tr = QLabel("NET::OK ◥", page)
        tr.setStyleSheet("""
            color: rgba(0, 180, 255, 0.35);
            font-size: 10px;
            font-family: monospace;
            background: transparent;
            border: none;
            letter-spacing: 2px;
        """)

        bl = QLabel("◣ VER::2.2.0", page)
        bl.setStyleSheet("""
            color: rgba(0, 180, 255, 0.35);
            font-size: 10px;
            font-family: monospace;
            background: transparent;
            border: none;
            letter-spacing: 2px;
        """)

        self._setup_corner_labels = [tl, tr, bl]

        # ── Fade-in on card ───────────────────────────
        # self._setup_opacity = QGraphicsOpacityEffect(setup_container)
        # setup_container.setGraphicsEffect(self._setup_opacity)
        # self._setup_opacity.setOpacity(0.0)
        # self._fade_anim = QPropertyAnimation(self._setup_opacity, b"opacity")
        # self._fade_anim.setDuration(900)
        # self._fade_anim.setStartValue(0.0)
        # self._fade_anim.setEndValue(1.0)
        # self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        # QTimer.singleShot(120, self._fade_anim.start)

        # center_row.addStretch(1)
        # center_row.addWidget(wrapper)
        # center_row.addStretch(3)

        # Store page ref for resizeEvent
        self._setup_page = page
        return page


    def _reposition_setup_bg(self):
        page = self._setup_page
        w, h = page.width() or 1200, page.height() or 900
        self._setup_canvas.setGeometry(0, 0, w, h)
        self._setup_scanlines.setGeometry(0, 0, w, h)
        self._setup_ring_tl.move(-80, -80)
        self._setup_ring_br.move(w - 220, h - 220)
        self._setup_canvas.lower()
        # Reposition corner labels
        if hasattr(self, "_setup_corner_labels"):
            tl, tr, bl = self._setup_corner_labels
            tl.move(24, 20)
            tr.adjustSize()
            tr.move(w - tr.width() - 24, 20)
            bl.adjustSize()
            bl.move(24, h - bl.height() - 20)


    # def resizeEvent(self, event):
    #     super().resizeEvent(event)
    #     if hasattr(self, "_setup_page"):
    #         self._reposition_setup_bg()


    def complete_setup(self):
        ip = self.setup_input_ip.text().strip()
        port = self.setup_input_port.text().strip()

        self.setup_status.setText("")
        self.setup_status.setStyleSheet("color: transparent; background: transparent; border: none;")

        if not ip or not port:
            self.setup_status.setText("⚠  Enter both IP and port")
            self.setup_status.setStyleSheet("""
                color: #FF5555;
                font-size: 12px;
                font-weight: 700;
                font-family: monospace;
                letter-spacing: 1px;
                background: transparent;
                border: none;
                padding: 0;
            """)
            return

        try:
            self.server_ip = ip
            self.server_port = port
            self.save_gns3_config(ip, port)
            self.setup_status.setText("✔  Connection established!")
            self.setup_status.setStyleSheet("""
                color: #00FF88;
                font-size: 12px;
                font-weight: 700;
                font-family: monospace;
                letter-spacing: 1px;
                background: transparent;
                border: none;
                padding: 0;
            """)
            self.server_configured = True
            QTimer.singleShot(600, self.show_landing_page)
        except Exception as e:
            self.setup_status.setText(f"✘  Error: {str(e)[:50]}")
            self.setup_status.setStyleSheet("""
                color: #FF5555;
                font-size: 12px;
                font-weight: 700;
                font-family: monospace;
                letter-spacing: 1px;
                background: transparent;
                border: none;
                padding: 0;
            """)


    def _position_setup_bg(self, page):
        w, h = page.width() or 1200, page.height() or 900
        self._setup_canvas.setGeometry(0, 0, w, h)
        self._setup_scanlines.setGeometry(0, 0, w, h)
        self._setup_ring_tl.move(-80, -80)
        self._setup_ring_br.move(w - 220, h - 220)
        # Push canvas behind everything
        self._setup_canvas.lower()
        self._setup_scanlines.raise_()

    # def resizeEvent(self, event):
    #     super().resizeEvent(event)
    #     page = self.stacked_widget.widget(0)  # setup page
    #     if hasattr(self, '_setup_canvas'):
    #         w, h = page.width(), page.height()
    #         self._setup_canvas.setGeometry(0, 0, w, h)
    #         self._setup_scanlines.setGeometry(0, 0, w, h)
    #         self._setup_ring_tl.move(-80, -80)
    #         self._setup_ring_br.move(w - 220, h - 220)
    #         self._setup_canvas.lower()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_setup_canvas'):
            page = self.stacked_widget.widget(0)
            w, h = page.width(), page.height()
            self._setup_canvas.setGeometry(0, 0, w, h)
            self._setup_scanlines.setGeometry(0, 0, w, h)
            self._setup_ring_tl.move(-80, -80)
            self._setup_ring_br.move(w - 220, h - 220)
            self._setup_canvas.lower()
            if hasattr(self, '_setup_corner_labels'):
                tl, tr, bl = self._setup_corner_labels
                tl.move(24, 20)
                tr.adjustSize()
                tr.move(w - tr.width() - 24, 20)
                bl.adjustSize()
                bl.move(24, h - bl.height() - 20)
    
    def showEvent(self, event):
        super().showEvent(event)
        if hasattr(self, '_setup_canvas'):
            self._reposition_setup_bg()

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
            self.setup_status.setText(f"Error: {str(e)[:50]}")
            self.setup_status.setStyleSheet("""
                QLabel {
                    color: #F87171;
                    background: rgba(248, 113, 113, 0.1);
                    padding: 8px;
                    border-radius: 8px;
                    border: 1px solid rgba(248, 113, 113, 0.3);
                }
            """)

    def _open_gns3_project(self, project_id: str, project_name: str):
        import urllib.request, json, subprocess, webbrowser

        if not project_id:
            QMessageBox.warning(self, "No Project ID",
                                "This project has no ID and cannot be opened.")
            return

        reply = QMessageBox.question(
            self,
            "Open Project",
            f"Open project '{project_name}' in GNS3?\n\n"
            f"This will send an open request to the GNS3 server and\n"
            f"open the GNS3 web UI in your browser.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        errors = []

        # Step 1: POST /v2/projects/{id}/open  to tell the server to load it
        for path in [
            f"/v2/projects/{project_id}/open",
            f"/api/v2/projects/{project_id}/open",
        ]:
            try:
                url = f"http://{self.server_ip}:{self.server_port}{path}"
                req = urllib.request.Request(
                    url,
                    data=b"{}",
                    headers={
                        "Content-Type": "application/json",
                        "Accept":        "application/json",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=4) as resp:
                    resp.read()
                errors = []   # success — clear errors
                break
            except urllib.error.HTTPError as e:
                body = ""
                try:
                    body = e.read().decode()
                except Exception:
                    pass
                # 409 = already open — that's fine
                if e.code == 409:
                    break
                errors.append(f"HTTP {e.code}: {body[:120]}")
            except Exception as e:
                errors.append(str(e))

        if errors:
            QMessageBox.warning(
                self, "Server Warning",
                f"Could not open project on server:\n{errors[-1]}\n\n"
                f"Will still try to open the GNS3 UI."
            )

        # Step 2: Open GNS3 web UI in the browser at that project
        web_url = (
            f"http://{self.server_ip}:{self.server_port}"
            f"/#/project/{project_id}"
        )
        try:
            webbrowser.open(web_url)
        except Exception as e:
            QMessageBox.warning(self, "Browser Error", f"Could not open browser:\n{e}")
            return

        # Step 3: Try to also launch the GNS3 desktop GUI if installed
        try:
            subprocess.Popen(
                ["gns3", "--server", f"{self.server_ip}:{self.server_port}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            pass  # GNS3 desktop not in PATH — web UI is enough
        except Exception:
            pass

        # Refresh dashboard after a short delay so status pills update
        QTimer.singleShot(1500, self._refresh_dashboard_stats)

    def _fetch_gns3_stats(self):
        import urllib.request, json, socket
        result = {
            "online": False,
            "projects": [],
            "open_count": 0,
            "closed_count": 0,
            "last_opened_name": "—",
            "error": "",
        }
        if not self.server_ip or not self.server_port:
            result["error"] = "No server configured"
            return result
        try:
            # First do a raw TCP ping to confirm the port is open
            sock = socket.create_connection(
                (self.server_ip, int(self.server_port)), timeout=2
            )
            sock.close()
        except Exception as e:
            result["error"] = f"TCP unreachable: {e}"
            return result

        # GNS3 2.2 uses /v2/projects
        for path in ["/v2/projects", "/api/v2/projects"]:
            try:
                url = f"http://{self.server_ip}:{self.server_port}{path}"
                req = urllib.request.Request(
                    url,
                    headers={"Accept": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=3) as resp:
                    raw = resp.read().decode()
                projects = json.loads(raw)
                if not isinstance(projects, list):
                    continue
                result["online"]   = True
                result["projects"] = projects
                open_p   = [p for p in projects if p.get("status") == "opened"]
                closed_p = [p for p in projects if p.get("status") != "opened"]
                result["open_count"]   = len(open_p)
                result["closed_count"] = len(closed_p)
                if open_p:
                    result["last_opened_name"] = open_p[0].get("name", "—")
                elif projects:
                    result["last_opened_name"] = projects[0].get("name", "—")
                return result
            except Exception as e:
                result["error"] = str(e)
                continue
        return result
    
    def _read_last_topology_meta(self):
        """
        Reads machine_names.txt and pre_Connections.json from the Generated_files folder
        to show a quick summary on the dashboard.
        Returns dict with: machines_count, conn_count, topology, timestamp_str
        """
        import json, datetime
        gui_dir  = os.path.dirname(os.path.abspath(__file__))
        gen_dir  = os.path.join(gui_dir, "VisioGns3", "Generated_files")
        machines_file = os.path.join(gen_dir, "machine_names.txt")
        conns_file    = os.path.join(gen_dir, "pre_Connections.json")

        meta = {"machines_count": 0, "conn_count": 0, "topology": "—", "timestamp_str": "—"}

        try:
            if os.path.exists(machines_file):
                with open(machines_file) as f:
                    lines = [l.strip() for l in f if l.strip()]
                meta["machines_count"] = len(lines)
                ts = os.path.getmtime(machines_file)
                dt = datetime.datetime.fromtimestamp(ts)
                delta = datetime.datetime.now() - dt
                mins = int(delta.total_seconds() // 60)
                if mins < 60:
                    meta["timestamp_str"] = f"{mins} min ago"
                elif mins < 1440:
                    meta["timestamp_str"] = f"{mins // 60}h ago"
                else:
                    meta["timestamp_str"] = dt.strftime("%d %b")
        except Exception:
            pass

        try:
            if os.path.exists(conns_file):
                with open(conns_file) as f:
                    conns = json.load(f)
                meta["conn_count"] = len(conns)
        except Exception:
            pass

        return meta 

    def create_landing_page(self):
        page = QWidget()
        page.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            "stop:0 #0F172A,stop:1 #1E293B);"
        )
        self._read_topology_history()
        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── CARD style (used for every panel and stat card) ──────────────
        CARD_SS = """
            QFrame {
                background: rgba(22,32,52,0.85);
                border: 1px solid rgba(34,211,238,0.18);
                border-radius: 16px;
            }
        """
        # Label helper — no background, no border, no border-radius
        def L(text, style=""):
            w = QLabel(text)
            w.setStyleSheet(style +
                " background:transparent; border:none; border-radius:0;")
            w.setWordWrap(True)
            return w

        # ════════════════════════════════════════════
        # NAV HEADER
        # ════════════════════════════════════════════
        header = QFrame()
        header.setFixedHeight(64)
        header.setStyleSheet("""
            QFrame {
                background: rgba(10,15,30,0.98);
                border-bottom: 1px solid rgba(34,211,238,0.12);
                border-radius: 0;
            }
        """)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(32, 0, 32, 0)
        hl.setSpacing(4)

        logo = QLabel("IN<span style='color:#22D3EE'>DA</span>")
        logo.setTextFormat(Qt.TextFormat.RichText)
        logo.setStyleSheet(
            "color:#FFFFFF; font-size:17px; font-weight:900;"
            "letter-spacing:6px; background:transparent; border:none;"
        )
        hl.addWidget(logo)
        hl.addSpacing(20)

        NAV_ON = """
            QPushButton {
                background: rgba(34,211,238,0.12);
                color: #22D3EE;
                border: 1px solid rgba(34,211,238,0.22);
                border-radius: 8px;
                font-size: 12px; font-weight: 700;
                padding: 0 14px; letter-spacing: 0.5px;
            }
        """
        NAV_OFF = """
            QPushButton {
                background: transparent; color: #64748B;
                border: none; border-radius: 8px;
                font-size: 12px; font-weight: 700;
                padding: 0 14px; letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: rgba(34,211,238,0.08); color: #22D3EE;
            }
        """
        for label, style, cb in [
            ("Dashboard",                NAV_ON,  None),
            ("Instruction Orchestrator", NAV_OFF, self.show_chatbot_page),
            ("Topology Interpreter",     NAV_OFF, self.show_console_page),
            ("Architecture Engine",      NAV_OFF, self.show_architecture_page),
        ]:
            btn = QPushButton(label)
            btn.setFixedHeight(36)
            btn.setStyleSheet(style)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if cb:
                btn.clicked.connect(cb)
            hl.addWidget(btn)

        hl.addStretch()

        # Server badge labels (updated after stats fetch below)
        self._landing_server_dot   = QLabel("●")
        self._landing_server_label = QLabel(
            f"GNS3  {self.server_ip}:{self.server_port}"
        )
        self._landing_server_dot.setStyleSheet(
            "color:#475569; font-size:13px; background:transparent; border:none;"
        )
        self._landing_server_label.setStyleSheet(
            "color:#64748B; font-size:11px; font-weight:700;"
            "letter-spacing:1px; background:transparent; border:none;"
        )
        srv_badge = QFrame()
        srv_badge.setStyleSheet("""
            QFrame {
                background: rgba(15,25,40,0.7);
                border: 1px solid rgba(100,116,139,0.18);
                border-radius: 20px;
            }
        """)
        sbl = QHBoxLayout(srv_badge)
        sbl.setContentsMargins(14, 5, 14, 5)
        sbl.setSpacing(7)
        sbl.addWidget(self._landing_server_dot)
        sbl.addWidget(self._landing_server_label)
        hl.addWidget(srv_badge)
        root.addWidget(header)

        # ════════════════════════════════════════════
        # SCROLLABLE BODY
        # ════════════════════════════════════════════
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background:transparent; border:none;")
        body = QWidget()
        body.setStyleSheet("background:transparent;")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(40, 32, 40, 40)
        bl.setSpacing(0)

        # Title + refresh row
        tr = QHBoxLayout()
        tc = QVBoxLayout()
        tc.setSpacing(3)
        tc.addWidget(L("Dashboard",
            "color:#F8FAFC; font-size:26px; font-weight:800;"))
        tc.addWidget(L("GNS3 server overview & quick access",
            "color:#475569; font-size:13px;"))
        refresh_btn = QPushButton("↻  Refresh")
        refresh_btn.setFixedHeight(36)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: rgba(34,211,238,0.07); color: #22D3EE;
                border: 1px solid rgba(34,211,238,0.18); border-radius: 10px;
                font-size: 12px; font-weight: 700; padding: 0 16px;
            }
            QPushButton:hover {
                background: rgba(34,211,238,0.15); border-color: #22D3EE;
            }
        """)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self._refresh_dashboard_stats)
        tr.addLayout(tc)
        tr.addStretch()
        tr.addWidget(refresh_btn)
        bl.addLayout(tr)
        bl.addSpacing(22)

        # ── Fetch live data ──────────────────────────────
        stats = self._fetch_gns3_stats()
        topo  = self._read_last_topology_meta()

        online_color = "#4ADE80" if stats["online"] else "#F87171"
        self._landing_server_dot.setStyleSheet(
            f"color:{online_color}; font-size:13px; background:transparent; border:none;"
        )

        # ════════════════════════════════════════════
        # STAT CARDS — one QFrame, direct QVBoxLayout children only
        # ════════════════════════════════════════════
        stats_row_layout = QHBoxLayout()
        stats_row_layout.setSpacing(14)

        def make_flat_card(emoji, label, value, sub="", sub_color="#475569"):
            """
            One QFrame. Children added directly to its QVBoxLayout.
            No nested QWidget / QFrame / QHBoxLayout at all.
            """
            card = QFrame()
            card.setMinimumHeight(116)
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            card.setStyleSheet(CARD_SS)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(22, 18, 22, 18)
            cl.setSpacing(5)
            cl.addWidget(L(emoji, "font-size:20px;"))
            cl.addWidget(L(label,
                "color:#475569; font-size:10px; font-weight:800; letter-spacing:2.5px;"))
            fs = "26px" if len(str(value)) <= 6 else "16px"
            cl.addWidget(L(str(value),
                f"color:#F8FAFC; font-size:{fs}; font-weight:800; line-height:1;"))
            if sub:
                cl.addWidget(L(sub, f"color:{sub_color}; font-size:11px;"))
            cl.addStretch()
            return card

        total = len(stats["projects"])
        stats_row_layout.addWidget(
            make_flat_card(
                "📁", "TOTAL PROJECTS", str(total),
                sub="across all topologies",
            ),
            
        )

        stats_row_layout.addWidget(
            make_flat_card(
                "⚡", "OPEN PROJECTS", str(stats["open_count"]),
                sub=f"{stats['closed_count']} closed",
            ),
            
        )

        stats_row_layout.addWidget(
            make_flat_card(
                "🕐", "LAST OPENED",
                (stats["last_opened_name"]
                if stats["last_opened_name"] != "—" else "—"),
                sub="most recently opened",
            ),
            
        )

        # GNS3 status card — dot and text on the same line via a single rich-text label
        srv_card = QFrame()
        srv_card.setMinimumHeight(116)
        srv_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        srv_card.setStyleSheet(CARD_SS)
        scl = QVBoxLayout(srv_card)
        scl.setContentsMargins(22, 18, 22, 18)
        scl.setSpacing(5)
        scl.addWidget(L("🖧", "font-size:20px;"))
        scl.addWidget(L("GNS3 SERVER STATUS",
            "color:#475569; font-size:10px; font-weight:800; letter-spacing:2.5px;"))
        # Use a single RichText label so dot+word share one widget — no nested layout
        srv_status_lbl = QLabel(
            f"<span style='color:{online_color}; font-size:16px;'>●</span>"
            f"&nbsp;&nbsp;"
            f"<span style='color:{online_color}; font-size:17px; font-weight:800;'>"
            f"{'ONLINE' if stats['online'] else 'OFFLINE'}</span>"
        )
        srv_status_lbl.setTextFormat(Qt.TextFormat.RichText)
        srv_status_lbl.setStyleSheet("background:transparent; border:none; border-radius:0;")
        scl.addWidget(srv_status_lbl)
        addr_txt = (f"{self.server_ip}:{self.server_port} · "
                    f"{'responding' if stats['online'] else 'unreachable'}")
        if stats.get("error") and not stats["online"]:
            addr_txt += f"\n{stats['error'][:60]}"
        scl.addWidget(L(addr_txt, "color:#475569; font-size:10px;"))
        scl.addStretch()
        stats_row_layout.addWidget(srv_card)

        bl.addLayout(stats_row_layout)
        bl.addSpacing(20)

        # ── Topology complexity chart panel ───────────
        history = self._read_topology_history()
        chart_panel = QFrame()
        chart_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        chart_panel.setMinimumHeight(260)
        chart_panel.setStyleSheet(CARD_SS)
        chart_layout = QVBoxLayout(chart_panel)
        chart_layout.setContentsMargins(22, 18, 22, 18)
        chart_layout.setSpacing(12)

        chart_header = QHBoxLayout()
        chart_header.addWidget(L("TOPOLOGY COMPLEXITY OVER TIME",
            "color:#475569; font-size:10px; font-weight:800; letter-spacing:2px;"))
        chart_header.addStretch()
        chart_header.addWidget(L(f"{len(history)} runs",
            "color:#38BDF8; font-size:10px; font-weight:700;"))
        chart_layout.addLayout(chart_header)

        chart_view = self._create_complexity_chart_widget(history)
        chart_layout.addWidget(chart_view)
        bl.addWidget(chart_panel)
        bl.addSpacing(20)

        # ════════════════════════════════════════════
        # BOTTOM PANELS
        # ════════════════════════════════════════════
        panels_row = QHBoxLayout()
        panels_row.setSpacing(18)

        # ── Left: last topology preview ──────────────
        topo_panel = QFrame()
        topo_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        topo_panel.setStyleSheet(CARD_SS)
        tpl = QVBoxLayout(topo_panel)
        tpl.setContentsMargins(22, 20, 22, 20)
        tpl.setSpacing(12)
        tpl.addWidget(L("LAST TOPOLOGY PREVIEW",
            "color:#475569; font-size:10px; font-weight:800; letter-spacing:2px;"))

        preview_text = (
            f"  Machines : {topo['machines_count']}\n"
            f"  Links    : {topo['conn_count']}\n"
            f"  When     : {topo['timestamp_str']}"
            if topo["machines_count"] > 0
            else "  No topology generated yet.\n  Run the Architecture Engine."
        )
        term = QTextEdit()
        term.setReadOnly(True)
        term.setFixedHeight(116)
        term.setPlainText(preview_text)
        term.setStyleSheet("""
            QTextEdit {
                background: rgba(8,16,28,0.8);
                color: #FFFFFF;
                border: 1px solid rgba(56,189,248,0.1);
                border-radius: 8px;
                padding: 12px 14px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        tpl.addWidget(term)

        tags_row = QHBoxLayout()
        tags_row.setSpacing(8)
        for tag_text in [f"{topo['machines_count']} Devices",
                        f"{topo['conn_count']} Links",
                        topo["timestamp_str"]]:
            tg = QLabel(tag_text)
            tg.setStyleSheet(
                "color:#22D3EE; background:rgba(34,211,238,0.07);"
                "border:1px solid rgba(34,211,238,0.15); border-radius:8px;"
                "font-size:10px; font-weight:800; padding:3px 10px; letter-spacing:.5px;"
            )
            tags_row.addWidget(tg)
        tags_row.addStretch()
        tpl.addLayout(tags_row)
        tpl.addStretch()

        # ── Right: ALL projects, scrollable ──────────
        proj_panel = QFrame()
        proj_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        proj_panel.setStyleSheet(CARD_SS)
        ppl = QVBoxLayout(proj_panel)
        ppl.setContentsMargins(22, 20, 22, 20)
        ppl.setSpacing(10)

        ph = QHBoxLayout()
        ph.addWidget(L("ALL GNS3 PROJECTS",
            "color:#475569; font-size:10px; font-weight:800; letter-spacing:2px;"))
        ph.addStretch()
        ph.addWidget(L(f"{total} total",
            "color:#475569; font-size:10px; font-weight:700;"))
        ppl.addLayout(ph)

        proj_scroll_area = QScrollArea()
        proj_scroll_area.setWidgetResizable(True)
        proj_scroll_area.setFixedHeight(220)
        proj_scroll_area.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                background: rgba(30,41,59,0.3); width: 5px; border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: rgba(34,211,238,0.25); border-radius: 3px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        proj_container = QWidget()
        proj_container.setStyleSheet("background:transparent;")
        pcl = QVBoxLayout(proj_container)
        pcl.setContentsMargins(0, 0, 4, 0)
        pcl.setSpacing(7)

        all_projects = stats["projects"]
        if not all_projects:
            err_msg = stats.get("error", "No projects or server unreachable.")
            pcl.addWidget(L(
                f"No projects found.\n{err_msg}",
                "color:#475569; font-size:12px;"
            ))
        else:
            for proj in all_projects:
                pname   = proj.get("name", "Unnamed")
                pid     = proj.get("project_id", "")
                is_open = proj.get("status") == "opened"

                # Each row is a QFrame with ONE QHBoxLayout — no nested frames
                row = QFrame()
                row.setStyleSheet("""
                    QFrame {
                        background: rgba(10,18,35,0.6);
                        border: 1px solid rgba(100,116,139,0.1);
                        border-radius: 10px;
                    }
                    QFrame:hover {
                        border: 1px solid rgba(34,211,238,0.35);
                        background: rgba(10,18,35,0.9);
                    }
                """)
                row.setCursor(Qt.CursorShape.PointingHandCursor)

                rl = QHBoxLayout(row)
                rl.setContentsMargins(12, 8, 12, 8)
                rl.setSpacing(10)

                # Icon — plain QLabel, no wrapper
                icon_l = QLabel("⚡" if is_open else "📁")
                icon_l.setStyleSheet("font-size:14px; background:transparent; border:none;")

                # Name — plain QLabel, no wrapper
                name_l = QLabel(pname)
                name_l.setStyleSheet(
                    "color:#CBD5E1; font-size:13px; font-weight:600;"
                    "background:transparent; border:none;"
                )
                name_l.setMaximumWidth(240)

                # Status pill — plain QLabel, no wrapper
                status_l = QLabel("OPEN" if is_open else "CLOSED")
                status_l.setStyleSheet(
                    ("color:#4ADE80; background:rgba(74,222,128,0.1);"
                    "border:1px solid rgba(74,222,128,0.22);"
                    if is_open else
                    "color:#64748B; background:rgba(100,116,139,0.1);"
                    "border:1px solid rgba(100,116,139,0.18);")
                    + "border-radius:20px; font-size:9px; font-weight:800;"
                    "padding:2px 8px; letter-spacing:.5px;"
                )

                # Open button — plain QPushButton, no wrapper
                open_btn = QPushButton("Open ↗")
                open_btn.setFixedHeight(24)
                open_btn.setFixedWidth(66)
                open_btn.setStyleSheet("""
                    QPushButton {
                        background: transparent; color: #22D3EE;
                        border: none; font-size: 11px; font-weight: 800;
                        padding: 0; letter-spacing: .5px;
                    }
                    QPushButton:hover { color: #67E8F9; }
                """)
                open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                open_btn.clicked.connect(
                    lambda _checked, _id=pid, _n=pname:
                        self._open_gns3_project(_id, _n)
                )

                rl.addWidget(icon_l)
                rl.addWidget(name_l)
                rl.addStretch()
                rl.addWidget(status_l)
                rl.addWidget(open_btn)

                row.mousePressEvent = (
                    lambda _e, _id=pid, _n=pname:
                        self._open_gns3_project(_id, _n)
                )

                pcl.addWidget(row)

        pcl.addStretch()
        proj_scroll_area.setWidget(proj_container)
        ppl.addWidget(proj_scroll_area)

        panels_row.addWidget(topo_panel, 45)
        panels_row.addWidget(proj_panel, 55)
        bl.addLayout(panels_row)
        bl.addSpacing(24)

        # ════════════════════════════════════════════
        # WORKFLOW CARDS
        # ════════════════════════════════════════════
        bl.addWidget(L("Workflows",
            "color:#475569; font-size:10px; font-weight:800; letter-spacing:3px;"))
        bl.addSpacing(10)

        wf_row = QHBoxLayout()
        wf_row.setSpacing(14)

        for emoji, title, desc, color, cb in [
            ("🤖", "Instruction Orchestrator",
            "Natural language topology generation", "#3B82F6", self.show_chatbot_page),
            ("📊", "Topology Interpreter",
            "Upload Visio / XML / SVG files",       "#8B5CF6", self.show_console_page),
            ("🏢", "Architecture Engine",
            "Design from building parameters",       "#06B6D4", self.show_architecture_page),
        ]:
            wcard = QFrame()
            wcard.setMinimumHeight(168)
            wcard.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            wcard.setStyleSheet(f"""
                QFrame {{
                    background: rgba(22,32,52,0.85);
                    border: 1px solid rgba(34,211,238,0.18);
                    border-radius: 16px;
                }}
                QFrame:hover {{
                    background: rgba(22,32,52,1);
                    border: 1px solid {color};
                }}
            """)
            wcard.setCursor(Qt.CursorShape.PointingHandCursor)
            wcard.mousePressEvent = lambda _e, _cb=cb: _cb()

            wl = QVBoxLayout(wcard)
            wl.setContentsMargins(22, 20, 22, 20)
            wl.setSpacing(7)
            wl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            for text, style in [
                (emoji, "font-size:28px;"),
                (title, "color:#E2E8F0; font-size:14px; font-weight:700;"),
                (desc,  "color:#475569; font-size:12px;"),
                ("→",   f"color:{color}; font-size:20px;"),
            ]:
                lb = QLabel(text)
                lb.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lb.setWordWrap(True)
                lb.setStyleSheet(style + " background:transparent; border:none;")
                wl.addWidget(lb)

            wf_row.addWidget(wcard)

        bl.addLayout(wf_row)
        bl.addStretch()

        scroll.setWidget(body)
        root.addWidget(scroll)
        self._landing_page_ref = page
        return page

    def _refresh_dashboard_stats(self):
        new_page = self.create_landing_page()
        old_idx  = self.stacked_widget.indexOf(self.landing_page)
        self.stacked_widget.removeWidget(self.landing_page)
        self.landing_page.deleteLater()
        self.landing_page = new_page
        self.stacked_widget.insertWidget(old_idx, new_page)
        self.stacked_widget.setCurrentIndex(old_idx)

    def create_card(self, emoji, title, desc, color, callback):
        card = QFrame()
        card.setMinimumHeight(300)
        card.setMinimumWidth(310)
        card.setMaximumWidth(360)
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
                <div style="font-size: 44px;">{emoji}</div>
                <div style="color: #F8FAFC; font-size: 20px; font-weight: 700; margin: 16px 0;">{title}</div>
                <div style="color: #94A3B8; font-size: 14px; line-height: 1.6; margin-bottom: 24px;">{desc}</div>
                <div style="color: {color}; font-size: 28px;">→</div>
            </div>
        """)
        content_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_label.setWordWrap(True)
        content_label.setStyleSheet("background: transparent; padding: 36px;")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(content_label)
        
        card.setLayout(layout)
        card.mousePressEvent = lambda e: callback()
        return card
    def _validate_arch_project_name(self):
        arch_proj_name = self.arch_project_name_input.text().strip()

        # Empty check
        if not arch_proj_name:
            QMessageBox.warning(self, "Project Name Required",
                                "Please enter a project name before confirming.")
            return

        # Server duplicate check
        if self.server_ip and self.server_port:
            try:
                import urllib.request, json as _json
                existing_names = []
                for path in ["/v2/projects", "/api/v2/projects"]:
                    try:
                        url = f"http://{self.server_ip}:{self.server_port}{path}"
                        with urllib.request.urlopen(
                            urllib.request.Request(url, headers={"Accept": "application/json"}),
                            timeout=3
                        ) as resp:
                            projects = _json.loads(resp.read().decode())
                        if isinstance(projects, list):
                            existing_names = [p.get("name", "") for p in projects]
                            break
                    except Exception:
                        continue

                if arch_proj_name in existing_names:
                    QMessageBox.warning(
                        self,
                        "Project Name Already Exists",
                        f"A project named '{arch_proj_name}' already exists on the GNS3 server.\n\n"
                        f"Please choose a different name."
                    )
                    self.arch_project_name_input.setFocus()
                    self.arch_project_name_input.selectAll()
                    self._set_arch_proj_status("taken")
                    return

            except Exception:
                pass  # Server unreachable — skip check

        # All good
        self._set_arch_proj_status("ok")

        # Save to file
        vsdx_path = os.path.join(
            os.path.expanduser("~"), "INDA", "VisioGns3", "vsdx_path.txt"
        )
        os.makedirs(os.path.dirname(vsdx_path), exist_ok=True)
        with open(vsdx_path, "w") as f:
            f.write(arch_proj_name)
        self._arch_log(f"📁  Project name confirmed & saved: {arch_proj_name}", "#4ADE80")


    def _create_complexity_chart_widget(self, history: list) -> QWebEngineView:
        """Returns a QWebEngineView with the topology complexity chart."""
        import json
        
        if history:
            labels = [entry["timestamp"][:16].replace("T", " ") for entry in history]
            data   = [entry["connection_count"] for entry in history]
        else:
            # Demo data so the chart doesn't show empty on first launch
            labels = ["No data yet"]
            data   = [0]

        labels_js = json.dumps(labels)
        data_js   = json.dumps(data)

        html = f"""<!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    html, body {{ background: transparent; width:100%; height:100%; }}
    body {{ padding: 4px 0; }}
    #wrap {{ position: relative; width: 100%; height: 200px; }}
    </style>
    </head>
    <body>
    <div id="wrap">
    <canvas id="cx" role="img" aria-label="Line chart of topology complexity over time, showing number of connections per generated topology.">Topology complexity history: {len(history)} entries.</canvas>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
    <script>
    const labels = {labels_js};
    const data   = {data_js};
    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    new Chart(document.getElementById('cx'), {{
    type: 'line',
    data: {{
        labels,
        datasets: [{{
        label: 'Connections',
        data,
        borderColor:     '#38BDF8',
        backgroundColor: 'rgba(56,189,248,0.12)',
        pointBackgroundColor: '#0EA5E9',
        pointBorderColor:    '#38BDF8',
        pointRadius: 5,
        pointHoverRadius: 7,
        borderWidth: 2.5,
        fill: true,
        tension: 0.4,
        }}]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
        legend: {{ display: false }},
        tooltip: {{
            backgroundColor: '#0F172A',
            borderColor: '#38BDF8',
            borderWidth: 1,
            titleColor: '#7DD3FC',
            bodyColor: '#E2E8F0',
            padding: 10,
            callbacks: {{
            label: ctx => `${{ctx.parsed.y}} connections`
            }}
        }}
        }},
        scales: {{
        x: {{
            ticks: {{
            color: '#475569',
            font: {{ size: 10 }},
            maxRotation: 30,
            autoSkip: true,
            maxTicksLimit: 6,
            }},
            grid: {{ color: 'rgba(71,85,105,0.2)' }},
            border: {{ color: 'rgba(71,85,105,0.3)' }}
        }},
        y: {{
            beginAtZero: true,
            ticks: {{
            color: '#475569',
            font: {{ size: 10 }},
            stepSize: 1,
            }},
            grid: {{ color: 'rgba(71,85,105,0.2)' }},
            border: {{ color: 'rgba(71,85,105,0.3)' }}
        }}
        }}
    }}
    }});
    </script>
    </body>
    </html>"""

        view = QWebEngineView()
        view.setFixedHeight(220)
        view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        view.setStyleSheet("background: transparent;")
        view.setHtml(html)
        return view

    def _set_arch_proj_status(self, state: str):
        """Updates the small status label next to the architecture project name field."""
        if state == "ok":
            self.arch_proj_status.setText("✔  Name confirmed")
            self.arch_proj_status.setStyleSheet(
                "color: #4ADE80; font-size: 12px; font-weight: 700;"
                "background: transparent; border: none;"
            )
            self.arch_proj_ok_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(74, 222, 128, 0.15);
                    color: #4ADE80;
                    border: 1px solid rgba(74, 222, 128, 0.45);
                    border-radius: 10px;
                    font-size: 13px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background: rgba(74, 222, 128, 0.28);
                }
            """)
        elif state == "taken":
            self.arch_proj_status.setText("✘  Name already taken")
            self.arch_proj_status.setStyleSheet(
                "color: #F87171; font-size: 12px; font-weight: 700;"
                "background: transparent; border: none;"
            )
            self.arch_proj_ok_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(248, 113, 113, 0.12);
                    color: #F87171;
                    border: 1px solid rgba(248, 113, 113, 0.35);
                    border-radius: 10px;
                    font-size: 13px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background: rgba(248, 113, 113, 0.25);
                }
            """)
        else:  # reset
            self.arch_proj_status.setText("")
            self.arch_proj_status.setStyleSheet("background: transparent; border: none;")
            self.arch_proj_ok_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(34, 211, 238, 0.10);
                    color: #22D3EE;
                    border: 1px solid rgba(34, 211, 238, 0.30);
                    border-radius: 10px;
                    font-size: 13px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background: rgba(34, 211, 238, 0.22);
                    border: 1px solid #22D3EE;
                }
            """)
    def create_architecture_page(self):
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
                background: rgba(6, 182, 212, 0.1);
                color: #22D3EE;
                border: 1px solid rgba(6, 182, 212, 0.3);
                border-radius: 22px;
                font-size: 14px;
                font-weight: 600;
                padding: 0 20px;
            }
            QPushButton:hover {
                background: rgba(6, 182, 212, 0.2);
                border: 1px solid #22D3EE;
            }
        """)
        back_btn.clicked.connect(self.show_landing_page)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        title = QLabel("Architecture Abstraction Engine")
        title.setStyleSheet("color: #F8FAFC; font-size: 26px; font-weight: 700; background: transparent;")

        badge = QLabel("🏢 Building Designer")
        badge.setStyleSheet("""
            color: #22D3EE;
            font-size: 13px;
            font-weight: 600;
            padding: 6px 14px;
            background: rgba(6, 182, 212, 0.1);
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
        c_layout.setSpacing(28)

        # Form header (directly in content, no wrapping container)
        form_layout = c_layout

        form_title = QLabel("🏗️  Building Configuration")
        form_title.setStyleSheet("color: #22D3EE; font-size: 18px; font-weight: 700; background: transparent;")

        form_desc = QLabel("Define your building parameters to generate an optimal network topology.")
        form_desc.setStyleSheet("color: #64748B; font-size: 14px; background: transparent;")
        form_desc.setWordWrap(True)

        form_layout.addWidget(form_title)
        form_layout.addWidget(form_desc)
        # ── Project Name ──────────────────────────────────────────────
        arch_proj_row = QHBoxLayout()
        arch_proj_label = QLabel("📁  Project Name")
        arch_proj_label.setStyleSheet(
            "color: #CBD5E1; font-size: 14px; font-weight: 600; background: transparent;"
        )
        arch_proj_label.setFixedWidth(160)

        self.arch_project_name_input = QLineEdit()
        self.arch_project_name_input.setPlaceholderText("Enter project name (e.g. OfficeNetwork)")
        self.arch_project_name_input.setMinimumHeight(46)
        self.arch_project_name_input.setStyleSheet("""
            QLineEdit {
                background: rgba(15, 23, 42, 0.8);
                color: #F8FAFC;
                border: 2px solid rgba(100, 116, 139, 0.3);
                border-radius: 10px;
                padding: 0 14px;
                font-size: 15px;
            }
            QLineEdit:focus {
                border: 2px solid #22D3EE;
            }
        """)
        self.arch_proj_ok_btn = QPushButton("OK")
        self.arch_proj_ok_btn.setFixedHeight(46)
        self.arch_proj_ok_btn.setFixedWidth(70)
        self.arch_proj_ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.arch_proj_ok_btn.setStyleSheet("""
            QPushButton {
                background: rgba(34, 211, 238, 0.10);
                color: #22D3EE;
                border: 1px solid rgba(34, 211, 238, 0.30);
                border-radius: 10px;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: rgba(34, 211, 238, 0.22);
                border: 1px solid #22D3EE;
            }
            QPushButton:pressed {
                background: rgba(34, 211, 238, 0.38);
            }
        """)
        self.arch_proj_ok_btn.clicked.connect(self._validate_arch_project_name)

        self.arch_proj_status = QLabel("")
        self.arch_proj_status.setStyleSheet(
            "background: transparent; border: none; font-size: 12px; font-weight: 700;"
        )

        arch_proj_row.addWidget(arch_proj_label)
        arch_proj_row.addWidget(self.arch_project_name_input)
        self.arch_project_name_input.textChanged.connect(
            lambda: self._set_arch_proj_status("reset")
        )
        arch_proj_row.addWidget(self.arch_proj_ok_btn)
        form_layout.addLayout(arch_proj_row)
        form_layout.addWidget(self.arch_proj_status)
        # ─────────────────────────────────────────────────────────────
        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background: rgba(6, 182, 212, 0.15); border: none; max-height: 1px;")
        form_layout.addWidget(divider)

        # Field style helpers
        label_style = "color: #CBD5E1; font-size: 14px; font-weight: 600; background: transparent;"
        hint_style = "color: #475569; font-size: 12px; background: transparent;"


        # ── Row 1: Floors + Rooms per floor ──
        row1 = QHBoxLayout()
        row1.setSpacing(30)

        # Number of floors
        floors_col = QVBoxLayout()
        floors_col.setSpacing(6)
        floors_label = QLabel("🏢  Number of Floors")
        floors_label.setStyleSheet(label_style)
        floors_hint = QLabel("Maximum: 5 floors")
        floors_hint.setStyleSheet(hint_style)
        self.floors_spin = StyledSpinBox(minimum=1, maximum=5, value=1)
        self.floors_spin.setMinimumWidth(200)
        floors_col.addWidget(floors_label)
        floors_col.addWidget(floors_hint)
        floors_col.addWidget(self.floors_spin)

        # Rooms per floor
        rooms_col = QVBoxLayout()
        rooms_col.setSpacing(6)
        rooms_label = QLabel("🚪  Rooms Per Floor")
        rooms_label.setStyleSheet(label_style)
        rooms_hint = QLabel("Maximum: 10 rooms")
        rooms_hint.setStyleSheet(hint_style)
        self.rooms_spin = StyledSpinBox(minimum=1, maximum=10, value=1)
        self.rooms_spin.setMinimumWidth(200)
        rooms_col.addWidget(rooms_label)
        rooms_col.addWidget(rooms_hint)
        rooms_col.addWidget(self.rooms_spin)

        row1.addLayout(floors_col)
        row1.addLayout(rooms_col)
        form_layout.addLayout(row1)

        # ── Row 2: Avg users + Building width ──
        row2 = QHBoxLayout()
        row2.setSpacing(30)

        # Average users per room
        users_col = QVBoxLayout()
        users_col.setSpacing(6)
        users_label = QLabel("👤  Average Users Per Room")
        users_label.setStyleSheet(label_style)
        users_hint = QLabel("Maximum: 20 users")
        users_hint.setStyleSheet(hint_style)
        self.users_spin = StyledSpinBox(minimum=1, maximum=20, value=1)
        self.users_spin.setMinimumWidth(200)
        users_col.addWidget(users_label)
        users_col.addWidget(users_hint)
        users_col.addWidget(self.users_spin)

        # Building width
        width_col = QVBoxLayout()
        width_col.setSpacing(6)
        width_label = QLabel("📐  Building Width")
        width_label.setStyleSheet(label_style)
        width_hint = QLabel("Enter value and select unit")
        width_hint.setStyleSheet(hint_style)

        width_input_row = QHBoxLayout()
        width_input_row.setSpacing(10)

        self.width_input = QLineEdit()
        self.width_input.setPlaceholderText("e.g., 50")
        self.width_input.setMinimumHeight(46)
        self.width_input.setStyleSheet("""
            QLineEdit {
                background: rgba(15, 23, 42, 0.8);
                color: #F8FAFC;
                border: 2px solid rgba(100, 116, 139, 0.3);
                border-radius: 10px;
                padding: 0 14px;
                font-size: 15px;
            }
            QLineEdit:focus {
                border: 2px solid #22D3EE;
            }
        """)

        self.width_unit_combo = StyledComboBox(items=["Feet", "Square Meters", "Meters"])
        self.width_unit_combo.setMinimumHeight(46)
        self.width_unit_combo.setMinimumWidth(180)

        width_input_row.addWidget(self.width_input)
        width_input_row.addWidget(self.width_unit_combo)

        width_col.addWidget(width_label)
        width_col.addWidget(width_hint)
        width_col.addLayout(width_input_row)

        row2.addLayout(users_col)
        row2.addLayout(width_col)
        form_layout.addLayout(row2)

        # ── Row 3: Building type (full width) ──
        type_col = QVBoxLayout()
        type_col.setSpacing(6)
        type_label = QLabel("🏗️  Building Type")
        type_label.setStyleSheet(label_style)
        type_hint = QLabel("Select the primary use of the building")
        type_hint.setStyleSheet(hint_style)
        self.building_type_combo = StyledComboBox(items=["Office", "Hospital", "School / University", "Hotel"])
        self.building_type_combo.setMinimumHeight(46)
        type_col.addWidget(type_label)
        type_col.addWidget(type_hint)
        type_col.addWidget(self.building_type_combo)
        form_layout.addLayout(type_col)

        # ── Row 4: Performance Metrics ──
        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(30)

        # Cost Priority
        cost_col = QVBoxLayout()
        cost_col.setSpacing(6)

        cost_label = QLabel("💰 Cost Priority")
        cost_label.setStyleSheet(label_style)

        cost_hint = QLabel("Importance of minimizing cost")
        cost_hint.setStyleSheet(hint_style)

        self.cost_combo = StyledComboBox(items=["Low", "Medium", "High"])
        self.cost_combo.setMinimumHeight(46)

        cost_col.addWidget(cost_label)
        cost_col.addWidget(cost_hint)
        cost_col.addWidget(self.cost_combo)


        # Speed Requirement
        speed_col = QVBoxLayout()
        speed_col.setSpacing(6)

        speed_label = QLabel("⚡ Speed Requirement")
        speed_label.setStyleSheet(label_style)

        speed_hint = QLabel("Required network performance")
        speed_hint.setStyleSheet(hint_style)

        self.speed_combo = StyledComboBox(items=["Low", "Medium", "High"])
        self.speed_combo.setMinimumHeight(46)

        speed_col.addWidget(speed_label)
        speed_col.addWidget(speed_hint)
        speed_col.addWidget(self.speed_combo)


        # Reliability Requirement
        reliability_col = QVBoxLayout()
        reliability_col.setSpacing(6)

        reliability_label = QLabel("🛡 Reliability Requirement")
        reliability_label.setStyleSheet(label_style)

        reliability_hint = QLabel("Network fault tolerance importance")
        reliability_hint.setStyleSheet(hint_style)

        self.reliability_combo = StyledComboBox(items=["Low", "Medium", "High"])
        self.reliability_combo.setMinimumHeight(46)

        reliability_col.addWidget(reliability_label)
        reliability_col.addWidget(reliability_hint)
        reliability_col.addWidget(self.reliability_combo)


        metrics_row.addLayout(cost_col)
        metrics_row.addLayout(speed_col)
        metrics_row.addLayout(reliability_col)

        form_layout.addLayout(metrics_row)

        # ── Row 5: Server Checklist ──
        self.server_map = {
            "Office": ["file_server", "mail_server", "backup_server", "vpn_server"],
            "Hospital": ["emr_server", "lab_server", "radiology_server", "pharmacy_server"],
            "School / University": ["lms_server", "exam_server", "library_server", "research_server"],
            "Hotel": ["booking_server", "guest_management_server", "billing_server", "cctv_server"]
        }

        server_col = QVBoxLayout()
        server_label = QLabel("🖥️ Servers")
        server_label.setStyleSheet(label_style)
        self.server_checkboxes = []
        self.server_container = QVBoxLayout()
        server_col.addWidget(server_label)
        server_col.addLayout(self.server_container)
        form_layout.addLayout(server_col)

        self.building_type_combo.currentIndexChanged.connect(self.update_server_checklist)
        self.update_server_checklist()  # initial

        # ── Row 6: Firewall Toggle ──
        firewall_col = QVBoxLayout()
        firewall_col.setSpacing(6)

        firewall_label = QLabel("🛡️  Firewall")
        firewall_label.setStyleSheet(label_style)

        firewall_hint = QLabel("Enable firewall for perimeter network security")
        firewall_hint.setStyleSheet(hint_style)
        
        # Toggle Switch
        self.firewall_toggle = ToggleSwitch("Enable Firewall")

        # Label beside toggle
        toggle_text = QLabel("Enable Firewall")
        toggle_text.setStyleSheet("color: #CBD5E1; font-weight: 600; font-size: 14px;")
        toggle_text.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        # Horizontal layout for toggle + text
        toggle_row = QHBoxLayout()
        toggle_row.setSpacing(12)
        toggle_row.addWidget(self.firewall_toggle)
        toggle_row.addWidget(toggle_text)
        toggle_row.addStretch()

        firewall_col.addWidget(firewall_label)
        firewall_col.addWidget(firewall_hint)
        firewall_col.addLayout(toggle_row)

        form_layout.addLayout(firewall_col)

        # Start Engine button
        start_btn = QPushButton("⚙️   Start Engine")
        start_btn.setMinimumHeight(60)
        start_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0891B2, stop:1 #06B6D4);
                color: #FFFFFF;
                border: none;
                border-radius: 14px;
                font-size: 17px;
                font-weight: 700;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0E7490, stop:1 #0891B2);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #164E63, stop:1 #0E7490);
            }
        """)
        start_btn.clicked.connect(self.start_architecture_engine)
        start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_shadow(start_btn)

        c_layout.addWidget(start_btn)

        # ── AP Placement Download Button ─────────────────────────────────────
        self.ap_download_btn = QPushButton("📥  Download AP Placement Plan")
        self.ap_download_btn.setMinimumHeight(50)
        self.ap_download_btn.setVisible(False)          # hidden until engine runs
        self.ap_download_btn.setStyleSheet("""
            QPushButton {
                background: rgba(34, 211, 238, 0.08);
                color: #22D3EE;
                border: 1px solid rgba(34, 211, 238, 0.35);
                border-radius: 12px;
                font-size: 15px;
                font-weight: 700;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: rgba(34, 211, 238, 0.18);
                border: 1px solid #22D3EE;
            }
            QPushButton:pressed {
                background: rgba(34, 211, 238, 0.30);
            }
            QPushButton:disabled {
                background: rgba(100, 116, 139, 0.08);
                color: #475569;
                border: 1px solid rgba(100, 116, 139, 0.2);
            }
        """)
        self.ap_download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ap_download_btn.clicked.connect(self._download_ap_placement)
        self.add_shadow(self.ap_download_btn)
        c_layout.addWidget(self.ap_download_btn)


        # ── Terminal Output Panel ──────────────────────────────────────────
        terminal_header = QHBoxLayout()

        terminal_label = QLabel(">_  Engine Output")
        terminal_label.setStyleSheet(
            "color: #22D3EE; font-size: 15px; font-weight: 700; background: transparent;"
        )

        self.arch_clear_btn = QPushButton("Clear")
        self.arch_clear_btn.setFixedHeight(30)
        self.arch_clear_btn.setStyleSheet("""
            QPushButton {
                background: rgba(6, 182, 212, 0.08);
                color: #94A3B8;
                border: 1px solid rgba(100, 116, 139, 0.25);
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
                padding: 0 14px;
            }
            QPushButton:hover { background: rgba(6, 182, 212, 0.18); color: #22D3EE; }
        """)
        self.arch_clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.arch_clear_btn.clicked.connect(lambda: self.arch_terminal.clear())

        self.arch_status_dot = QLabel("●")
        self.arch_status_dot.setStyleSheet("color: #475569; font-size: 18px; background: transparent;")

        terminal_header.addWidget(self.arch_status_dot)
        terminal_header.addSpacing(6)
        terminal_header.addWidget(terminal_label)
        terminal_header.addStretch()
        terminal_header.addWidget(self.arch_clear_btn)

        c_layout.addLayout(terminal_header)

        self.arch_terminal = QTextEdit()
        self.arch_terminal.setReadOnly(True)
        self.arch_terminal.setMinimumHeight(280)
        self.arch_terminal.setStyleSheet("""
            QTextEdit {
                background: #0A0F1A;
                color: #A8FF78;
                border: 1px solid rgba(6, 182, 212, 0.25);
                border-radius: 12px;
                padding: 16px 20px;
                font-family: 'Courier New', 'Consolas', monospace;
                font-size: 13px;
                line-height: 1.6;
            }
            QScrollBar:vertical {
                background: rgba(30, 41, 59, 0.5);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(34, 211, 238, 0.3);
                border-radius: 4px;
            }
        """)
        self.arch_terminal.setPlaceholderText("Engine output will appear here...")
        c_layout.addWidget(self.arch_terminal)

        c_layout.addStretch()
        content.setLayout(c_layout)

        # Put content inside a scroll area so the form doesn't get cut off
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        scroll.setStyleSheet("background: transparent; border: none;")

        layout.addWidget(header)
        layout.addWidget(scroll)
        page.setLayout(layout)
        return page

    def update_server_checklist(self, index=None):
        """Refresh the server checkbox list based on selected building type."""
        # Clear existing widgets in the server container layout
        while self.server_container.count():
            item = self.server_container.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        self.server_checkboxes = []

        # Determine selected building type text
        try:
            btype = self.building_type_combo._combo.currentText()
        except Exception:
            # fallback if called with index or styled combo doesn't expose _combo
            if isinstance(index, int):
                try:
                    btype = self.building_type_combo._combo.itemText(index)
                except Exception:
                    btype = None
            else:
                btype = None

        servers = self.server_map.get(btype, []) if btype else []
        accent = "#22D3EE"
        border_gray = "rgba(100, 116, 139, 0.45)"
        checkbox_css = f"""
QCheckBox {{
    color: #CBD5E1;
    spacing: 12px;
    font-weight: 600;
    font-size: 13px;
}}
QCheckBox::indicator {{
    width: 20px;
    height: 20px;
    border: 2px solid {border_gray};
    border-radius: 4px;
    background: transparent;
}}
QCheckBox::indicator:checked {{
    background: {accent};
    border: 2px solid {accent};
    image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><polyline points='20 6 9 17 4 12' fill='none' stroke='white' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/></svg>");
}}
QCheckBox::indicator:unchecked:hover {{
    border: 2px solid rgba(34,211,238,0.35);
}}
"""

        for s in servers:
            cb = QCheckBox(s.replace('_', ' ').title())
            cb.setStyleSheet(checkbox_css)
            cb.setChecked(False)
            cb.setCursor(Qt.CursorShape.PointingHandCursor)
            cb.setMinimumHeight(26)
            cb.setProperty('server_key', s)
            self.server_container.addWidget(cb)
            self.server_checkboxes.append(cb)

    def _arch_log(self, text: str, color: str = "#A8FF78"):
        import html
        escaped = html.escape(str(text))

        if any(k in text for k in ["✅", "SUCCESS", "success"]):
            color = "#4ADE80"
        elif any(k in text for k in ["❌", "ERROR", "Error", "error", "FAILED", "failed"]):
            color = "#F87171"
        elif any(k in text for k in ["⚠️", "WARNING", "Warning", "warning"]):
            color = "#FBBF24"
        elif any(k in text for k in ["🔧", "🚀", "📡", "📋", "INFO", "[INFO]"]):
            color = "#60A5FA"
        elif text.startswith("──") or text.startswith("=="):
            color = "#475569"

        self.arch_terminal.append(
            f"<span style='color:{color}; white-space:pre;'>{escaped}</span>"
        )
        self.arch_terminal.verticalScrollBar().setValue(
            self.arch_terminal.verticalScrollBar().maximum()
        )

    def start_architecture_engine(self):
        # ── Clear terminal & set status ──────────────────────────────────
        self.arch_terminal.clear()
        self.arch_status_dot.setStyleSheet(
            "color: #FBBF24; font-size: 18px; background: transparent;"
        )
        self._arch_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        self._arch_log("  🚀  Architecture Abstraction Engine  —  Starting")
        self._arch_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        # Save project name
        # Save project name
        arch_proj_name = self.arch_project_name_input.text().strip()
        if not arch_proj_name:
            self._arch_log("❌  Please enter a Project Name before starting.", "#F87171")
            self.arch_status_dot.setStyleSheet(
                "color: #F87171; font-size: 18px; background: transparent;"
            )
            return

        if "confirmed" not in self.arch_proj_status.text():
            self._arch_log(
                "❌  Click OK next to the project name to confirm it is unique before starting.",
                "#F87171"
            )
            self.arch_status_dot.setStyleSheet(
                "color: #F87171; font-size: 18px; background: transparent;"
            )
            return

        # Check if project already exists on the GNS3 server
        if self.server_ip and self.server_port:
            try:
                import urllib.request, json as _json
                for path in ["/v2/projects", "/api/v2/projects"]:
                    try:
                        url = f"http://{self.server_ip}:{self.server_port}{path}"
                        with urllib.request.urlopen(
                            urllib.request.Request(url, headers={"Accept": "application/json"}),
                            timeout=3
                        ) as resp:
                            projects = _json.loads(resp.read().decode())
                        if isinstance(projects, list):
                            existing_names = [p.get("name", "") for p in projects]
                            if arch_proj_name in existing_names:
                                self._arch_log(
                                    f"❌  A project named '{arch_proj_name}' already exists "
                                    f"on the GNS3 server. Please choose a different name.",
                                    "#F87171"
                                )
                                self.arch_status_dot.setStyleSheet(
                                    "color: #F87171; font-size: 18px; background: transparent;"
                                )
                                return
                            break
                    except Exception:
                        continue
            except Exception:
                pass  # If server unreachable, skip the check and proceed

        vsdx_path = os.path.join(
            os.path.expanduser("~"), "INDA", "VisioGns3", "vsdx_path.txt"
        )
        os.makedirs(os.path.dirname(vsdx_path), exist_ok=True)
        with open(vsdx_path, "w") as f:
            f.write(arch_proj_name)
        self._arch_log(f"📁  Project name saved: {arch_proj_name}", "#60A5FA")
        
        # ── Validation ───────────────────────────────────────────────────
        errors = []

        floors_text = self.floors_spin.line_edit.text().strip()
        if not floors_text:
            errors.append("Number of Floors cannot be empty.")
        else:
            try:
                floors = int(floors_text)
                if floors <= 0:      errors.append("Floors must be > 0.")
                elif floors > 5:     errors.append("Floors cannot exceed 5.")
            except ValueError:       errors.append("Floors must be a whole number.")

        rooms_text = self.rooms_spin.line_edit.text().strip()
        if not rooms_text:
            errors.append("Rooms Per Floor cannot be empty.")
        else:
            try:
                rooms = int(rooms_text)
                if rooms <= 0:       errors.append("Rooms must be > 0.")
                elif rooms > 10:     errors.append("Rooms cannot exceed 10.")
            except ValueError:       errors.append("Rooms must be a whole number.")

        users_text = self.users_spin.line_edit.text().strip()
        if not users_text:
            errors.append("Users Per Room cannot be empty.")
        else:
            try:
                users = int(users_text)
                if users <= 0:       errors.append("Users must be > 0.")
                elif users > 20:     errors.append("Users cannot exceed 20.")
            except ValueError:       errors.append("Users must be a whole number.")

        width_text = self.width_input.text().strip()
        if not width_text:
            errors.append("Building Width cannot be empty.")
        else:
            try:
                width = float(width_text)
                if width <= 0:       errors.append("Width must be > 0.")
            except ValueError:       errors.append("Width must be a number.")

        if errors:
            self.arch_status_dot.setStyleSheet(
                "color: #F87171; font-size: 18px; background: transparent;"
            )
            self._arch_log("\n❌  Validation failed:", "#F87171")
            for e in errors:
                self._arch_log(f"   • {e}", "#F87171")
            return

        # ── Read form values ─────────────────────────────────────────────
        unit          = self.width_unit_combo.currentText()
        building_type = self.building_type_combo._combo.currentText()
        firewall_enabled   = self.firewall_toggle.isChecked()
        cost_priority      = self.cost_combo._combo.currentText()
        speed_priority     = self.speed_combo._combo.currentText()
        reliability_priority = self.reliability_combo._combo.currentText()

        self._arch_log(f"\n📋  Configuration Summary")
        self._arch_log(f"   Floors: {floors}  |  Rooms/Floor: {rooms}  |  Users/Room: {users}")
        self._arch_log(f"   Width : {width} {unit}  |  Type: {building_type}")
        self._arch_log(f"   Cost: {cost_priority}  |  Speed: {speed_priority}  |  Reliability: {reliability_priority}")
        self._arch_log(f"   Firewall: {'Enabled ✅' if firewall_enabled else 'Disabled'}")

        # ── Collect selected servers ──────────────────────────────────────
        selected_servers = []
        for cb in self.server_checkboxes:
            try:
                if cb.isChecked():
                    key = cb.property('server_key')
                    if key:
                        selected_servers.append(key)
            except Exception:
                continue

        if selected_servers:
            self._arch_log(f"   Servers: {', '.join(selected_servers)}")
        else:
            self._arch_log("   Servers: None (DHCP + DNS only)")

        # ── Step 1: Generate machine names ───────────────────────────────
        self._arch_log("\n🔧  [1/4]  Generating device list...", "#60A5FA")
        try:
            from VisioGns3.Architecture.generate_machine_names_architecture import ArchitectureEngine
 
            gui_dir  = os.path.dirname(os.path.abspath(__file__))
            visio_dir = os.path.join(gui_dir, "VisioGns3")
            out_dir   = os.path.join(visio_dir, "Generated_files")
            os.makedirs(out_dir, exist_ok=True)
            out_path  = os.path.join(out_dir, "machine_names.txt")
 
            engine = ArchitectureEngine(floors, rooms, users, width, unit,
                                        building_type, firewall_enabled)
            engine.servers = selected_servers
            if selected_servers:
                engine.add_servers()
 
            machines = engine.run(out_path)
            self._arch_log(f"   ✅  {len(machines)} devices written → {out_path}", "#4ADE80")
 
            # ── AP placement plan ────────────────────────────────────────────
            self._ap_placement_path = os.path.join(out_dir, "ap_placement_plan.txt")
            engine.generate_ap_placement_file(self._ap_placement_path)
            cols, rows, aps_needed, radius = engine._compute_ap_grid()
            self._arch_log(
                f"   ✅  AP placement plan: {aps_needed} AP(s)/floor "
                f"in a {cols}×{rows} grid → {self._ap_placement_path}",
                "#4ADE80"
            )
            self.ap_download_btn.setVisible(True)
 
        except Exception as e:
            self._arch_log(f"   ❌  Device generation failed: {e}", "#F87171")
            self.arch_status_dot.setStyleSheet(
                "color: #F87171; font-size: 18px; background: transparent;"
            )
            return

        # ── Step 2: Generate connections + topology selection ────────────────
        self._arch_log("\\n🔧  [2/4]  Scoring topologies...", "#60A5FA")
        try:
            from VisioGns3.Architecture.generate_connections_architecture import ArchitectureConnections
 
            conn_engine = ArchitectureConnections(
                floors, rooms, users, engine.width_m,
                building_type, firewall_enabled, selected_servers,
                cost_priority, speed_priority, reliability_priority
            )
            pre_conn_path = os.path.join(visio_dir, "Generated_files", "pre_Connections.json")
 
            # Log the two candidates
            for entry in conn_engine.top2:
                pc   = entry["pros_cons"]
                icon = pc.get("icon", "◈")
                dname = pc.get("display_name", entry["name"].title())
                self._arch_log(
                    f"   #{entry['rank']}  {icon}  {dname}  "
                    f"(score {entry['score']})",
                    "#60A5FA"
                )
 
            # ── Topology selection dialog ────────────────────────────────
            dlg = TopologySelectionDialog(
                conn_engine.top2,
                conn_engine=conn_engine,          # ← NEW: needed to generate previews
                machine_list=engine.machines,     # ← NEW: the list from Step 1
                parent=self,
            )
            if dlg.exec() != QDialog.DialogCode.Accepted:
                self._arch_log(
                    "\\n⚠️  Topology selection cancelled by user.", "#FBBF24"
                )
                self.arch_status_dot.setStyleSheet(
                    "color: #FBBF24; font-size: 18px; background: transparent;"
                )
                return
 
            chosen      = dlg.chosen_topology
            connections = dlg.chosen_connections   # already generated, no re-work

            # Just write the file
            import json
            with open(pre_conn_path, "w") as f:
                json.dump(connections, f, indent=4)
                _log_topology_history(connections, os.path.join(visio_dir, "Generated_files"))

            self._arch_log(f"   ✅  {len(connections)} connections written → {pre_conn_path}", "#4ADE80")
 
        except Exception as e:
            self._arch_log(f"   ❌  Connection generation failed: {e}", "#F87171")
            self.arch_status_dot.setStyleSheet(
                "color: #F87171; font-size: 18px; background: transparent;"
            )
            return


        # ── Step 3: Run automation shell script ──────────────────────────
        self._arch_log("\n🔧  [3/4]  Running automation script...", "#60A5FA")

        script_path = os.path.join(gui_dir, "VisioGns3", "automation_architecture.sh")

        if not os.path.exists(script_path):
            self._arch_log(f"   ❌  Script not found: {script_path}", "#F87171")
            self.arch_status_dot.setStyleSheet(
                "color: #F87171; font-size: 18px; background: transparent;"
            )
            return

        # Clean up any previous thread
        if hasattr(self, '_arch_worker') and self._arch_worker is not None:
            try:
                self._arch_worker.output_signal.disconnect()
                self._arch_worker.finished_signal.disconnect()
            except Exception:
                pass

        self._arch_worker = AutomationRunnerThread(script_path, gui_dir)
        self._arch_worker.output_signal.connect(
            lambda line: self._arch_log(f"   {line}")
        )
        self._arch_worker.finished_signal.connect(self._on_arch_script_finished)
        self._arch_worker.start()

        self._arch_log("   Script launched — streaming output below ↓", "#60A5FA")


    def _on_arch_script_finished(self, exit_code: int):
        self._arch_log("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        if exit_code == 0:
            self._arch_log("  ✅  All steps completed successfully!", "#4ADE80")
            self.arch_status_dot.setStyleSheet(
                "color: #4ADE80; font-size: 18px; background: transparent;"
            )
        else:
            self._arch_log(
                f"  ⚠️  Script exited with code {exit_code}. Deployment may have been cancelled.",
                "#FBBF24"
            )
            self.arch_status_dot.setStyleSheet(
                "color: #FBBF24; font-size: 18px; background: transparent;"
            )
        self._arch_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    def _on_arch_script_error(self, message: str):
        self._arch_log(f"\n❌  Fatal error: {message}", "#F87171")
        self.arch_status_dot.setStyleSheet(
            "color: #F87171; font-size: 18px; background: transparent;"
        )

    def _download_ap_placement(self):
        """Open a Save-As dialog so the user can store ap_placement_plan.txt."""
        src = getattr(self, "_ap_placement_path", None)
        if not src or not os.path.exists(src):
            QMessageBox.warning(self, "File Not Found",
                                "AP placement file has not been generated yet.")
            return
 
        dest, _ = QFileDialog.getSaveFileName(
            self,
            "Save AP Placement Plan",
            os.path.join(os.path.expanduser("~"), "ap_placement_plan.txt"),
            "Text Files (*.txt);;All Files (*)"
        )
        if not dest:
            return          # user cancelled
 
        try:
            import shutil
            shutil.copy2(src, dest)
            QMessageBox.information(
                self,
                "Saved",
                f"AP placement plan saved to:\n{dest}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Save Failed", str(e))

    def _validate_chatbot_project_name(self):
        proj_name = self.chatbot_project_name_input.text().strip()
        self.chatbot_project_name_input.textChanged.connect(
            lambda: self._set_chatbot_proj_status("reset")
        )
        # Empty check
        if not proj_name:
            QMessageBox.warning(self, "Project Name Required",
                                "Please enter a project name before confirming.")
            return

        # Server duplicate check
        if self.server_ip and self.server_port:
            try:
                import urllib.request, json as _json
                existing_names = []
                for path in ["/v2/projects", "/api/v2/projects"]:
                    try:
                        url = f"http://{self.server_ip}:{self.server_port}{path}"
                        with urllib.request.urlopen(
                            urllib.request.Request(url, headers={"Accept": "application/json"}),
                            timeout=3
                        ) as resp:
                            projects = _json.loads(resp.read().decode())
                        if isinstance(projects, list):
                            existing_names = [p.get("name", "") for p in projects]
                            break
                    except Exception:
                        continue

                if proj_name in existing_names:
                    QMessageBox.warning(
                        self,
                        "Project Name Already Exists",
                        f"A project named '{proj_name}' already exists on the GNS3 server.\n\n"
                        f"Please choose a different name."
                    )
                    self.chatbot_project_name_input.setFocus()
                    self.chatbot_project_name_input.selectAll()
                    self._set_chatbot_proj_status("taken")
                    return

            except Exception:
                pass  # Server unreachable — skip check

        # All good
        self._set_chatbot_proj_status("ok")

        # Save to file
        vsdx_path = os.path.join(
            os.path.expanduser("~"), "INDA", "VisioGns3", "vsdx_path.txt"
        )
        os.makedirs(os.path.dirname(vsdx_path), exist_ok=True)
        with open(vsdx_path, "w") as f:
            f.write(proj_name)

    def _set_chatbot_proj_status(self, state: str):
        """Updates the small status label next to the chatbot project name field."""
        if state == "ok":
            self.chatbot_proj_status.setText("✔  Name confirmed")
            self.chatbot_proj_status.setStyleSheet(
                "color: #4ADE80; font-size: 12px; font-weight: 700;"
                "background: transparent; border: none;"
            )
            self.chatbot_proj_ok_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(74, 222, 128, 0.15);
                    color: #4ADE80;
                    border: 1px solid rgba(74, 222, 128, 0.45);
                    border-radius: 10px;
                    font-size: 13px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background: rgba(74, 222, 128, 0.28);
                }
            """)
        elif state == "taken":
            self.chatbot_proj_status.setText("✘  Name already taken")
            self.chatbot_proj_status.setStyleSheet(
                "color: #F87171; font-size: 12px; font-weight: 700;"
                "background: transparent; border: none;"
            )
            self.chatbot_proj_ok_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(248, 113, 113, 0.12);
                    color: #F87171;
                    border: 1px solid rgba(248, 113, 113, 0.35);
                    border-radius: 10px;
                    font-size: 13px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background: rgba(248, 113, 113, 0.25);
                }
            """)
        else:
            self.chatbot_proj_status.setText("")
            self.chatbot_proj_status.setStyleSheet("background: transparent; border: none;")


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

         # ── Project Name ──────────────────────────────────────────────
        proj_name_layout = QHBoxLayout()
        proj_name_label = QLabel("📁  Project Name")
        proj_name_label.setStyleSheet(
            "color: #CBD5E1; font-size: 14px; font-weight: 600; background: transparent;"
        )
        proj_name_label.setFixedWidth(140)

        self.chatbot_project_name_input = QLineEdit()
        self.chatbot_project_name_input.setPlaceholderText("Enter project name (e.g. MyNetwork)")
        self.chatbot_project_name_input.setMinimumHeight(44)
        self.chatbot_project_name_input.setStyleSheet("""
            QLineEdit {
                background: rgba(15, 23, 42, 0.6);
                color: #F8FAFC;
                border: 1px solid rgba(100, 116, 139, 0.3);
                border-radius: 10px;
                padding: 0 16px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #60A5FA;
            }
        """)
        self.chatbot_proj_ok_btn = QPushButton("OK")
        self.chatbot_proj_ok_btn.setFixedHeight(44)
        self.chatbot_proj_ok_btn.setFixedWidth(70)
        self.chatbot_proj_ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chatbot_proj_ok_btn.setStyleSheet("""
            QPushButton {
                background: rgba(96, 165, 250, 0.12);
                color: #60A5FA;
                border: 1px solid rgba(96, 165, 250, 0.35);
                border-radius: 10px;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: rgba(96, 165, 250, 0.25);
                border: 1px solid #60A5FA;
            }
            QPushButton:pressed {
                background: rgba(96, 165, 250, 0.40);
            }
            QPushButton:disabled {
                background: rgba(100, 116, 139, 0.08);
                color: #475569;
                border: 1px solid rgba(100, 116, 139, 0.2);
            }
        """)
        self.chatbot_proj_ok_btn.clicked.connect(self._validate_chatbot_project_name)

        self.chatbot_proj_status = QLabel("")
        self.chatbot_proj_status.setStyleSheet("background: transparent; border: none;")

        proj_name_layout.addWidget(proj_name_label)
        proj_name_layout.addWidget(self.chatbot_project_name_input)
        proj_name_layout.addWidget(self.chatbot_proj_ok_btn)
        c_layout.addLayout(proj_name_layout)
        c_layout.addWidget(self.chatbot_proj_status)
        # ─────────────────────────────────────────────────────────────

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
        # Save project name to vsdx_path.txt
        proj_name = self.chatbot_project_name_input.text().strip()
        if not proj_name:
            self.add_chat_message("bot", "⚠️ Please enter a Project Name before sending.")
            return

        # Ensure the OK button was clicked and confirmed green
        confirmed_text = self.chatbot_proj_status.text()
        if "confirmed" not in confirmed_text:
            self.add_chat_message(
                "bot",
                "⚠️ Please click <b>OK</b> next to the project name to confirm it is unique before sending."
            )
            return
        
        vsdx_path = os.path.join(
            os.path.expanduser("~"), "INDA", "VisioGns3", "vsdx_path.txt"
        )
        os.makedirs(os.path.dirname(vsdx_path), exist_ok=True)
        with open(vsdx_path, "w") as f:
            f.write(proj_name)

        # Reset for a fresh run each time
        self.automation_completed = False
        self.assistant_active = False
        self.run_btn.setEnabled(False)

        self.add_chat_message("user", msg)
        self.add_chat_message("bot", "🔮 Processing your request...")
        self.chat_input.clear()
        self.chat_input.setEnabled(False)

        script_path = os.path.expanduser("~/INDA/VisioGns3/NLP1/run_pipeline.py")

        # Safely disconnect and discard any previous thread
        if hasattr(self, 'script_runner') and self.script_runner is not None:
            try:
                self.script_runner.output_signal.disconnect()
                self.script_runner.finished_signal.disconnect()
            except Exception:
                pass
            self.script_runner = None

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
        self.chat_input.setFocus()

        if self.automation_completed:
            self.run_btn.setEnabled(True)
            self.add_chat_message("bot", "✅ Ready to run the automation! Click the 🚀 Run button to execute.")
        else:
            # Pipeline finished but didn't signal success — still let user try again
            self.add_chat_message("bot", "⚠️ Processing finished. You can enter a new request.")        

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
            self.add_chat_message("bot", f"Script not found:\n{script_path}")
            self.run_btn.setEnabled(True)
            return

        if not os.access(script_path, os.X_OK):
            self.add_chat_message("bot", "Script is not executable (chmod +x needed)")
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
        self.run_btn.setEnabled(False)   # hide until next successful pipeline run
        self.automation_completed = False
        self.assistant_active = False

        if return_code == 0:
            self.add_chat_message("bot", "✅ Automation completed successfully! You can enter a new request.")
            # Log topology to history and refresh dashboard graph
            try:
                gui_dir = os.path.dirname(os.path.abspath(__file__))
                visio_dir = os.path.join(gui_dir, "VisioGns3")
                gen_files = os.path.join(visio_dir, "Generated_files")
                pre_conn_path = os.path.join(gen_files, "pre_Connections.json")
                
                if os.path.exists(pre_conn_path):
                    import json
                    with open(pre_conn_path) as f:
                        connections = json.load(f)
                    _log_topology_history(connections, gen_files)
                    # Refresh the dashboard to show updated graph
                    QTimer.singleShot(500, self._refresh_dashboard_stats)
            except Exception as e:
                pass  # Silently skip if history logging fails
        else:
            self.add_chat_message("bot", f"⚠️ Automation exited with code {return_code}. You can enter a new request.")

        self.chat_input.setEnabled(True)
        self.chat_input.setFocus()

    def add_chat_message(self, role, content):
        current = self.chat_display.toHtml()

        if role == "user":
            # Reset assistant block when user speaks
            self.assistant_active = False

            msg = f"""
            <div style='margin: 15px 0;'>
                <span style='color: #68D391; font-weight: 700;'>👤 You:</span><br/>
                <span style='color: #E2E8F0;'>{content}</span>
            </div>
            """

        else:  # Assistant
            if not self.assistant_active:
                # First assistant message → create header once
                msg = f"""
                <div style='margin: 15px 0;'>
                    <span style='color: #4299E1; font-weight: 700;'>🤖 Assistant:</span><br/>
                    <span style='color: #E2E8F0;'>{content}</span>
                """
                self.assistant_active = True
            else:
                # Subsequent assistant messages → append only content
                msg = f"""
                    <br/>
                    <span style='color: #E2E8F0;'>{content}</span>
                """

        self.chat_display.setHtml(current + msg)
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )

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
        # Refresh stats every time dashboard is shown (non-blocking, fast)
        QTimer.singleShot(50, self._refresh_dashboard_stats)

    def show_console_page(self):
        self.stacked_widget.setCurrentIndex(2)

    def show_chatbot_page(self):
        self.stacked_widget.setCurrentIndex(3)
        self.chat_input.setFocus()

    def show_architecture_page(self):
        self.stacked_widget.setCurrentIndex(4)

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

    def _read_topology_history(self):
        import json
        gui_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(gui_dir, "VisioGns3", "Generated_files", "topology_history.json")
        try:
            with open(path) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def update_output(self, text):
        self.output_text.append(text)
        self.output_text.ensureCursorVisible()

    def on_topology_automation_finished(self):
        self.output_text.append("\n✅ Completed!")
        # Log topology to history and refresh dashboard graph
        try:
            gui_dir = os.path.dirname(os.path.abspath(__file__))
            visio_dir = os.path.join(gui_dir, "VisioGns3")
            gen_files = os.path.join(visio_dir, "Generated_files")
            pre_conn_path = os.path.join(gen_files, "pre_Connections.json")
            
            if os.path.exists(pre_conn_path):
                import json
                with open(pre_conn_path) as f:
                    connections = json.load(f)
                _log_topology_history(connections, gen_files)
                # Refresh the dashboard to show updated graph
                QTimer.singleShot(500, self._refresh_dashboard_stats)
        except Exception as e:
            pass  # Silently skip if history logging fails
        
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