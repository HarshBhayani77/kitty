import os
import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QTimer
from PyQt6.QtGui import QMouseEvent, QFont, QColor

from core.ai_manager import AIManager
from core.sound_manager import SoundManager
from database.database import DatabaseManager

class ChatBubble(QFrame):
    """A styled message bubble inside the chat history."""
    def __init__(self, text: str, is_user: bool, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 8, 10, 8)

        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        if is_user:
            self.setStyleSheet("""
                QFrame {
                    background-color: #6c5ce7;
                    border-radius: 12px;
                    border-bottom-right-radius: 2px;
                    margin-left: 50px;
                }
                QLabel {
                    color: #ffffff;
                    font-size: 12px;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: rgba(45, 52, 70, 220);
                    border: 1px solid rgba(231, 76, 60, 120);
                    border-radius: 12px;
                    border-bottom-left-radius: 2px;
                    margin-right: 50px;
                }
                QLabel {
                    color: #f5f6fa;
                    font-size: 12px;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
            """)
        layout.addWidget(lbl)
        self.setLayout(layout)


class ChatDialog(QWidget):
    """
    An interactive, beautiful glassmorphism chat interface for conversations with Kitty AI.
    Integrates directly with AIManager (both offline persona and Cloud/Local conversation APIs).
    """
    message_sent = pyqtSignal(str)

    def __init__(self, ai_manager: AIManager, db_manager: DatabaseManager, pet_window=None, parent=None):
        super().__init__(parent)
        self.ai = ai_manager
        self.db = db_manager
        self.pet_win = pet_window
        self.drag_position = QPoint()

        # Window properties
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedWidth(380)
        self.setFixedHeight(500)

        # Main Layout
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(8, 8, 8, 8)

        self.container = QFrame()
        self.container.setStyleSheet("""
            QFrame#chatContainer {
                background-color: rgba(22, 22, 38, 240);
                border: 2px solid #e74c3c;
                border-radius: 16px;
            }
            QLabel {
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLineEdit {
                background-color: rgba(10, 10, 20, 200);
                border: 1px solid #e74c3c;
                border-radius: 8px;
                padding: 8px 12px;
                color: #ffffff;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #ff7675;
            }
            QPushButton#sendBtn {
                background-color: #e74c3c;
                color: #ffffff;
                font-weight: bold;
                border-radius: 8px;
                padding: 8px 14px;
                border: none;
            }
            QPushButton#sendBtn:hover {
                background-color: #d63031;
            }
            QPushButton.chipBtn {
                background-color: rgba(255, 255, 255, 20);
                color: #dfe6e9;
                font-size: 10px;
                border-radius: 10px;
                padding: 4px 8px;
                border: 1px solid rgba(255, 255, 255, 30);
            }
            QPushButton.chipBtn:hover {
                background-color: rgba(231, 76, 60, 60);
                color: #ffffff;
                border-color: #e74c3c;
            }
        """)
        self.container.setObjectName("chatContainer")

        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(14, 12, 14, 12)
        container_layout.setSpacing(8)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("💬 Meow Chat — Kitty AI")
        title.setStyleSheet("font-size: 13px; font-weight: bold; color: #ff7675;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(22, 22)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 20);
                color: #ffffff;
                font-size: 16px;
                font-weight: bold;
                border-radius: 11px;
                border: none;
            }
            QPushButton:hover {
                background-color: #e74c3c;
            }
        """)
        self.close_btn.clicked.connect(self.hide)
        header_layout.addWidget(self.close_btn)
        container_layout.addLayout(header_layout)

        # Chat History Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.history_widget = QWidget()
        self.history_widget.setStyleSheet("background: transparent;")
        self.history_layout = QVBoxLayout()
        self.history_layout.setContentsMargins(0, 4, 0, 4)
        self.history_layout.setSpacing(8)
        self.history_layout.addStretch()
        self.history_widget.setLayout(self.history_layout)

        self.scroll_area.setWidget(self.history_widget)
        container_layout.addWidget(self.scroll_area)

        # Quick chips
        chips_layout = QHBoxLayout()
        chips_layout.setSpacing(6)
        chips = [
            ("⚡ PC Health", "How is my PC running right now?"),
            ("😹 Cat Joke", "Tell me a hilarious cat joke!"),
            ("🎯 Focus Mode", "Help me stay focused and productive!"),
            ("🐾 Who are you?", "Who are you and what can you do?")
        ]
        for label_text, prompt_text in chips:
            chip = QPushButton(label_text)
            chip.setProperty("class", "chipBtn")
            chip.setStyleSheet("""
                background-color: rgba(255, 255, 255, 20);
                color: #dfe6e9;
                font-size: 10px;
                border-radius: 9px;
                padding: 3px 8px;
                border: 1px solid rgba(255, 255, 255, 30);
            """)
            chip.setCursor(Qt.CursorShape.PointingHandCursor)
            chip.clicked.connect(lambda checked, p=prompt_text: self.send_prompt(p))
            chips_layout.addWidget(chip)
        container_layout.addLayout(chips_layout)

        # Input Row
        input_layout = QHBoxLayout()
        input_layout.setSpacing(6)
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask Kitty anything... (Press Enter)")
        self.input_field.returnPressed.connect(self.on_send_clicked)
        input_layout.addWidget(self.input_field)

        self.send_btn = QPushButton("Send 🐾")
        self.send_btn.setObjectName("sendBtn")
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.clicked.connect(self.on_send_clicked)
        input_layout.addWidget(self.send_btn)

        container_layout.addLayout(input_layout)
        self.container.setLayout(container_layout)
        outer_layout.addWidget(self.container)
        self.setLayout(outer_layout)

        # Initial Welcome Message
        user_name = self.db.get_setting("user_name", "human")
        self.add_message(f"Meow, {user_name}! Ask me anything, or configure my AI API in Settings for supercharged chat! 😸", is_user=False)

    def add_message(self, text: str, is_user: bool) -> None:
        """Add a bubble to history and scroll to bottom."""
        bubble = ChatBubble(text, is_user=is_user)
        # Insert before stretch
        count = self.history_layout.count()
        self.history_layout.insertWidget(max(0, count - 1), bubble)
        # Scroll down
        QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))

    def send_prompt(self, prompt: str) -> None:
        """Helper to send a pre-configured prompt."""
        self.input_field.setText(prompt)
        self.on_send_clicked()

    def on_send_clicked(self) -> None:
        """Handle sending user message."""
        text = self.input_field.text().strip()
        if not text:
            return

        self.input_field.clear()
        self.add_message(text, is_user=True)

        user_name = self.db.get_setting("user_name", "human")
        vol = int(self.db.get_setting("volume", "80"))
        snd = self.db.get_setting("sound_enabled", "true") == "true"

        # Show pending message
        self.add_message("Thinking... purr... 🐾", is_user=False)
        pending_item = self.history_layout.itemAt(self.history_layout.count() - 2)

        def on_success(reply: str):
            # Replace thinking bubble with real reply
            if pending_item and pending_item.widget():
                pending_item.widget().deleteLater()
            self.add_message(reply, is_user=False)
            SoundManager.play_sound("meow", volume_percent=vol, enabled=snd)
            if self.pet_win:
                self.pet_win.show_message(reply, duration_ms=5000)

        def on_error(err: str):
            if pending_item and pending_item.widget():
                pending_item.widget().deleteLater()
            self.add_message(f"😿 Error: {err}", is_user=False)

        self.ai.update_config(self.db.get_setting("personality_style", "default"))
        self.ai.send_message(text, on_success, on_error, user_name=user_name, db_manager=self.db)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
