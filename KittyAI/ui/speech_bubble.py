import time
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QTimer, QPoint, QRectF
from PyQt6.QtGui import QPainter, QColor, QPainterPath, QBrush, QPen, QFont

class SpeechBubbleWidget(QWidget):
    """
    A compact, beautiful, floating speech bubble with a downward pointer tail,
    supporting structured color-box status cards and formatted text dialogs.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        # Frameless, on-top, tool overlay
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        self.tail_height = 7
        self.corner_radius = 10

        # Compact layout margins
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(8, 6, 8, 6 + self.tail_height)
        self.setLayout(self.layout)

        # Label for content (supports rich HTML)
        self.label = QLabel()
        self.label.setTextFormat(Qt.TextFormat.RichText)
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("background: transparent; color: #ffffff;")
        self.layout.addWidget(self.label)

        # Drop shadow for floating effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 140))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

        # Auto-hide timer
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide_bubble)

    def show_status_snapshot(self, data: dict, duration_ms: int = 6000) -> None:
        """Display system metrics in a petite, structured multi-box card layout."""
        cpu = data.get("cpu", 0.0)
        cpu_ghz = data.get("cpu_ghz", "")
        mem_pct = data.get("memory_percent", 0.0)
        mem_used = data.get("memory_used_gb", 0.0)
        mem_tot = data.get("memory_total_gb", 0.0)
        gpu = data.get("gpu", {})
        gpu_name = gpu.get("name", "Integrated GPU")
        
        if len(gpu_name) > 18:
            gpu_name = gpu_name.replace("Intel(R)", "").replace("Graphics", "").strip()

        disk_pct = data.get("disk", 0.0)
        disks = data.get("disks", [])
        disk_free = f"{disks[0]['free_gb']} GB Free" if disks else "Normal"

        batt = data.get("battery", {})
        batt_html = ""
        if batt.get("percent") is not None:
            b_pct = batt["percent"]
            b_status = "AC ⚡" if batt.get("plugged") else "Batt 🔋"
            batt_html = f"""
            <div style="background-color: rgba(46, 204, 113, 0.18); border: 1px solid #2ecc71; border-radius: 6px; padding: 3px 6px; margin-top: 3px; text-align: left; font-size: 9px;">
              <span style="color: #2ecc71; font-weight: bold;">🔋</span>
              <span style="font-weight: bold; color: #ffffff; margin-left: 2px;">{b_pct}% — {b_status}</span>
            </div>
            """

        html = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; color: #ffffff; min-width: 210px;">
          <!-- Header -->
          <div style="font-size: 10px; font-weight: bold; color: #ff7675; margin-bottom: 4px; letter-spacing: 0.5px;">
            🐾 SYSTEM SNAPSHOT
          </div>

          <!-- Structured 2x2 Grid of Colored Boxes -->
          <table width="100%" cellpadding="0" cellspacing="3" style="border-collapse: separate; border-spacing: 3px;">
            <tr>
              <!-- CPU Box -->
              <td width="50%" style="background-color: rgba(9, 132, 227, 0.22); border: 1px solid #74b9ff; border-radius: 6px; padding: 4px 6px; text-align: left;">
                <div style="font-size: 8px; color: #74b9ff; font-weight: bold;">⚡ CPU</div>
                <div style="font-size: 11px; font-weight: bold; color: #ffffff;">{cpu:.1f}%</div>
                <div style="font-size: 8px; color: #b2bec3;">{cpu_ghz}</div>
              </td>
              <!-- RAM Box -->
              <td width="50%" style="background-color: rgba(108, 92, 231, 0.22); border: 1px solid #a29bfe; border-radius: 6px; padding: 4px 6px; text-align: left;">
                <div style="font-size: 8px; color: #a29bfe; font-weight: bold;">🧠 RAM</div>
                <div style="font-size: 11px; font-weight: bold; color: #ffffff;">{mem_pct:.1f}%</div>
                <div style="font-size: 8px; color: #b2bec3;">{mem_used:.1f}/{mem_tot:.1f} GB</div>
              </td>
            </tr>
            <tr>
              <!-- GPU Box -->
              <td width="50%" style="background-color: rgba(0, 184, 148, 0.22); border: 1px solid #55efc4; border-radius: 6px; padding: 4px 6px; text-align: left;">
                <div style="font-size: 8px; color: #55efc4; font-weight: bold;">🎮 GPU</div>
                <div style="font-size: 9px; font-weight: bold; color: #ffffff;">{gpu_name}</div>
              </td>
              <!-- Disk Box -->
              <td width="50%" style="background-color: rgba(225, 112, 85, 0.22); border: 1px solid #fab1a0; border-radius: 6px; padding: 4px 6px; text-align: left;">
                <div style="font-size: 8px; color: #fab1a0; font-weight: bold;">💽 DISK C:</div>
                <div style="font-size: 11px; font-weight: bold; color: #ffffff;">{disk_pct:.1f}%</div>
                <div style="font-size: 8px; color: #b2bec3;">{disk_free}</div>
              </td>
            </tr>
          </table>

          {batt_html}
        </div>
        """
        self.setFixedWidth(230)
        self.label.setText(html)
        self.adjustSize()
        self.show()
        self.hide_timer.start(duration_ms)

    def show_dialog_text(self, text: str, duration_ms: int = 4000) -> None:
        """Display regular pet dialogue message in a petite, compact speech bubble."""
        html = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; color: #ffffff; padding: 1px 2px; font-size: 10.5px; line-height: 1.25; font-weight: 500;">
          {text}
        </div>
        """
        target_w = min(210, max(110, len(text) * 5 + 24))
        self.setFixedWidth(target_w)
        self.label.setText(html)
        self.adjustSize()
        self.show()
        self.hide_timer.start(duration_ms)

    def hide_bubble(self) -> None:
        self.hide_timer.stop()
        self.hide()

    def mousePressEvent(self, a0) -> None:
        """Dismiss bubble when clicked."""
        self.hide_bubble()

    def paintEvent(self, event) -> None:
        """Draw the speech bubble rounded box with bottom pointer arrow pointing to Kitty."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        w = self.width()
        h = self.height() - self.tail_height

        path = QPainterPath()
        path.addRoundedRect(QRectF(1.5, 1.5, w - 3, h - 3), self.corner_radius, self.corner_radius)

        # Downward speech tail pointing to the cat's head
        tail_cx = w // 2
        tail_path = QPainterPath()
        tail_path.moveTo(tail_cx - 6, h - 1.5)
        tail_path.lineTo(tail_cx, h + self.tail_height - 1.5)
        tail_path.lineTo(tail_cx + 6, h - 1.5)
        tail_path.closeSubpath()

        full_bubble = path.united(tail_path)

        # Fill background (dark glassmorphism)
        painter.setBrush(QBrush(QColor(22, 22, 36, 245)))
        # Thin sleek border
        painter.setPen(QPen(QColor("#e74c3c"), 1.5))
        painter.drawPath(full_bubble)
