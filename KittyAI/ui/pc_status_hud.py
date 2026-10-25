import os
import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QFrame, QGraphicsOpacityEffect, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QMouseEvent, QPainter, QBrush, QPen

from core.system_monitor import SystemMonitor

class PcStatusHud(QWidget):
    """
    A futuristic, animated, glassmorphic HUD window showing real-time PC status:
    CPU, RAM, GPU, Disks, Battery, and Uptime.
    """
    hud_closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.drag_position = QPoint()

        # Frameless, transparent, always-on-top tool window
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedWidth(360)
        self.setFixedHeight(480)

        # Main Layout
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(10, 10, 10, 10)

        # Container Frame with dark glassmorphism
        self.container = QFrame()
        self.container.setStyleSheet("""
            QFrame#hudContainer {
                background-color: rgba(20, 20, 35, 235);
                border: 2px solid #e74c3c;
                border-radius: 16px;
            }
            QLabel {
                color: #f0f0f5;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QProgressBar {
                background-color: rgba(255, 255, 255, 25);
                border: 1px solid rgba(255, 255, 255, 40);
                border-radius: 5px;
                text-align: center;
                font-size: 11px;
                font-weight: bold;
                color: #ffffff;
                height: 14px;
            }
            QProgressBar::chunk {
                border-radius: 4px;
            }
        """)
        self.container.setObjectName("hudContainer")

        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(16, 14, 16, 14)
        container_layout.setSpacing(10)

        # Header bar
        header_layout = QHBoxLayout()
        title_label = QLabel("🐾 Kitty AI — PC Status")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ff7675;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 20);
                color: #ffffff;
                font-size: 16px;
                font-weight: bold;
                border-radius: 12px;
                border: none;
            }
            QPushButton:hover {
                background-color: #e74c3c;
            }
        """)
        self.close_btn.clicked.connect(self.hide_hud)
        header_layout.addWidget(self.close_btn)
        container_layout.addLayout(header_layout)

        # Divider line
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("background-color: rgba(231, 76, 60, 80); max-height: 1px;")
        container_layout.addWidget(div)

        # Scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; } QScrollBar { width: 0px; }")
        
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 4, 0, 4)
        self.content_layout.setSpacing(12)

        # 1. CPU Section
        self.cpu_title = QLabel("⚡ Processor (CPU)")
        self.cpu_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #74b9ff;")
        self.cpu_sub = QLabel("Loading CPU details...")
        self.cpu_sub.setStyleSheet("font-size: 10px; color: #b2bec3;")
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setRange(0, 100)
        self.content_layout.addWidget(self.cpu_title)
        self.content_layout.addWidget(self.cpu_sub)
        self.content_layout.addWidget(self.cpu_bar)

        # 2. RAM Section
        self.ram_title = QLabel("🧠 Memory (RAM)")
        self.ram_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #a29bfe;")
        self.ram_sub = QLabel("Loading RAM...")
        self.ram_sub.setStyleSheet("font-size: 10px; color: #b2bec3;")
        self.ram_bar = QProgressBar()
        self.ram_bar.setRange(0, 100)
        self.content_layout.addWidget(self.ram_title)
        self.content_layout.addWidget(self.ram_sub)
        self.content_layout.addWidget(self.ram_bar)

        # 3. GPU Section
        self.gpu_title = QLabel("🎮 Graphics (GPU)")
        self.gpu_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #55efc4;")
        self.gpu_name = QLabel("Detecting GPU...")
        self.gpu_name.setStyleSheet("font-size: 11px; font-weight: bold; color: #ffffff;")
        self.gpu_details = QLabel("")
        self.gpu_details.setStyleSheet("font-size: 10px; color: #b2bec3;")
        self.content_layout.addWidget(self.gpu_title)
        self.content_layout.addWidget(self.gpu_name)
        self.content_layout.addWidget(self.gpu_details)

        # 4. Storage (Disks) Section
        self.disk_title = QLabel("💽 Storage (Drives)")
        self.disk_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #ffeaa7;")
        self.content_layout.addWidget(self.disk_title)
        self.disk_container = QVBoxLayout()
        self.disk_container.setSpacing(6)
        self.content_layout.addLayout(self.disk_container)

        # 5. Battery & Power
        self.battery_title = QLabel("🔋 Battery & Power")
        self.battery_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #fab1a0;")
        self.battery_status = QLabel("Checking battery...")
        self.battery_status.setStyleSheet("font-size: 11px; color: #dfe6e9;")
        self.battery_bar = QProgressBar()
        self.battery_bar.setRange(0, 100)
        self.content_layout.addWidget(self.battery_title)
        self.content_layout.addWidget(self.battery_status)
        self.content_layout.addWidget(self.battery_bar)

        # 6. System Uptime & Processes
        self.sys_info = QLabel("⏱️ Uptime: ... | 📂 Processes: ...")
        self.sys_info.setStyleSheet("font-size: 11px; color: #81ecec; padding-top: 4px;")
        self.content_layout.addWidget(self.sys_info)

        content_widget.setLayout(self.content_layout)
        scroll.setWidget(content_widget)
        container_layout.addWidget(scroll)

        self.container.setLayout(container_layout)
        outer_layout.addWidget(self.container)
        self.setLayout(outer_layout)

        # Auto-refresh timer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_metrics)

    def show_hud(self, pos: QPoint = None) -> None:
        """Position and display the HUD with refreshed metrics."""
        self.refresh_metrics()
        if pos:
            # Place near requested point
            self.move(pos)
        self.show()
        self.raise_()
        self.activateWindow()
        self.refresh_timer.start(1500)

    def hide_hud(self) -> None:
        """Hide HUD and pause auto refresh timer."""
        self.refresh_timer.stop()
        self.hide()
        self.hud_closed.emit()

    def toggle_hud(self, anchor_x: int = 100, anchor_y: int = 100) -> None:
        """Toggle HUD visibility."""
        if self.isVisible():
            self.hide_hud()
        else:
            # Position HUD adjacent to the pet
            px = max(20, anchor_x - 380)
            py = max(20, min(anchor_y - 100, 500))
            self.show_hud(QPoint(px, py))

    def _get_bar_color(self, percent: float) -> str:
        """Return harmonious color based on load level."""
        if percent >= 85:
            return "#e74c3c"  # Red
        elif percent >= 70:
            return "#f39c12"  # Amber
        elif percent >= 45:
            return "#3498db"  # Blue
        return "#2ecc71"      # Green

    def refresh_metrics(self) -> None:
        """Collect latest system stats and refresh UI components."""
        data = SystemMonitor.get_system_snapshot()

        # 1. CPU
        cpu_val = int(data["cpu"])
        self.cpu_bar.setValue(cpu_val)
        self.cpu_bar.setStyleSheet(f"""
            QProgressBar::chunk {{ background-color: {self._get_bar_color(cpu_val)}; border-radius: 4px; }}
        """)
        self.cpu_sub.setText(f"Load: {data['cpu']:.1f}% | Clock: {data['cpu_ghz']} | Cores: {data['cpu_cores_phys']}P / {data['cpu_cores_log']}L")

        # 2. RAM
        ram_val = int(data["memory_percent"])
        self.ram_bar.setValue(ram_val)
        self.ram_bar.setStyleSheet(f"""
            QProgressBar::chunk {{ background-color: {self._get_bar_color(ram_val)}; border-radius: 4px; }}
        """)
        self.ram_sub.setText(f"Used: {data['memory_used_gb']} GB / {data['memory_total_gb']} GB ({ram_val}%) | Free: {data['memory_avail_gb']} GB")

        # 3. GPU
        gpu = data["gpu"]
        self.gpu_name.setText(f"🎮 {gpu.get('name', 'Graphics Adapter')}")
        details_str = []
        if gpu.get("driver"): details_str.append(f"Driver: {gpu['driver']}")
        if gpu.get("util") and gpu["util"] != "N/A": details_str.append(f"Util: {gpu['util']}")
        if gpu.get("mem_used") and gpu.get("mem_total"): details_str.append(f"VRAM: {gpu['mem_used']} / {gpu['mem_total']}")
        if gpu.get("temp"): details_str.append(f"Temp: {gpu['temp']}")
        self.gpu_details.setText(" | ".join(details_str) if details_str else "Status: Active & Operating")

        # 4. Disks
        # Clear previous disk widgets
        while self.disk_container.count():
            item = self.disk_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for d in data.get("disks", []):
            d_box = QVBoxLayout()
            d_box.setSpacing(2)
            d_lbl = QLabel(f"Drive {d['mount']} — {d['used_gb']} GB used / {d['total_gb']} GB total ({d['percent']}%)")
            d_lbl.setStyleSheet("font-size: 10px; color: #dfe6e9;")
            d_bar = QProgressBar()
            d_bar.setRange(0, 100)
            d_bar.setValue(int(d["percent"]))
            d_bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {self._get_bar_color(d['percent'])}; border-radius: 4px; }}")
            d_box.addWidget(d_lbl)
            d_box.addWidget(d_bar)
            w = QWidget()
            w.setLayout(d_box)
            self.disk_container.addWidget(w)

        # 5. Battery
        batt = data.get("battery", {})
        if batt.get("percent") is not None:
            b_pct = batt["percent"]
            self.battery_bar.show()
            self.battery_bar.setValue(b_pct)
            b_color = "#2ecc71" if b_pct > 30 else "#e74c3c"
            self.battery_bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {b_color}; border-radius: 4px; }}")
            self.battery_status.setText(f"{batt.get('status', 'Battery')} ({b_pct}%)")
        else:
            self.battery_bar.hide()
            self.battery_status.setText("Desktop AC Power (No Battery Detected)")

        # 6. System Uptime & Processes
        self.sys_info.setText(f"⏱️ Uptime: {data.get('uptime', 'N/A')}  |  📂 Active Processes: {data.get('process_count', 0)}")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Allow dragging the HUD across the screen."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
